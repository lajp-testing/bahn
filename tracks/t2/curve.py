"""Win rate by quoted price (times list), on the price-war day and on the other days, 08:00-18:00, over saved weeks."""
import gzip, json, sys
from pathlib import Path
rows = [json.loads(l) for l in open('data/runs.jsonl')]
war_b = {}; other_b = {}
for label in sys.argv[1:]:
    for x in {r['seed']: r for r in rows if r['label'] == label}.values():
        rev = json.load(gzip.open(Path('data/runs') / Path(x['folder']).name / 'reveal.json.gz', 'rt'))
        q = []
        for item in rev['requests']:
            rq = item['request']; day, minute = divmod(rq['arrivedAt'], 1440)
            if not item['quote'] or day > 4 or not 480 <= minute < 1080: continue
            lists = {o['kind']: o['listPriceCents'] for o in rq['options']}
            ratio = min(item['quote'][k] / lists[k] for k in item['quote'])
            if ratio <= 3: q.append((day, ratio, item['outcome'] == 'won'))
        rate = {d: sum(w for dd, r, w in q if dd == d) / max(1, sum(1 for dd, r, w in q if dd == d)) for d in range(5)}
        war = min(rate, key=rate.get)
        for d, r, w in q:
            s = (war_b if d == war else other_b).setdefault(min(2.2, max(1.0, round(r * 10) / 10)), [0, 0]); s[0] += 1; s[1] += w
print('price/list   war day: n win%    other days: n win%')
for b in sorted(set(war_b) | set(other_b)):
    a, c = war_b.get(b, [0, 0]), other_b.get(b, [0, 0])
    print(f"{b:>9.1f}   {a[0]:>6} {100 * a[1] / max(1, a[0]):>4.0f}%        {c[0]:>6} {100 * c[1] / max(1, c[0]):>4.0f}%")
