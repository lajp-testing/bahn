"""Leftover switching ratio per option kind, from the six scans.

Leftover = the option's switching ratio minus the mean ratio of the `next_day`
rows of the same world and day. Rows with switch_high == 0 (no positive price
wins) are skipped, as in structure.py.

Run locally: python3 tracks/t2/kinds2.py
"""
import json
from pathlib import Path

TRACK = Path(__file__).resolve().parent


def load():
    rows = []
    for path in sorted(TRACK.glob('scan-t2-scan-*-l8.jsonl')):
        for line in path.open():
            r = json.loads(line)
            if r['switch_high'] == 0:
                continue
            r['ratio'] = (r['switch_low'] + r['switch_high']) / 2
            r['day'] = r['arrival'] // 1440
            rows.append(r)
    return rows


def quantile(xs, q):
    """Linear-interpolation quantile, as numpy's default."""
    s = sorted(xs)
    pos = (len(s) - 1) * q
    lo = int(pos)
    hi = min(lo + 1, len(s) - 1)
    return s[lo] + (s[hi] - s[lo]) * (pos - lo)


def main():
    rows = load()
    sums, counts = {}, {}
    for r in rows:
        if r['option'] == 'next_day':
            key = (r['seed'], r['day'])
            sums[key] = sums.get(key, 0.0) + r['ratio']
            counts[key] = counts.get(key, 0) + 1
    means = {k: sums[k] / counts[k] for k in sums}
    by_kind = {}
    for r in rows:
        if (r['seed'], r['day']) in means:
            by_kind.setdefault(r['option'], []).append(r['ratio'] - means[(r['seed'], r['day'])])
    print(f"{'kind':<15} {'n':>5} {'mean':>7} {'q25':>7} {'q50':>7} {'q75':>7}")
    for kind in sorted(by_kind):
        xs = by_kind[kind]
        print(f"{kind:<15} {len(xs):>5} {sum(xs) / len(xs):>7.3f} "
              f"{quantile(xs, 0.25):>7.3f} {quantile(xs, 0.5):>7.3f} {quantile(xs, 0.75):>7.3f}")


if __name__ == '__main__':
    main()
