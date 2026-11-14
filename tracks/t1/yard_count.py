"""How often the quoter's yard discount applied in saved weeks of a label.

Replays each week's event log in desk order: a request is open from its price_request until the
dealer decides (order_won / order_lost) or the order is cancelled. A request hits the discount when
another open request waits within `yard_km` road km of its pickup for a delivery within 100 km.

    python3 -m tracks.t1.yard_count g1-yard15
"""
from __future__ import annotations

import gzip
import json
import os
import sys

HOME = os.environ.get("SPREAD_HOME", "/home/agent/.t3/projects/bahn")
DATA = os.path.join(HOME, "data")


def rows(label: str) -> list[dict]:
    with open(os.path.join(DATA, "runs.jsonl"), encoding="utf-8") as index:
        return [json.loads(line) for line in index if line.strip()
                and json.loads(line).get("label") == label and not json.loads(line).get("board")]


def read(folder: str, name: str):
    with gzip.open(os.path.join(DATA, "runs", folder, name), "rt", encoding="utf-8") as file:
        return [json.loads(line) for line in file if line.strip()]


def main() -> None:
    label = sys.argv[1] if len(sys.argv) > 1 else "g1-yard15"
    yard_km = 10.0
    with open(os.path.join(DATA, "map.json"), encoding="utf-8") as file:
        road = {(r["from"], r["to"]): r["km"] for r in json.load(file)["roads"]}
    total = hits = quoted = requests = 0
    for row in sorted(rows(label), key=lambda r: str(r["seed"])):
        open_: dict[str, dict] = {}
        hit, quote, n = 0, 0, 0
        quotes = {a["action"]["requestId"] for a in read(os.path.basename(row["folder"]), "actions.jsonl.gz")
                  if a["action"]["type"] == "quote"}
        for event in read(os.path.basename(row["folder"]), "events.jsonl.gz"):
            kind = event["kind"]
            if kind == "price_request":
                request = event["request"]
                n += 1
                leg = request["legs"][0]
                pickup, delivery = leg["pickup"]["placeId"], leg["delivery"]["placeId"]
                if any(other_id != request["id"]
                       and road[(other["legs"][0]["pickup"]["placeId"], pickup)] <= yard_km
                       and road[(other["legs"][0]["delivery"]["placeId"], delivery)] <= 100
                       for other_id, other in open_.items()):
                    hit += 1
                    quote += request["id"] in quotes
                open_[request["id"]] = request
            elif kind == "order_won":
                open_.pop(event["order"]["id"], None)
            elif kind == "order_lost":
                open_.pop(event["requestId"], None)
            elif kind == "order_cancelled":
                open_.pop(event["orderId"], None)
        print(f"{row['seed']}: {n} requests, discount on {hit} ({hit / max(n, 1):.0%}), of those quoted {quote}")
        total, hits, quoted, requests = total + hit, hits + hit, quoted + quote, requests + n
    print(f"total: {requests} requests, discount on {hits} ({hits / max(requests, 1):.0%}), of those quoted {quoted}")


if __name__ == "__main__":
    main()
