"""Structure of switching ratios across scanned worlds: prints tables for FINDINGS.

Ratio = midpoint of switch_low and switch_high; rows with switch_high == 0 are skipped.
First option of each request unless a table says otherwise.
Run locally: python3 tracks/t2/structure.py [seed ...]
"""
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

TRACK = Path(__file__).resolve().parent
KM_BANDS = [(0, 50, 'under 50'), (50, 150, '50-150'), (150, 300, '150-300'),
            (300, 500, '300-500'), (500, 10**9, 'over 500')]


def load(seeds=None):
    rows = []
    for path in sorted(TRACK.glob('scan-t2-scan-*-l8.jsonl')):
        for line in path.open():
            r = json.loads(line)
            if r['switch_high'] == 0:
                continue
            r['ratio'] = (r['switch_low'] + r['switch_high']) / 2
            r['day'] = r['arrival'] // 1440
            r['first'] = r['option'] == r['request']['options'][0]['kind']
            rows.append(r)
    if seeds:
        rows = [r for r in rows if r['seed'] in seeds]
    return rows


def mean(xs):
    return sum(xs) / len(xs)


def stdev(xs):
    if len(xs) < 2:
        return 0.0
    m = mean(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1))


def town_distance():
    places = {p['id']: (p['lat'], p['lon']) for p in json.load((TRACK / 'map.json').open())['places']}
    def dist(a, b):
        (la1, lo1), (la2, lo2) = places[a], places[b]
        dy = math.radians(la2 - la1)
        dx = math.radians(lo2 - lo1) * math.cos(math.radians((la1 + la2) / 2))
        return 6371 * math.hypot(dx, dy)
    return places, dist


def table(title, header, rows):
    print(f'\n## {title}')
    print('| ' + ' | '.join(header) + ' |')
    print('|' + '|'.join(['---'] * len(header)))
    for row in rows:
        print('| ' + ' | '.join(str(c) for c in row) + ' |')


def main():
    seeds = sys.argv[1:] or None
    rows = load(seeds)
    first = [r for r in rows if r['first']]
    seed_names = sorted({r['seed'] for r in rows})
    counts = ', '.join(f'{s} ({sum(1 for r in first if r["seed"] == s)})' for s in seed_names)
    print(f'Rows kept (switch_high>0): {len(rows)} total, {len(first)} first-option; seeds: {counts}')

    # a. Mean and stdev by day (first option) and by option kind (all rows).
    for seed in seed_names:
        srows = [r for r in first if r['seed'] == seed]
        days = sorted({r['day'] for r in srows})
        table(f'a. {seed}: first-option ratio by day',
              ['day', 'n', 'mean', 'stdev'],
              [[d, (n := sum(1 for r in srows if r['day'] == d)),
                round(mean([r['ratio'] for r in srows if r['day'] == d]), 3),
                round(stdev([r['ratio'] for r in srows if r['day'] == d]), 3)] for d in days])
    all_opt = defaultdict(list)
    for r in rows:
        all_opt[(r['seed'], r['option'])].append(r['ratio'])
    table('a. Ratio by option kind (all option rows, per seed)',
          ['seed', 'option', 'n', 'mean', 'stdev'],
          [[s, o, len(v), round(mean(v), 3), round(stdev(v), 3)]
           for (s, o), v in sorted(all_opt.items())])

    # b. Leftovers after removing each seed-day mean (first option).
    day_mean = {(r['seed'], r['day']): mean([x['ratio'] for x in first if x['seed'] == r['seed'] and x['day'] == r['day']])
                for r in first}
    for r in first:
        r['left'] = r['ratio'] - day_mean[(r['seed'], r['day'])]
    groups = {'dealer': lambda r: [r['dealer']],
              'pickup_town': lambda r: [r['pickup_town']],
              'delivery_town': lambda r: [r['delivery_town']],
              'km_band': lambda r: [next(band for lo, hi, band in KM_BANDS if lo <= r['km'] < hi)]}
    for name, keyfn in groups.items():
        vals = defaultdict(list)
        for r in first:
            for k in keyfn(r):
                vals[(r['seed'], k)].append(r['left'])
        table(f'b. Day-mean leftover by {name} (first option, n>=15)',
              ['seed', name, 'n', 'mean leftover'],
              [[s, k, len(v), round(mean(v), 3)]
               for (s, k), v in sorted(vals.items()) if len(v) >= 15])

    # c. Same entity across seeds: per-seed leftover side by side.
    for name in ('dealer', 'pickup_town', 'delivery_town'):
        per = defaultdict(lambda: defaultdict(list))
        for r in first:
            per[r[name]][r['seed']].append(r['left'])
        out = []
        for k, by_seed in sorted(per.items()):
            cells = {s: (mean(v), len(v)) for s, v in by_seed.items() if len(v) >= 15}
            if len(cells) < 2:
                continue
            means = [m for m, _ in cells.values()]
            same_sign = all(m > 0 for m in means) or all(m < 0 for m in means)
            spread = max(means) - min(means)
            out.append((k, cells, same_sign, spread))
        table(f'c. {name} leftover across seeds (n>=15 per seed; flag=same sign everywhere)',
              [name] + [f'{s} mean (n)' for s in seed_names] + ['same sign', 'spread'],
              [[k] + [f'{cells[s][0]:+.3f} ({cells[s][1]})' if s in cells else '' for s in seed_names]
               + ['yes' if same_sign else 'no', round(spread, 3)]
               for k, cells, same_sign, spread in out])

    # d. Outage and price war per seed.
    places, dist = town_distance()
    towns = sorted(places)
    region = {t: [u for u in towns if u == t or dist(t, u) <= 80] for t in towns}
    for seed in seed_names:
        srows = [r for r in first if r['seed'] == seed]
        days = sorted({r['day'] for r in srows})
        dmean = {d: mean([r['ratio'] for r in srows if r['day'] == d]) for d in days}
        others = {d: mean([r['ratio'] for r in srows if r['day'] != d]) for d in days}
        table(f'd. {seed}: price-war check - day mean vs mean of other days',
              ['day', 'n', 'day mean', 'other days mean', 'ratio'],
              [[d, sum(1 for r in srows if r['day'] == d), round(dmean[d], 3),
                round(others[d], 3), round(dmean[d] / others[d], 3)] for d in days])
        best = []
        for d in days:
            for anchor in towns:
                for side in ('pickup_town', 'delivery_town'):
                    inside = [r['left'] for r in srows if r['day'] == d and r[side] in region[anchor]]
                    outside = [r['left'] for r in srows if r['day'] == d and r[side] not in region[anchor]]
                    if len(inside) >= 15 and len(outside) >= 15:
                        best.append((mean(inside) - mean(outside), d, anchor, side,
                                     len(inside), round(mean(inside), 3), round(mean(outside), 3)))
        best.sort(reverse=True)
        table(f'd. {seed}: outage check - top day x 80km-region pickup/delivery leftovers (n>=15 both sides)',
              ['gap', 'day', 'region anchor', 'side', 'n in', 'mean in', 'mean out'],
              [[round(g, 3), d, a, s, n, mi, mo] for g, d, a, s, n, mi, mo in best[:8]])

    # e. How fast the day level shows.
    for seed in seed_names:
        srows = [r for r in first if r['seed'] == seed]
        out = []
        for d in sorted({r['day'] for r in srows}):
            day_rows = sorted([r for r in srows if r['day'] == d], key=lambda r: r['arrival'])
            full = mean([r['ratio'] for r in day_rows])
            out.append([d, len(day_rows), round(full, 3)] +
                       [round(mean([r['ratio'] for r in day_rows[:k]]) / full, 3) if len(day_rows) >= k else ''
                        for k in (10, 20, 40)])
        table(f'e. {seed}: mean of first 10/20/40 requests of the day over the whole day mean',
              ['day', 'n', 'day mean', 'first 10', 'first 20', 'first 40'], out)


if __name__ == '__main__':
    main()
