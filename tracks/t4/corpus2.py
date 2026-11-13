"""Builds the notes corpus from every saved reveal: one row per noted request, with the truth where we won the order.

    python3 tracks/t4/corpus2.py            writes data/notes_corpus.jsonl and prints its size
"""
from __future__ import annotations

import glob
import gzip
import json
import os
import sys

sys.path.insert(0, os.getcwd())
from harness import config  # noqa: E402


def rows():
    index = {os.path.basename(json.loads(line)["folder"]): json.loads(line) for line in open(config.INDEX, encoding="utf-8") if line.strip()}
    seen = {}
    for folder in sorted(glob.glob(os.path.join(config.RUNS, "*"))):
        row = index.get(os.path.basename(folder))
        path = os.path.join(folder, "reveal.json.gz")
        if row is None or not os.path.exists(path) or os.path.getsize(path) < 100:
            continue
        try:
            reveal = json.load(gzip.open(path, "rt", encoding="utf-8"))
        except Exception:
            continue
        truth = {order["orderId"]: order["legs"] for order in reveal["orders"]}
        for item in reveal["requests"]:
            request = item["request"]
            if not request["note"]:
                continue
            key = (row["level"], row["seed"], request["id"])
            legs = truth.get(request["id"])
            if key in seen and (seen[key]["truth"] is not None or legs is None):
                continue
            seen[key] = {"level": row["level"], "seed": row["seed"], "request": request, "truth": legs, "option": item["option"]}
    return list(seen.values())


if __name__ == "__main__":
    out = rows()
    path = os.path.join(config.DATA, "notes_corpus.jsonl")
    with open(path, "w", encoding="utf-8") as file:
        for row in out:
            file.write(json.dumps(row, ensure_ascii=False) + "\n")
    seeds = sorted({(r["level"], r["seed"]) for r in out})
    print(len(out), "noted requests,", sum(1 for r in out if r["truth"]), "with truth,", len(seeds), "weeks:", seeds)
