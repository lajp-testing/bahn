"""Step 3's order-shift check: does a fee model move the mix towards the cheap, safe groups?

    python3 tracks/t3/shift.py <label A> <label B>

Groups each label's dev-week orders by the lead from the request's arrival to the first leg's pickup
window opening (the cost table's groups), and prints counts, late share and margin per group.
"""
from __future__ import annotations

import collections
import gzip
import json
import os
import sys

from harness import config
from harness.play import read_index

HOUR = 60


def rows_of(label: str) -> list[dict]:
    # One row per seed, the last one, as harness.run does: an interrupted run can leave a week twice.
    done = {row["seed"]: row for row in read_index()
            if row["label"] == label and row["level"] == 8 and row["seed"] in config.SEEDS["dev"]}
    rows = []
    for row in done.values():
        folder = os.path.join(config.RUNS, os.path.basename(row["folder"]))
        snapshot = json.load(gzip.open(os.path.join(folder, "snapshot.json.gz"), "rt", encoding="utf-8"))
        reveal = json.load(gzip.open(os.path.join(folder, "reveal.json.gz"), "rt", encoding="utf-8"))
        requests = {item["request"]["id"]: item["request"] for item in reveal["requests"]}
        money: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
        gig_orders = {gig["id"]: sorted({stop["orderId"] for stop in gig["stops"]}) for gig in snapshot["gigs"]}
        with gzip.open(os.path.join(folder, "events.jsonl.gz"), "rt", encoding="utf-8") as events:
            for text in events:
                event = json.loads(text)
                if event["kind"] != "ledger":
                    continue
                line = event["line"]
                owners = [line["orderId"]] if line["orderId"] else gig_orders.get(line["gigId"] or "", [])
                for owner in owners:
                    money[owner][line["kind"]] += line["cents"] / len(owners)
        for order in snapshot["orders"]:
            if order["status"] == "cancelled" or order["id"] not in requests:
                continue
            request = requests[order["id"]]
            lines = money[order["id"]]
            lead = (request["legs"][0]["pickup"]["window"]["from"] - request["arrivedAt"]) / HOUR
            rows.append({
                "lead": "open/<=3h" if lead <= 3 else "3-12h" if lead <= 12 else "12-24h" if lead < 24 else "24h+",
                "late": lines["late_refund"] + lines["undelivered_penalty"] < 0,
                "margin": sum(lines.values()) / 100,
            })
    return rows


def group(name: str, rows: list[dict]) -> None:
    by: dict[str, list[dict]] = collections.defaultdict(list)
    for row in rows:
        by[row["lead"]].append(row)
    print(f"\n{name}: {len(rows)} orders, margin €{sum(r['margin'] for r in rows):,.0f}")
    print(f"{'lead to window':16} {'orders':>7} {'share':>7} {'late':>7} {'margin €':>9}")
    for key in ("open/<=3h", "3-12h", "12-24h", "24h+"):
        g = by.get(key, [])
        n = len(g)
        if not rows:
            continue
        print(f"{key:16} {n:>7} {n / len(rows):>7.1%} {(sum(r['late'] for r in g) / n if n else 0.0):>7.1%} {sum(r['margin'] for r in g):>9,.0f}")


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("usage: python3 tracks/t3/shift.py <label A> <label B>")
    for label in sys.argv[1:]:
        group(label, rows_of(label))


if __name__ == "__main__":
    main()
