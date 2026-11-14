"""Compare g2 option-kind sweeps with the mainline label on the dev seeds.

Usage: python3 tracks/t2/g2_compare.py LABEL [LABEL ...]
Reads /home/agent/.t3/projects/bahn/data/runs.jsonl; ignores board rows.
"""
import json
import sys

RUNS = "/home/agent/.t3/projects/bahn/data/runs.jsonl"
BASE = "b52-fee4-car110"
SEEDS = [f"dev-{i:02d}" for i in range(1, 11)]


def rows(label):
    out = {}
    with open(RUNS) as f:
        for line in f:
            r = json.loads(line)
            if r["label"] == label and r["seed"] in SEEDS and not r.get("board"):
                out[r["seed"]] = r
    return out


def report(label, base):
    r = rows(label)
    missing = [s for s in SEEDS if s not in r or s not in base]
    if missing:
        print(f"{label}: missing seeds {missing}")
        return
    tm_b = sum(base[s]["marginCents"] for s in SEEDS)
    tm = sum(r[s]["marginCents"] for s in SEEDS)
    ob = sum(base[s]["wonOrders"] for s in SEEDS)
    o = sum(r[s]["wonOrders"] for s in SEEDS)
    higher = sum(1 for s in SEEDS if r[s]["marginCents"] > base[s]["marginCents"])
    lower = sum(1 for s in SEEDS if r[s]["marginCents"] < base[s]["marginCents"])
    print(f"== {label} vs {BASE} (10 dev weeks) ==")
    print(f"total margin: {tm/100:,.2f} EUR vs {tm_b/100:,.2f} EUR  diff {((tm-tm_b)/100):+,.2f} EUR")
    print(f"weeks higher/lower/equal: {higher}/{lower}/{10-higher-lower}")
    print(f"orders: {o} vs {ob}  per week {o/10:.1f} vs {ob/10:.1f}  diff {o-ob:+d}")
    print(f"margin per car: {tm/o/100:.2f} EUR vs {tm_b/ob/100:.2f} EUR")
    lows = sorted(SEEDS, key=lambda s: r[s]["onTimeShare"])[:3]
    print("3 lowest onTimeShare weeks: " + ", ".join(
        f"{s} {r[s]['onTimeShare']*100:.1f}% (base {base[s]['onTimeShare']*100:.1f}%)" for s in lows))
    per = ", ".join(
        f"{s} {(r[s]['marginCents']-base[s]['marginCents'])/100:+,.0f}" for s in SEEDS)
    print("per-week margin diff (EUR): " + per)
    print()


def main():
    base = rows(BASE)
    for label in sys.argv[1:]:
        report(label, base)


if __name__ == "__main__":
    main()
