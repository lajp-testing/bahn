"""Compare labels' dev weeks group by group: orders, on-time share, margin per order and in total.

    python3 tracks/t1/ceiling.py t1s11-base t1s13-flood [t1s13-wide]
"""
import collections, gzip, json, os, sys
sys.path.insert(0, os.getcwd())
from harness import config
from harness.orders import orders_of
from harness.play import read_index


def rows_of(label):
    out = []
    for row in read_index():
        if row["label"] == label and row["level"] == 8 and row["seed"] in config.SEEDS["dev"]:
            folder = os.path.join(config.RUNS, os.path.basename(row["folder"]))
            snap = json.load(gzip.open(os.path.join(folder, "snapshot.json.gz"), "rt"))
            size = collections.Counter()
            for gig in snap["gigs"]:
                ids = {s["orderId"] for s in gig["stops"]}
                for o in ids:
                    size[o] = max(size[o], len(ids))
            for r in orders_of(folder):
                r["bundled"] = size[r["id"]] > 1
                r["seed"] = row["seed"]
                out.append(r)
    return out


def band(v, edges):
    return next((f"<{e}" for e in edges if v < e), f">={edges[-1]}")


KEYS = {
    "km": lambda r: band(r["km"], [100, 200, 300, 500]),
    "option": lambda r: r["option"],
    "near P": lambda r: band(r["near_pickup"], [10, 30, 80]),
    "near D": lambda r: band(r["near_delivery"], [10, 30, 80]),
    "P/D": lambda r: ("P+" if r["near_pickup"] >= 30 else "P-") + ("D+" if r["near_delivery"] >= 30 else "D-"),
    "day": lambda r: str(r["day"]),
    "private": lambda r: str(r["private"]),
    "bundled": lambda r: str(r["bundled"]),
}

labels = sys.argv[1:]
data = {l: rows_of(l) for l in labels}
for l, rs in data.items():
    print(f"{l}: {len(rs)} orders, {1 - sum(r['late'] for r in rs) / len(rs):.1%} on time, €{sum(r['margin'] for r in rs):,.0f}, €{sum(r['margin'] for r in rs)/len(rs):.1f}/order")
for name, key in KEYS.items():
    print(f"\n{name:10}" + "".join(f" | {l[-8:]:>8}: n  ontime  €/ord   tot€" for l in labels))
    groups = sorted({key(r) for rs in data.values() for r in rs})
    for g in groups:
        line = f"{g:10}"
        for l in labels:
            sub = [r for r in data[l] if key(r) == g]
            n = len(sub) or 1
            line += f" | {len(sub):>11} {1 - sum(r['late'] for r in sub) / n:>6.1%} {sum(r['margin'] for r in sub) / n:>6.1f} {sum(r['margin'] for r in sub):>6,.0f}"
        print(line)
