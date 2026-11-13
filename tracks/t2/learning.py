"""Fit a shared logistic midpoint on prefixes of Monday's randomized quotes."""
import gzip, json, math, sys
from harness.play import read_index
for row in read_index():
    if row['label'] != sys.argv[1]: continue
    reveal = json.load(gzip.open(row['folder'] + '/reveal.json.gz', 'rt'))
    observations = []
    for item in sorted(reveal['requests'], key=lambda x: x['request']['arrivedAt']):
        request, quote = item['request'], item['quote']
        if request['arrivedAt'] >= 1440 or not quote or item['outcome'] not in ('won', 'lost'): continue
        option = request['options'][0]
        observations.append((quote[option['kind']] / option['listPriceCents'], item['outcome'] == 'won'))
    print(row['seed'], 'Monday observations', len(observations))
    for n in (20, 50, 100, len(observations)):
        sample = observations[:n]
        def loss(mid):
            total = 0
            for price, won in sample:
                z = max(-30, min(30, (price-mid)/.10))
                total += math.log1p(math.exp(z)) if won else math.log1p(math.exp(-z))
            return total
        print(n, min((i/1000 for i in range(900, 2001)), key=loss))
