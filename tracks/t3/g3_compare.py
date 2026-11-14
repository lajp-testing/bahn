"""Compare g3 sweep labels against the b46-car105-sameday480 baseline on the dev seeds."""
import json
from pathlib import Path

BASE = "b46-car105-sameday480"
LABELS = ["g3-flatup20", "g3-patience60", "g3-endcar112"]
RUNS = Path("/home/agent/.t3/projects/bahn/data/runs.jsonl")

rows = {}
with open(RUNS) as f:
    for line in f:
        r = json.loads(line)
        if r.get("board"):
            continue
        rows.setdefault(r["label"], {})[r["seed"]] = r

base = rows.get(BASE, {})
print(f"baseline {BASE}: {len(base)} non-board weeks in index\n")

for label in LABELS:
    lab = rows.get(label, {})
    common = sorted(set(base) & set(lab))
    if not common:
        print(f"{label}: no common seeds yet")
        continue
    dm = sum(lab[s]["marginCents"] - base[s]["marginCents"] for s in common)
    higher = sum(1 for s in common if lab[s]["marginCents"] > base[s]["marginCents"])
    orders = sum(lab[s]["wonOrders"] for s in common)
    # margin per car: use revenue as car proxy? no: use undelivered? Use wonOrders per week and margin
    print(f"== {label} vs {BASE} ({len(common)} common seeds) ==")
    print(f"total margin diff: {dm/100:+,.2f} EUR")
    print(f"weeks with higher margin: {higher}/{len(common)}")
    print(f"orders per week: {orders/len(common):.1f}")
    print(f"margin per car (cents/order): {sum(lab[s]['marginCents'] for s in common)/orders:.0f}")
    worst = sorted(common, key=lambda s: lab[s]["onTimeShare"])[:3]
    print("3 lowest onTimeShare weeks: " + ", ".join(
        f"{s} {lab[s]['onTimeShare']:.1%} (base {base[s]['onTimeShare']:.1%})" for s in worst))
    print()
