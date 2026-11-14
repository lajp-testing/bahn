"""The price-war day in saved weeks: found after the fact as the working day with the lowest win rate; what we quoted and won on it, hour by hour, and on the next morning."""
import gzip, json, sys
from pathlib import Path
rows = [json.loads(l) for l in open('data/runs.jsonl')]
hours = {}; nxt = {}; usual = {}; days = []
for label in sys.argv[1:]:
    for x in {r['seed']: r for r in rows if r['label'] == label}.values():
        rev = json.load(gzip.open(Path('data/runs') / Path(x['folder']).name / 'reveal.json.gz', 'rt'))
        q = []
        for item in rev['requests']:
            rq = item['request']; day, minute = divmod(rq['arrivedAt'], 1440)
            if not item['quote']: continue
            lists = {o['kind']: o['listPriceCents'] for o in rq['options']}
            ratio = min(item['quote'][k] / lists[k] for k in item['quote'])
            if ratio > 3 or day > 4: continue
            q.append((day, minute // 60, ratio, item['outcome'] == 'won'))
        rate = {d: sum(w for dd, h, r, w in q if dd == d and 8 <= h < 18) / max(1, sum(1 for dd, h, r, w in q if dd == d and 8 <= h < 18)) for d in range(5)}
        war = min(rate, key=rate.get); others = [rate[d] for d in rate if d != war]
        days.append((x['seed'], war, round(100 * rate[war]), round(100 * sum(others) / 4), round(100 * min(others))))
        for d, h, r, w in q:
            book = hours if d == war else nxt if d == war + 1 else usual
            s = book.setdefault(h, [0, 0, 0.0]); s[0] += 1; s[1] += w; s[2] += r
print('weeks', len(days), 'war day by weekday', {d: sum(1 for t in days if t[1] == d) for d in range(5)})
print('win % on the war day / mean of other days / lowest other day, per week:', [(t[2], t[3], t[4]) for t in days])
print('hour   war day: n win% price   next day: n win% price   other days: n win% price')
for h in range(8, 19):
    cells = []
    for book in (hours, nxt, usual):
        n, w, r = book.get(h, [0, 0, 0.0]); cells.append(f"{n:>5} {100 * w / max(1, n):>3.0f}% {r / max(1, n):.2f}")
    print(f"{h:>4}   " + '      '.join(cells))
