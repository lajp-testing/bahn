"""Refund tiers: how many orders of each label ended in each late-refund tier, and the refunds, over the seeds both
labels hold; then the orders whose tier differs between the two labels. Reads saved weeks only.

    python3 tracks/t3/tiers.py b26-fix-wo t3s10-calm
"""
import collections, sys, os
sys.path.insert(0, os.path.dirname(__file__))
from late_cars import weeks, orders


def main(a, b):
    A, B = weeks(a), weeks(b)
    seeds = sorted(set(A) & set(B))
    cnt = {a: collections.Counter(), b: collections.Counter()}
    ref = collections.Counter(); fee = collections.Counter()
    moves = collections.Counter()
    for s in seeds:
        oa, ob = orders(A[s]), orders(B[s])
        for L, o in ((a, oa), (b, ob)):
            for x in o.values():
                cnt[L][x["tier"] or "on time"] += 1
                ref[L] += x["refund"]; fee[L] += x["fee"]
        for oid in set(oa) & set(ob):
            ta, tb = oa[oid]["tier"] or "on time", ob[oid]["tier"] or "on time"
            if ta != tb:
                moves[(ta, tb)] += 1
    print(f"{len(seeds)} seeds")
    for L in (a, b):
        print(f"{L}: refunds €{ref[L]/100:,.0f} fees €{fee[L]/100:,.0f} tiers {dict(cnt[L].most_common())}")
    print("tier moves", a, "->", b)
    for k, v in moves.most_common(15):
        print(f"  {v:4} {k[0]} -> {k[1]}")


if __name__ == "__main__":
    main(*sys.argv[1:3])
