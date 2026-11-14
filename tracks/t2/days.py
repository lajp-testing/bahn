"""Win rate and quoted price by day and dealer, 08:00 to 18:00, for a label's saved weeks: where are the outage and the price war?"""
import gzip, json, sys
from pathlib import Path
label, seeds = sys.argv[1], sys.argv[2:]
rows = [json.loads(l) for l in open('data/runs.jsonl')]
for seed in seeds:
    r = [x for x in rows if x['label'] == label and x['seed'] == seed][-1]
    rev = json.load(gzip.open(Path('data/runs') / Path(r['folder']).name / 'reveal.json.gz', 'rt'))
    stat = {}; batches = {}
    for q in rev['requests']:
        rq = q['request']; d = rq['dealerId']; day, minute = divmod(rq['arrivedAt'], 1440)
        if rq.get('batchId'): batches.setdefault(rq['batchId'], []).append((rq['arrivedAt'], d, q['outcome']))
        if not q['quote'] or not 480 <= minute < 1080: continue
        lists = {o['kind']: o['listPriceCents'] for o in rq['options']}
        ratio = min(q['quote'][k] / lists[k] for k in q['quote'])
        if ratio > 3: continue
        for key in ((day, d), (day, 'all')):
            s = stat.setdefault(key, [0, 0, 0.0]); s[0] += 1; s[1] += q['outcome'] == 'won'; s[2] += ratio
    dealers = sorted({d for _, d in stat if d != 'all'}, key=lambda d: -sum(stat.get((day, d), [0])[0] for day in range(5)))[:8] + ['all']
    print(seed, '   n win% price/list, by day')
    for d in dealers:
        cells = []
        for day in range(5):
            n, won, ratio = stat.get((day, d), [0, 0, 0.0])
            cells.append(f"{n:>3} {100 * won / max(1, n):>3.0f}% {ratio / max(1, n):.2f}")
        print(f"{d:>4}  " + '   '.join(cells))
    for b, items in batches.items():
        print('  batch', b, 'requests', len(items), 'at', sorted({i[0] for i in items})[:3], 'dealers', sorted({i[1] for i in items}), 'won', sum(i[2] == 'won' for i in items))
