"""Compares two labels on the same seeds: margin euros, weeks higher, orders/week, lowest on-time weeks."""
import json
import sys

SEEDS = [f"dev-{i:02d}" for i in range(1, 11)] + ["rob-04", "rob-14", "rob-17"]


def rows(label):
    out = {}
    with open("/home/agent/.t3/projects/bahn/data/runs.jsonl") as fh:
        for line in fh:
            r = json.loads(line)
            if r["label"] == label and r["seed"] in SEEDS:
                out[r["seed"]] = r  # last wins
    return out


a, b = rows(sys.argv[1]), rows(sys.argv[2])
common = sorted(set(a) & set(b), key=lambda s: (s not in SEEDS, SEEDS.index(s) if s in SEEDS else 0))
dm = (sum(a[s]["marginCents"] for s in common) - sum(b[s]["marginCents"] for s in common)) / 100
higher = sum(a[s]["marginCents"] > b[s]["marginCents"] for s in common)
print(f"seeds: {len(common)}  margin {sys.argv[1]} vs {sys.argv[2]}: {dm:+.2f} EUR total, {higher}/{len(common)} weeks higher")
print(f"orders/week: {sum(a[s]['wonOrders'] for s in common)/len(common):.1f} vs {sum(b[s]['wonOrders'] for s in common)/len(common):.1f}")
for name, tab in ((sys.argv[1], a), (sys.argv[2], b)):
    low = sorted(common, key=lambda s: tab[s]["onTimeShare"])[:3]
    print(f"{name} lowest onTimeShare: " + ", ".join(f"{s} {tab[s]['onTimeShare']:.3f}" for s in low))
print(f"{'seed':8} {'dEUR':>8} {'onA':>6} {'onB':>6}")
for s in common:
    d = (a[s]["marginCents"] - b[s]["marginCents"]) / 100
    print(f"{s:8} {d:+8.2f} {a[s]['onTimeShare']:6.3f} {b[s]['onTimeShare']:6.3f}")
