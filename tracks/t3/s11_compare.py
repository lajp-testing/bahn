"""Paired 30-seed comparison against b26-fix-wo, plus booked/first-viewed fee ratio by day."""
import json, sys, os, glob
from collections import defaultdict
DATA = "/home/agent/.t3/projects/bahn/data"
rows = [json.loads(l) for l in open(f"{DATA}/runs.jsonl")]
seeds = [f"dev-{i:02d}" for i in range(1, 11)] + [f"rob-{i:02d}" for i in range(1, 21)]
def get(label):
    d = {}
    for r in rows:
        if r["label"] == label and not r["board"] and r["seed"] in seeds:
            d[r["seed"]] = r
    return d
base = get("b26-fix-wo")
for label in sys.argv[1:]:
    v = get(label)
    common = [s for s in seeds if s in v and s in base]
    dm = sum(v[s]["marginCents"] - base[s]["marginCents"] for s in common) / 100
    ot = lambda d: sum(d[s]["onTimeShare"] * d[s]["wonOrders"] for s in common) / sum(d[s]["wonOrders"] for s in common)
    low = sorted(v[s]["onTimeShare"] for s in common)[:3]
    hi = sum(v[s]["marginCents"] > base[s]["marginCents"] for s in common)
    tot = sum(v[s]["marginCents"] for s in common) / 100
    print(f"{label}: {len(common)} weeks margin €{tot:,.2f} Δ€{dm:+,.2f}  on time {ot(v):.2%} vs {ot(base):.2%}  lowest {[round(x*100,1) for x in low]}  higher {hi}/{len(common)}  ranked {sum(v[s]['ranked'] for s in common)}")
