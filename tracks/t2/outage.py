"""The outage in saved weeks, found after the fact: the day and the 80 km region whose requests won far more often than their prices explain. Then: what we quoted and won inside it."""
import gzip, json, math, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from dispatch.context import Context
ctx = Context.build(8, json.load(open('data/map.json')), [])
rows = [json.loads(l) for l in open('data/runs.jsonl')]
side = sys.argv[1]; inside = {}; outside = {}; found = []
near = {a: {b for b in ctx.places if ctx.straight_km(a, b) <= 80} for a in ctx.places}
for label in sys.argv[2:]:
    for x in {r['seed']: r for r in rows if r['label'] == label}.values():
        rev = json.load(gzip.open(Path('data/runs') / Path(x['folder']).name / 'reveal.json.gz', 'rt'))
        q = []
        for item in rev['requests']:
            rq = item['request']; day, minute = divmod(rq['arrivedAt'], 1440)
            if not item['quote'] or day > 4 or not 480 <= minute < 1080: continue
            lists = {o['kind']: o['listPriceCents'] for o in rq['options']}
            ratio = min(item['quote'][k] / lists[k] for k in item['quote'])
            if ratio <= 3: q.append((day, rq['legs'][0][side]['placeId'], min(2.2, max(1.0, round(ratio * 10) / 10)), item['outcome'] == 'won', minute // 60))
        bucket = {}
        for d, p, b, w, h in q:
            s = bucket.setdefault(b, [0, 0]); s[0] += 1; s[1] += w
        expect = {b: s[1] / s[0] for b, s in bucket.items()}
        best = None
        for d in range(5):
            for centre in ctx.places:
                sel = [(b, w) for dd, p, b, w, h in q if dd == d and p in near[centre]]
                if len(sel) < 8: continue
                var = sum(expect[b] * (1 - expect[b]) for b, w in sel) or 1
                score = sum(w - expect[b] for b, w in sel) / math.sqrt(var)
                if best is None or score > best[0]: best = (score, d, centre, len(sel))
        score, d, centre, n = best
        found.append((x['seed'], d, ctx.places[centre]['name'], n, round(score, 1), round(100 * n / len(q))))
        for dd, p, b, w, h in q:
            if dd == d:
                s = (inside if p in near[centre] else outside).setdefault(b, [0, 0]); s[0] += 1; s[1] += w
print(side, 'weeks', len(found))
print('seed, day, centre, requests inside, score, % of the week:', found[:30])
print('price/list   inside that day: n win%    outside that day: n win%')
for b in sorted(set(inside) | set(outside)):
    a, c = inside.get(b, [0, 0]), outside.get(b, [0, 0])
    print(f"{b:>9.1f}   {a[0]:>6} {100 * a[1] / max(1, a[0]):>4.0f}%        {c[0]:>6} {100 * c[1] / max(1, c[0]):>4.0f}%")
