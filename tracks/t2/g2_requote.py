"""Compare the g2 re-quote runs with the mainline label on the rob seeds, and count re-quotes.

Usage: python3 tracks/t2/g2_requote.py LABEL [LABEL ...]
Reads /home/agent/.t3/projects/bahn/data/runs.jsonl and each week's actions.jsonl.gz; ignores board rows.
"""
import gzip
import json
import os
import sys

RUNS = "/home/agent/.t3/projects/bahn/data/runs.jsonl"
DATA = "/home/agent/.t3/projects/bahn/data/runs"
BASE = "b89-main"
SEEDS = [f"rob-{n}" for n in range(21, 31)]


def rows(label):
    out = {}
    with open(RUNS) as f:
        for line in f:
            r = json.loads(line)
            if r["label"] == label and r["seed"] in SEEDS and not r.get("board"):
                out[r["seed"]] = r
    return out

def requotes(folder):
    """Quote actions sent per request: (requests quoted again, extra quote actions, requests quoted)."""
    folder = os.path.join(DATA, os.path.basename(folder))
    seen = {}
    with gzip.open(os.path.join(folder, "actions.jsonl.gz"), "rt", encoding="utf-8") as f:
        for line in f:
            row = json.loads(line)
            action = row["action"]
            if action["type"] == "quote" and row["result"].get("ok"):
                seen[action["requestId"]] = seen.get(action["requestId"], 0) + 1
    twice = sum(1 for n in seen.values() if n > 1)
    return twice, sum(n - 1 for n in seen.values() if n > 1), len(seen)


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
    rq_b = sum(base[s]["requests"] for s in SEEDS)
    rq = sum(r[s]["requests"] for s in SEEDS)
    higher = sum(1 for s in SEEDS if r[s]["marginCents"] > base[s]["marginCents"])
    lower = sum(1 for s in SEEDS if r[s]["marginCents"] < base[s]["marginCents"])
    print(f"== {label} vs {BASE} (10 rob weeks) ==")
    print(f"total margin: {tm/100:,.2f} EUR vs {tm_b/100:,.2f} EUR  diff {((tm-tm_b)/100):+,.2f} EUR")
    print(f"weeks higher/lower/equal: {higher}/{lower}/{10-higher-lower}")
    print(f"orders: {o} vs {ob}  per week {o/10:.1f} vs {ob/10:.1f}  diff {o-ob:+d}")
    print(f"requests: {rq} vs {rq_b}  per week {rq/10:.0f} vs {rq_b/10:.0f}  diff {rq-rq_b:+d}")
    lows = sorted(SEEDS, key=lambda s: r[s]["onTimeShare"])[:3]
    print("3 lowest onTimeShare weeks: " + ", ".join(
        f"{s} {r[s]['onTimeShare']*100:.1f}% (base {base[s]['onTimeShare']*100:.1f}%)" for s in lows))
    per = ", ".join(f"{s} {(r[s]['marginCents']-base[s]['marginCents'])/100:+,.0f}" for s in SEEDS)
    print("per-week margin diff (EUR): " + per)
    counted = {s: requotes(r[s]["folder"]) for s in SEEDS}
    print("re-quotes per week (requests quoted again / extra quote actions / requests quoted): " + ", ".join(
        f"{s} {counted[s][0]}/{counted[s][1]}/{counted[s][2]}" for s in SEEDS))
    print(f"totals: {sum(c[0] for c in counted.values())} requests quoted again, "
          f"{sum(c[1] for c in counted.values())} extra quote actions over {sum(c[2] for c in counted.values())} quoted")
    print()


def main():
    base = rows(BASE)
    for label in sys.argv[1:]:
        report(label, base)


if __name__ == "__main__":
    main()
