"""Compare g3 quoter level-speed sweep labels against b52-fee4-car110 on the dev seeds."""
import json
from pathlib import Path

BASE = "b52-fee4-car110"
LABELS = ["g3-step10", "g3-boost5"]
RUNS = Path("/home/agent/.t3/projects/bahn/data/runs.jsonl")
rows = {}
with open(RUNS) as f:
    for line in f:
        r = json.loads(line)
        if r.get("board"):
            continue
        rows.setdefault(r["label"], {})[r["seed"]] = r

base = {s: r for s, r in rows.get(BASE, {}).items() if s.startswith("dev-")}
print(f"baseline {BASE}: {len(base)} dev weeks in index")
print(f"baseline dev totals: margin EUR "
      f"{sum(r['marginCents'] for r in base.values())/100:,.0f}, "
      f"orders/wk {sum(r['wonOrders'] for r in base.values())/max(len(base),1):.1f}, "
      f"EUR/car {sum(r['marginCents'] for r in base.values())/max(sum(r['wonOrders'] for r in base.values()),1)/100:.2f}\n")

for label in LABELS:
    lab = rows.get(label, {})
    common = sorted(set(base) & set(lab))
    if not common:
        print(f"{label}: no common seeds yet")
        continue
    dm = sum(lab[s]["marginCents"] - base[s]["marginCents"] for s in common)
    higher = sum(1 for s in common if lab[s]["marginCents"] > base[s]["marginCents"])
    orders = sum(lab[s]["wonOrders"] for s in common)
    margin = sum(lab[s]["marginCents"] for s in common)
    print(f"== {label} vs {BASE} ({len(common)} common seeds) ==")
    print(f"total margin diff: {dm/100:+,.2f} EUR")
    print(f"weeks with higher margin: {higher}/{len(common)}")
    print(f"orders per week: {orders/len(common):.1f}")
    print(f"margin per car (EUR/order): {margin/orders/100:.2f}")
    worst = sorted(common, key=lambda s: lab[s]["onTimeShare"])[:3]
    print("3 lowest onTimeShare weeks: " + ", ".join(
        f"{s} {lab[s]['onTimeShare']:.1%} (base {base[s]['onTimeShare']:.1%})" for s in worst))
    print()
