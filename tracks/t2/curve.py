"""Summarise first-option grid outcomes, by price and day, from named run label."""
import collections, gzip, json, sys
from harness.play import read_index

rows = [r for r in read_index() if r['label'] == sys.argv[1]]
for row in rows:
    data = json.load(gzip.open(row['folder'] + '/reveal.json.gz', 'rt'))
    counts = collections.defaultdict(lambda: [0, 0])
    for item in data['requests']:
        req, quote = item['request'], item['quote']
        if not quote or item['outcome'] not in ('won', 'lost'):
            continue
        opt = req['options'][0]
        price = quote.get(opt['kind'])
        if price is None: continue
        bucket = round(price / opt['listPriceCents'] * 20) / 20
        day = req['arrivedAt'] // 1440
        for group in ('all', 'Monday' if day == 0 else 'later'):
            c = counts[group, bucket]; c[0] += item['outcome'] == 'won'; c[1] += 1
    print(row['seed'], 'margin', row['marginCents'], 'on time', row['onTimeShare'])
    for key, (wins, n) in sorted(counts.items()): print(*key, wins, n, round(wins / n, 3))
