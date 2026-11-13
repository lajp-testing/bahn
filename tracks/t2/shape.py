"""The true shape of the chance curve, from the six scans (step 2 of stint 6).

z = an option's switching ratio minus the mean ratio of its world and day,
within one option kind (the kind's own day mean, so a kind's level offset is
removed first). S(z) = the share of scanned options whose leftover is above z,
next to the logistic chance 1/(1+exp(z/s)) the quoter assumes.

Run locally: python3 tracks/t2/shape.py [kind]
"""
import json
import sys
from pathlib import Path

TRACK = Path(__file__).resolve().parent


def load(kind):
    rows = []
    for path in sorted(TRACK.glob('scan-t2-scan-*-l8.jsonl')):
        for line in path.open():
            r = json.loads(line)
            if r['switch_high'] == 0 or r['option'] != kind:
                continue
            r['ratio'] = (r['switch_low'] + r['switch_high']) / 2
            rows.append(r)
    return rows


def main():
    kind = sys.argv[1] if len(sys.argv) > 1 else 'same_day'
    rows = load(kind)
    sums, counts = {}, {}
    for r in rows:
        key = (r['seed'], r['arrival'] // 1440)
        sums[key] = sums.get(key, 0.0) + r['ratio']
        counts[key] = counts.get(key, 0) + 1
    means = {k: sums[k] / counts[k] for k in sums}
    zs = sorted(r['ratio'] - means[(r['seed'], r['arrival'] // 1440)] for r in rows if (r['seed'], r['arrival'] // 1440) in means)
    print(f"kind {kind}: {len(zs)} rows, {len(means)} world-days")
    print(f"{'z':>6} {'S(z)':>7} {'log .2':>7} {'log .3':>7} {'S-log.2':>8}")
    for i in range(41):
        z = -1.0 + 0.05 * i
        s = sum(1 for x in zs if x > z) / len(zs)
        l2, l3 = 1 / (1 + 2 ** (z / 0.2 * 0)) or 0, 0  # placeholder removed below
        l2 = 1 / (1 + 2.718281828459045 ** (z / 0.2)) if z / 0.2 < 40 else 0.0
        l3 = 1 / (1 + 2.718281828459045 ** (z / 0.3)) if z / 0.3 < 40 else 0.0
        print(f"{z:>6.2f} {s:>7.3f} {l2:>7.3f} {l3:>7.3f} {s - l2:>8.3f}")


if __name__ == '__main__':
    main()
