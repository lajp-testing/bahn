"""Analyses the test final's reveal: which requests we lost, at what quote ratio.

    python3 tracks/t2/analyse_final.py [DIR=tracks/t2/final-1800]

Prints the tables of FINDINGS.md "Test final 18:00". Standard library only.
"""
from __future__ import annotations

import json
import os
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
DAY = 1440


def load(dirpath: str):
    with open(os.path.join(dirpath, "reveal.json"), encoding="utf-8") as fh:
        reveal = json.load(fh)
    with open(os.path.join(dirpath, "events.json"), encoding="utf-8") as fh:
        events = json.load(fh)
    with open(os.path.join(HERE, "map.json"), encoding="utf-8") as fh:
        world_map = json.load(fh)
    return reveal, events, world_map


def analyse(dirpath: str) -> None:
    reveal, events, world_map = load(dirpath)
    km = {(r["from"], r["to"]): r["km"] for r in world_map["roads"]}

    # Per-order margin: every ledger line carries the order's id.
    with open(os.path.join(dirpath, "snapshot.json"), encoding="utf-8") as fh:
        snapshot = json.load(fh)
    gig_orders = {g["id"]: {s["orderId"] for s in g["stops"]} for g in snapshot["gigs"]}
    margin = defaultdict(int)
    for e in events:
        if e["kind"] != "ledger":
            continue
        line = e["line"]
        if line["orderId"] is not None:
            margin[line["orderId"]] += line["cents"]
        else:  # a gig's fee, split over the orders the gig carried
            orders = gig_orders.get(line["gigId"], set())
            for order_id in orders:
                margin[order_id] += line["cents"] / len(orders)

    rows = []  # one per request
    options = []  # one per quoted option
    unquoted_options = 0
    for r in reveal["requests"]:
        req = r["request"]
        quote = r["quote"] or {}
        cheapest = min(req["options"], key=lambda o: o["listPriceCents"])
        road = sum(km[(leg["pickup"]["placeId"], leg["delivery"]["placeId"])] for leg in req["legs"])
        private = any(leg["pickup"]["privateAddress"] or leg["delivery"]["privateAddress"]
                      for leg in req["legs"])
        ratios = {kind: q / o["listPriceCents"] for kind, q in quote.items()
                  for o in req["options"] if o["kind"] == kind and q is not None}
        for o in req["options"]:
            if o["kind"] not in quote or quote[o["kind"]] is None:
                unquoted_options += 1
        won = r["outcome"] == "won"
        rows.append({
            "id": req["id"], "won": won, "option": r["option"],
            "cheapest_lp": cheapest["listPriceCents"], "road": road,
            "weekday": req["arrivedAt"] // DAY, "private": private,
            "cheapest_ratio": ratios.get(cheapest["kind"]),
            "min_ratio": min(ratios.values()) if ratios else None,
            "margin": margin.get(req["id"], 0) if won else None,
        })
        for kind, ratio in ratios.items():
            options.append({"kind": kind, "ratio": ratio,
                            "won_here": won and r["option"] == kind})

    n = len(rows)
    wins = sum(r["won"] for r in rows)
    print(f"{n} requests, {wins} won ({wins / n:.1%}), {n - wins} lost, "
          f"{unquoted_options} offered options left unquoted\n")

    def table(title: str, key, order=None, fmt=str):
        groups = defaultdict(list)
        for r in rows:
            groups[key(r)].append(r)
        keys = order(groups) if order else sorted(groups)
        print(f"{title}")
        print(f"{'band':<22}{'requests':>9}{'won':>6}{'win rate':>10}{'avg quote/list':>16}{'avg won margin':>16}")
        for k in keys:
            g = groups[k]
            w = sum(r["won"] for r in g)
            ratios = [r["cheapest_ratio"] for r in g if r["cheapest_ratio"] is not None]
            margins = [r["margin"] for r in g if r["won"]]
            print(f"{fmt(k):<22}{len(g):>9}{w:>6}{w / len(g):>10.1%}"
                  f"{(sum(ratios) / len(ratios)) if ratios else float('nan'):>16.3f}"
                  f"{(sum(margins) / len(margins) / 100) if margins else float('nan'):>16.2f}")
        print()

    # (a) quintiles of the cheapest option's list price
    lps = sorted(r["cheapest_lp"] for r in rows)
    cuts = [lps[n * i // 5 - 1] for i in range(1, 5)]
    def quintile(r):
        return sum(r["cheapest_lp"] > c for c in cuts)
    table("(a) cheapest option's list price, quintiles", quintile,
          order=lambda g: sorted(g),
          fmt=lambda i: f"Q{i+1} <= {cuts[i] / 100:.0f}€" if i < 4 else f"Q5 > {cuts[3] / 100:.0f}€")

    # (b) road distance
    def band(r):
        return "<100" if r["road"] < 100 else "100-300" if r["road"] < 300 else "300-500" if r["road"] < 500 else ">500"
    table("(b) road km, all legs", band, order=lambda g: ["<100", "100-300", "300-500", ">500"])

    # (d) weekday
    table("(d) weekday of the request", lambda r: WEEKDAYS[r["weekday"]],
          order=lambda g: [d for d in WEEKDAYS if d in g])

    # (e) private address
    table("(e) private address at either end", lambda r: "yes" if r["private"] else "no",
          order=lambda g: ["no", "yes"])

    # (c) option kind, per quoted option
    print("(c) per quoted option")
    print(f"{'kind':<22}{'quoted':>9}{'won on it':>10}{'win rate':>10}{'avg quote/list':>16}")
    for kind in ["same_day", "next_day", "within_3_days"]:
        g = [o for o in options if o["kind"] == kind]
        if not g:
            continue
        w = sum(o["won_here"] for o in g)
        print(f"{kind:<22}{len(g):>9}{w:>10}{w / len(g):>10.1%}{sum(o['ratio'] for o in g) / len(g):>16.3f}")
    print()

    # Win rate by how far our best quote sits above list price.
    print("win rate by our best (lowest) quote/list ratio")
    print(f"{'ratio':<22}{'requests':>9}{'won':>6}{'win rate':>10}")
    for lo, hi in [(0, 1.1), (1.1, 1.3), (1.3, 1.5), (1.5, 1.7), (1.7, 2.0), (2.0, 2.5), (2.5, 99)]:
        g = [r for r in rows if r["min_ratio"] is not None and lo <= r["min_ratio"] < hi]
        if not g:
            continue
        w = sum(r["won"] for r in g)
        print(f"{lo}-{hi if hi < 99 else 'inf':<22}{len(g):>9}{w:>6}{w / len(g):>10.1%}")
    print()

    # Offered options we left unquoted, by kind.
    offered, unquoted = defaultdict(int), defaultdict(int)
    for r in reveal["requests"]:
        quote = r["quote"] or {}
        for o in r["request"]["options"]:
            offered[o["kind"]] += 1
            if quote.get(o["kind"]) is None:
                unquoted[o["kind"]] += 1
    print("offered options unquoted, by kind:",
          {k: f"{unquoted[k]}/{offered[k]}" for k in offered})
    print()

    # Declines: no quote, or a quote far above list.
    for t in (1.5, 2.0, 3.0):
        far = sum(1 for r in rows if r["min_ratio"] is not None and r["min_ratio"] > t)
        print(f"min quote/list > {t}: {far} requests ({far / n:.1%}), "
              f"of which won {sum(r['won'] for r in rows if r['min_ratio'] is not None and r['min_ratio'] > t)}")
    print()

    # What we won vs lost looks like.
    for label, sel in (("won", lambda r: r["won"]), ("lost", lambda r: not r["won"])):
        g = [r for r in rows if sel(r)]
        print(f"{label}: {len(g)} requests, avg cheapest list {sum(r['cheapest_lp'] for r in g) / len(g) / 100:.2f}€, "
              f"avg road {sum(r['road'] for r in g) / len(g):.0f} km, "
              f"avg margin/order {(sum(r['margin'] for r in g if r['won']) / max(1, sum(r['won'] for r in g))) / 100:.2f}€")
    won_margin = sum(r["margin"] for r in rows if r["won"])
    print(f"total won margin {won_margin / 100:.2f}€, revenue share of it "
          f"{sum(1 for r in rows if r['won'])} orders")
    # Ratio where we win vs lose, on the cheapest option.
    for label, sel in (("won", lambda r: r["won"]), ("lost", lambda r: not r["won"])):
        g = [r["cheapest_ratio"] for r in rows if sel(r) and r["cheapest_ratio"] is not None]
        print(f"avg cheapest-option quote/list when {label}: {sum(g) / len(g):.3f} (n={len(g)})")


if __name__ == "__main__":
    analyse(sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "final-1800"))
