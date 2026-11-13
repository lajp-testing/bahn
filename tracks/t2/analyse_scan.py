"""Descriptive first-option proxy; brackets leave up to 3.125 percentage points uncertainty."""
import glob
import heapq
import json
import math
import statistics

for path in sorted(glob.glob('tracks/t2/scan-*.jsonl')):
    rows = [json.loads(line) for line in open(path)]
    first = [r for r in rows if r['option'] == r['request']['options'][0]['kind']]
    if not first: continue
    print(path, 'first options', len(first))
    for mode in ('fixed 1.3', 'learning first-only', 'calibrate first 50'):
        midpoint, pending, wins, profit = 1.45, [], 0, 0
        observations = []
        for r in first:
            now = r['arrival']
            while pending and pending[0][0] <= now:
                _, ratio, won = heapq.heappop(pending)
                probability = 1/(1+math.exp(max(-40,min(40,(ratio-midpoint)/.1))))
                observations.append((ratio, won))
                if mode == 'learning first-only':
                    midpoint = max(.8,min(2.2,midpoint+.02*(won-probability)))
                elif mode == 'calibrate first 50' and len(observations) <= 50:
                    midpoint = max((n/100 for n in range(80,221)), key=lambda x: sum(-math.log1p(math.exp(max(-40,min(40,((p-x)/.1)*(1 if w else -1))))) for p,w in observations))
            base, fee = r['listPriceCents'], r['referenceFeeCents']
            if mode == 'fixed 1.3': ratio = 1.3
            elif mode == 'calibrate first 50' and len(observations) < 50:
                ratio = 1.0 + (int(r['request']['id'][1:]) % 21)*.05
            else:
                ratio = max(range(80,251), key=lambda n: (base*n/100-fee)/(1+math.exp(max(-40,min(40,(n/100-midpoint)/.1)))))/100
            won = ratio <= r['switch_low']
            wins += won
            profit += (round(base*ratio)-fee)*won
            heapq.heappush(pending,(r['request']['respondBy'],ratio,won))
        print(mode, 'wins',wins, f'{wins/len(first):.1%}', 'proxy euros',round(profit/100,2))
    for day in range(5):
        values = [(r['switch_low']+r['switch_high'])/2 for r in first if r['arrival']//1440 == day]
        if values: print('day',day,'n',len(values),'mean',round(statistics.mean(values),3))
