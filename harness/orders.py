"""Each order's money, from a saved week: what the run viewer shows, as rows we can group.

    python3 -m harness.orders <label>            groups the label's dev weeks by lane length, option, drivers near the pickup, ...
"""
from __future__ import annotations

import collections
import gzip
import json
import math
import os
import sys

from . import config
from .play import read_index


def orders_of(folder: str) -> list[dict]:
    """One row per order that was not cancelled: price, driver fees, refunds and other costs, and what kind of car it was."""
    snapshot = json.load(gzip.open(os.path.join(folder, "snapshot.json.gz"), "rt", encoding="utf-8"))
    roster = json.load(gzip.open(os.path.join(folder, "roster.json.gz"), "rt", encoding="utf-8"))
    reveal = json.load(gzip.open(os.path.join(folder, "reveal.json.gz"), "rt", encoding="utf-8"))
    places = {place["id"]: place for place in json.load(open(os.path.join(config.DATA, "map.json"), encoding="utf-8"))["places"]}
    roads = {(road["from"], road["to"]): road for road in json.load(open(os.path.join(config.DATA, "map.json"), encoding="utf-8"))["roads"]}
    requests = {item["request"]["id"]: item["request"] for item in reveal["requests"]}

    def straight(a: str, b: str) -> float:
        p, q = places[a], places[b]
        lat1, lat2, dlon = math.radians(p["lat"]), math.radians(q["lat"]), math.radians(q["lon"] - p["lon"])
        return 2 * 6371 * math.asin(math.sqrt(math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2))

    homes = collections.Counter(driver["homePlaceId"] for driver in roster)
    near = {town: sum(count for home, count in homes.items() if straight(town, home) <= 30) for town in places}
    gig_orders = {gig["id"]: sorted({stop["orderId"] for stop in gig["stops"]}) for gig in snapshot["gigs"]}
    money: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
    with gzip.open(os.path.join(folder, "events.jsonl.gz"), "rt", encoding="utf-8") as events:
        for text in events:
            event = json.loads(text)
            if event["kind"] != "ledger":
                continue
            line = event["line"]
            owners = [line["orderId"]] if line["orderId"] else gig_orders.get(line["gigId"] or "", [])
            for owner in owners:
                money[owner][line["kind"]] += line["cents"] / len(owners)
    rows = []
    for order in snapshot["orders"]:
        if order["status"] == "cancelled" or order["id"] not in requests:
            continue
        request, leg, lines = requests[order["id"]], order["legs"][0], money[order["id"]]
        option = next(o for o in request["options"] if o["kind"] == order["option"])
        rows.append({
            "id": order["id"], "price": order["priceCents"] / 100, "list": option["listPriceCents"] / 100, "typical": request["referenceFeeCents"] / 100,
            "fee": -lines["driver_fee"] / 100, "refund": -(lines["late_refund"] + lines["undelivered_penalty"]) / 100,
            "other": -(lines["failed_visit"] + lines["waiting"] + lines["fine"] + lines["release_fee"]) / 100,
            "margin": sum(lines.values()) / 100, "late": lines["late_refund"] + lines["undelivered_penalty"] < 0,
            "km": roads[(leg["pickup"]["placeId"], leg["delivery"]["placeId"])]["km"], "option": order["option"], "legs": len(order["legs"]),
            "private": any(l[side]["privateAddress"] for l in order["legs"] for side in ("pickup", "delivery")),
            "near_pickup": near[leg["pickup"]["placeId"]], "near_delivery": near[leg["delivery"]["placeId"]],
            "day": request["arrivedAt"] // 1440, "pickup": leg["pickup"]["placeId"], "delivery": leg["delivery"]["placeId"], "note": bool(request["note"]),
        })
    return rows


def show(title: str, rows: list[dict], key) -> None:
    groups: dict = collections.defaultdict(list)
    for row in rows:
        groups[key(row)].append(row)
    print(f"\n{title}\n{'':18} {'orders':>6} {'on time':>7} {'price':>6} {'/list':>5} {'fee':>6} {'/typ':>5} {'refund':>6} {'other':>5} {'margin':>6} {'total €':>8}")
    for name in sorted(groups):
        g = groups[name]
        n = len(g)
        mean = lambda field: sum(row[field] for row in g) / n
        print(f"{str(name):18} {n:>6} {1 - sum(row['late'] for row in g) / n:>7.1%} {mean('price'):>6.0f} {sum(r['price'] for r in g) / sum(r['list'] for r in g):>5.2f} {mean('fee'):>6.0f} "
              f"{sum(r['fee'] for r in g) / sum(r['typical'] for r in g):>5.2f} {mean('refund'):>6.1f} {mean('other'):>5.1f} {mean('margin'):>6.1f} {sum(r['margin'] for r in g):>8,.0f}")


def main() -> None:
    label = sys.argv[1]
    rows = []
    for row in read_index():
        if row["label"] == label and row["level"] == 8 and row["seed"] in config.SEEDS["dev"]:
            rows += orders_of(os.path.join(config.RUNS, os.path.basename(row["folder"])))
    print(f"{label}: {len(rows)} orders, margin €{sum(r['margin'] for r in rows):,.0f}")
    band = lambda value, edges: next((f"<{edge}" for edge in edges if value < edge), f">={edges[-1]}")
    show("by lane length, km", rows, lambda r: band(r["km"], [50, 150, 300, 500]).rjust(6))
    show("by option", rows, lambda r: r["option"])
    show("by drivers living within 30 km of the pickup", rows, lambda r: band(r["near_pickup"], [10, 30, 80]).rjust(5))
    show("by drivers living within 30 km of the delivery", rows, lambda r: band(r["near_delivery"], [10, 30, 80]).rjust(5))
    show("by day the request arrived", rows, lambda r: r["day"])
    show("private address", rows, lambda r: r["private"])
    show("on time or late", rows, lambda r: "late" if r["late"] else "on time")
    worst = sorted(rows, key=lambda r: r["margin"])[:12]
    print("\nworst orders: " + "; ".join(f"{r['pickup']}>{r['delivery']} {r['margin']:.0f}€ (price {r['price']:.0f}, fee {r['fee']:.0f}, refund {r['refund']:.0f})" for r in worst))


if __name__ == "__main__":
    main()
