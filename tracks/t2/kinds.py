"""Win share of our quotes by option kind and price-ratio band, from saved weeks.

Reads the reveal of every week a label holds (runs.jsonl is the index): for each
quoted option, the ratio our price / list price, the band it falls in, and whether
that option was the one taken. Prints win shares per kind and band.

Run locally: python3 tracks/t2/kinds.py <label> [label ...]
"""
import gzip
import json
import sys
from collections import defaultdict
from pathlib import Path

DATA = Path("/home/agent/.t3/projects/bahn/data")
BANDS = [(0.0, 1.0), (1.0, 1.2), (1.2, 1.4), (1.4, 1.6), (1.6, 2.0), (2.0, 4.0), (4.0, 99.0)]


def band(ratio):
    return next(f"{lo:g}-{hi:g}" for lo, hi in BANDS if lo <= ratio < hi)


def main():
    labels = sys.argv[1:]
    rows = [json.loads(line) for line in (DATA / "runs.jsonl").open()]
    folders = [DATA / "runs" / r["folder"].split("/")[-1]
               for r in rows if r["label"] in labels and not r.get("board") and r["level"] == 8]
    cells = defaultdict(lambda: [0, 0])  # (kind, band) -> [quoted, taken]
    for folder in folders:
        reveal = json.load(gzip.open(folder / "reveal.json.gz", "rt"))
        for row in reveal["requests"]:
            lists = {o["kind"]: o["listPriceCents"] for o in row["request"]["options"]}
            for kind, cents in row["quote"].items():
                if kind not in lists or cents >= lists[kind] * 4:  # a declined quote says nothing
                    continue
                cells[(kind, band(cents / lists[kind]))][0] += 1
                if row["outcome"] == "won" and row["option"] == kind:
                    cells[(kind, band(cents / lists[kind]))][1] += 1
    kinds = sorted({k for k, _ in cells})
    bands = [f"{lo:g}-{hi:g}" for lo, hi in BANDS]
    print(f"{'kind':<15} " + " ".join(f"{b:>12}" for b in bands))
    for kind in kinds:
        cells_k = [(cells[(kind, b)][1] / cells[(kind, b)][0] if cells[(kind, b)][0] else None, cells[(kind, b)])
                   for b in bands]
        print(f"{kind:<15} " + " ".join(f"{(f'{s:.0%} {n[0]}' if s is not None else '-'):>12}" for s, n in cells_k))
    for kind in kinds:
        quoted = sum(n[0] for b in bands for n in [cells[(kind, b)]])
        taken = sum(n[1] for b in bands for n in [cells[(kind, b)]])
        print(f"{kind}: {taken}/{quoted} taken = {taken / max(1, quoted):.1%}")


if __name__ == "__main__":
    main()
