"""Per-dealer win rates at the same effective ratio, from saved weeks.

For every request we quoted with a real price (lowest quoted price over that option's
list price under 4), the effective ratio is (lowest price / list) / (the dealer's trust
factor at that moment).  The trust factor is rebuilt from the `ledger` events exactly as
`ProfitQuoter.count` does.  Prints, for the six largest dealers and all others, the
share won per day and per ratio band.

Usage: python3 tracks/t2/dealers.py [label]   (default t2s5-base)
"""
from __future__ import annotations

import gzip
import json
import os
import sys
from collections import defaultdict

INDEX = "/home/agent/.t3/projects/bahn/data/runs.jsonl"
RUNS = "/home/agent/.t3/projects/bahn/data/runs"
DAY = 24 * 60
BANDS = ((1.2, " <1.2"), (1.4, "1.2-1.4"), (1.6, "1.4-1.6"), (float("inf"), "  >1.6"))


def weeks(label: str):
    with open(INDEX, encoding="utf-8") as file:
        for line in file:
            row = json.loads(line)
            if row["label"] == label and not row.get("board"):
                yield os.path.join(RUNS, os.path.basename(row["folder"]))


def read(folder: str, name: str):
    with gzip.open(os.path.join(folder, name), "rt", encoding="utf-8") as file:
        for line in file:
            yield json.loads(line)


def scan(folder: str):
    """Yields (dealer, day, ratio, won) for every really-quoted request of one week."""
    events = list(read(folder, "events.jsonl.gz"))
    actions = sorted((a for a in read(folder, "actions.jsonl.gz") if a["action"]["type"] == "quote"
                      and a["result"].get("ok")), key=lambda a: a["at"])
    requests = {e["request"]["id"]: e["request"] for e in events if e["kind"] == "price_request"}
    won = {e["order"]["id"] for e in events if e["kind"] == "order_won"}
    lost = {e["requestId"] for e in events if e["kind"] == "order_lost"}

    counts: dict[str, int] = {}
    open_orders: dict[str, str] = {}     # order -> dealer, as ProfitQuoter keeps them
    before: dict[str, tuple[str, int]] = {}
    out = []
    i = 0

    def count(line):
        order = line.get("orderId")
        if line["kind"] == "revenue" and order in open_orders:
            dealer = open_orders.pop(order)
            before[order] = (dealer, counts.get(dealer, 0))
            counts[dealer] = min(25, counts.get(dealer, 0) + 1)
        elif line["kind"] == "late_refund" and order in before:
            dealer, was = before.pop(order)
            counts[dealer] = was // 2
        elif line["kind"] == "undelivered_penalty":
            open_orders.pop(order, None)

    for action in actions:
        while i < len(events) and events[i]["at"] <= action["at"]:
            event = events[i]
            i += 1
            if event["kind"] == "ledger":
                count(event["line"])
            elif event["kind"] == "order_won":
                open_orders[event["order"]["id"]] = event["order"]["dealerId"]
        request = requests.get(action["action"]["requestId"])
        if request is None:
            continue
        lists = {option["kind"]: option["listPriceCents"] for option in request["options"]}
        ratios = [cents / lists[kind] for kind, cents in action["action"]["prices"].items() if kind in lists]
        if not ratios or min(ratios) >= 4:
            continue  # the intake declined this request: it says nothing about the level
        rid = request["id"]
        if rid not in won and rid not in lost:
            continue
        factor = 1 + 0.01 * counts.get(request["dealerId"], 0)
        out.append((request["dealerId"], action["at"] // DAY, min(ratios) / factor, rid in won))
    return out


def main(label: str = "t2s5-base") -> None:
    rows = []
    for folder in weeks(label):
        rows += scan(folder)
    size = defaultdict(int)
    for dealer, day, ratio, won in rows:
        size[dealer] += 1
    top = [dealer for dealer, _ in sorted(size.items(), key=lambda kv: -kv[1])[:6]]
    groups = {dealer: dealer for dealer in top}
    print(f"{label}: {len(rows)} quoted requests in {sum(1 for _ in weeks(label))} weeks")
    print("dealer sizes:", ", ".join(f"{d}={size[d]}" for d in top))

    def table(key, order=None):
        head = order or sorted({key(row) for row in rows})
        print(f"{'':10}" + "".join(f"{h:>22}" for h in head))
        for dealer in top + ["others"]:
            cells = []
            for h in head:
                part = [row for row in rows
                        if (groups.get(row[0], "others") == dealer if dealer != "others" else row[0] not in groups)
                        and key(row) == h]
                cells.append(f"{len(part):>6} {sum(r[3] for r in part) / len(part):5.1%} "
                             f"{sum(r[2] for r in part) / len(part):5.2f}" if part else f"{'-':>22}")
            print(f"{dealer:10}" + "".join(cells))

    print("per day: requests, share won, mean ratio")
    table(lambda row: row[1])
    print("\nper ratio band: requests, share won, mean ratio")
    table(lambda row: next(name for edge, name in BANDS if row[2] < edge), [name for _, name in BANDS])


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "t2s5-base")
