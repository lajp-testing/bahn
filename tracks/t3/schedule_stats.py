"""Summarise booking fees and first-post learning proxies from saved weeks."""
import collections, gzip, json, statistics, sys
from pathlib import Path
root = Path('/home/agent/.t3/projects/bahn/data/runs')
for label in sys.argv[1:]:
    ratios, days = [], collections.defaultdict(list)
    bookings = drops = files = 0
    for p in root.iterdir():
        try:
            meta = json.loads((p/'result.json').read_text())
            if meta['label'] != label or not str(meta['seed']).startswith('dev-'): continue
            with gzip.open(p/'reveal.json.gz','rt') as f: req = {x['request']['id']: x['request'] for x in json.load(f)['requests']}
            with gzip.open(p/'actions.jsonl.gz','rt') as f: actions = [json.loads(x) for x in f]
            with gzip.open(p/'events.jsonl.gz','rt') as f: events = [json.loads(x) for x in f]
            if not events: continue
            files += 1; posts = {}
            for x in actions:
                a, result = x['action'], x['result']
                if a['type']=='post' and result.get('ok'):
                    oid = a['stops'][0]['orderId']
                    posts[result['id']] = (oid, x['at'], a['schedule'][0]['feeCents'], len({(s['orderId'],s['leg']) for s in a['stops']}) if False else None)
            for e in events:
                if e['kind'] == 'gig_dropped': drops += 1
                if e['kind'] != 'gig_booked': continue
                bookings += 1
                if e['gigId'] not in posts: continue
                oid, at, opening, _ = posts[e['gigId']]
                if oid in req:
                    # A post may cover fewer legs than the order; scale by the number of pickups.
                    a = next((x['action'] for x in actions if x['result'].get('id') == e['gigId'] and x['action']['type']=='post'), None)
                    cars = sum(1 for s in a['stops'] if s.get('kind') == 'pickup') if a else 0
                    if not cars: cars = len(req[oid]['legs'])
                    typical = req[oid]['referenceFeeCents'] * cars / len(req[oid]['legs'])
                    ratios.append(e['feeCents']/typical)
                days[at//1440].append((e['feeCents']/opening,e['at']-at))
        except FileNotFoundError: continue
    print(label, 'files',files,'bookings',bookings,'drops/booking',round(drops/bookings,3) if bookings else None,'mean fee/typical',round(statistics.mean(ratios),3) if ratios else None)
    for day, values in sorted(days.items()):
        print(' day',day,'n',len(values),'fee/open',round(statistics.mean(v[0] for v in values),3),'minutes',round(statistics.mean(v[1] for v in values),1))
