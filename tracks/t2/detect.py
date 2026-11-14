"""Would a running test find the outage live? For each request, in arrival order: z = sum(won - expected) / sqrt(variance) over the day's
earlier decided requests picked up within 80 km. Flag when z >= Z with at least N. Reports flags inside and outside the outage found after the fact."""
import gzip, json, math, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from dispatch.context import Context
ctx = Context.build(8, json.load(open('data/map.json')), [])
rows = [json.loads(l) for l in open('data/runs.jsonl')]
Z, N = float(sys.argv[1]), int(sys.argv[2])
near = {a: {b for b in ctx.places if ctx.straight_km(a, b) <= 80} for a in ctx.places}
tot = dict(true_flag=0, true_miss=0, false_flag=0, quiet=0); first = []
for label in sys.argv[3:]:
    for x in {r['seed']: r for r in rows if r['label'] == label}.values():
        rev = json.load(gzip.open(Path('data/runs') / Path(x['folder']).name / 'reveal.json.gz', 'rt'))
        q = []
        for item in rev['requests']:
            rq = item['request']; day, minute = divmod(rq['arrivedAt'], 1440)
            if not item['quote'] or day > 4 or not 480 <= minute < 1080: continue
            lists = {o['kind']: o['listPriceCents'] for o in rq['options']}
            ratio = min(item['quote'][k] / lists[k] for k in item['quote'])
            if ratio <= 3: q.append((rq['arrivedAt'], rq['respondBy'], rq['legs'][0]['pickup']['placeId'], min(2.2, max(1.0, round(ratio * 10) / 10)), item['outcome'] == 'won'))
        bucket = {}
        for at, by, p, b, w in q:
            s = bucket.setdefault(b, [0, 0]); s[0] += 1; s[1] += w
        expect = {b: s[1] / s[0] for b, s in bucket.items()}
        best = None  # the outage after the fact
        for d in range(5):
            for centre in ctx.places:
                sel = [(b, w) for at, by, p, b, w in q if at // 1440 == d and p in near[centre]]
                if len(sel) < 8: continue
                score = sum(w - expect[b] for b, w in sel) / math.sqrt(sum(expect[b] * (1 - expect[b]) for b, w in sel) or 1)
                if best is None or score > best[0]: best = (score, d, centre)
        score, od, centre = best
        seen_first = None
        for at, by, p, b, w in q:
            known = [(bb, ww) for a2, by2, p2, bb, ww in q if a2 // 1440 == at // 1440 and by2 <= at and p2 in near[p]]
            z = sum(ww - expect[bb] for bb, ww in known) / math.sqrt(sum(expect[bb] * (1 - expect[bb]) for bb, ww in known) or 1) if len(known) >= N else 0
            inside = at // 1440 == od and p in near[centre]
            flag = z >= Z
            tot['true_flag' if inside and flag else 'true_miss' if inside else 'false_flag' if flag else 'quiet'] += 1
            if inside and flag and seen_first is None: seen_first = at % 1440
        first.append(seen_first)
print('Z', Z, 'N', N, tot, 'first flag on the outage day (minute of day), median:', sorted(f for f in first if f)[len([f for f in first if f]) // 2], 'weeks never flagged:', sum(f is None for f in first))
