"""Booked fee / fee at the booking driver's first view, and minutes from that view to booking, by day of booking (dev seeds)."""
import collections, gzip, json, statistics, sys
from pathlib import Path
root = Path('/home/agent/.t3/projects/bahn/data/runs')
for label in sys.argv[1:]:
    by = collections.defaultdict(list); seen = set()
    for p in sorted(root.iterdir(), reverse=True):
        try: meta = json.loads((p/'result.json').read_text())
        except Exception: continue
        if meta.get('label') != label or not str(meta.get('seed')).startswith('dev-') or meta['seed'] in seen: continue
        seen.add(meta['seed'])
        sched = {}
        with gzip.open(p/'actions.jsonl.gz','rt') as f:
            for x in map(json.loads, f):
                if x['action']['type'] == 'post' and x['result'].get('ok'):
                    sched[x['result']['id']] = sorted((s['at'], s['feeCents']) for s in x['action']['schedule'])
        first = {}
        with gzip.open(p/'events.jsonl.gz','rt') as f:
            for e in map(json.loads, f):
                if e['kind'] == 'gig_viewed': first.setdefault((e['gigId'], e['driverId']), e['at'])
                elif e['kind'] == 'gig_booked' and e['gigId'] in sched:
                    v = first.get((e['gigId'], e['driverId']))
                    if v is None: continue
                    fee = [c for a, c in sched[e['gigId']] if a <= v]
                    fee = fee[-1] if fee else sched[e['gigId']][0][1]
                    by[e['at'] // 1440].append((e['feeCents'] / fee, e['at'] - v))
    print(label, len(seen), 'weeks')
    for d in sorted(by):
        r = by[d]; print(f"  {'Mon Tue Wed Thu Fri Sat Sun'.split()[d] if d < 7 else d}: n {len(r):4d}  mean ratio {statistics.mean(x for x,_ in r):.2f}  mean minutes {statistics.mean(m for _,m in r):5.0f}")
