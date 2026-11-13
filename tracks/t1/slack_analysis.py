"""Describe observed delivery outcomes by note-adjusted slack and drive time."""
import gzip, json, os
from collections import defaultdict
from dispatch.context import Context
from dispatch.notes import ReadNotes

root = '/home/agent/.t3/projects/bahn/data'
ctx = Context.build(8, json.load(open(root + '/map.json')), [])
notes = ReadNotes()
groups = defaultdict(lambda: [0, 0])
for row in map(json.loads, open(root + '/runs.jsonl')):
    if row['label'] != 't1-limit15-later-price16-fee11' or not row['seed'].startswith('dev-'): continue
    notes = ReadNotes()
    folder = root + '/runs/' + os.path.basename(row['folder'])
    requests = {}
    with gzip.open(folder + '/events.jsonl.gz', 'rt') as f:
        for line in f:
            event = json.loads(line)
            if event['kind'] == 'price_request': requests[event['request']['id']] = event['request']
    with gzip.open(folder + '/snapshot.json.gz', 'rt') as f: orders = json.load(f)['orders']
    for order in orders:
        if order['status'] == 'cancelled' or order['id'] not in requests: continue
        req = requests[order['id']]; leg = req['legs'][0]
        drive = ctx.minutes(leg['pickup']['placeId'], leg['delivery']['placeId'])
        slack = notes.latest_delivery(req, order['deadline']) - max(req['respondBy'], notes.earliest_pickup(req)) - drive
        private = any(l[s]['privateAddress'] for l in req['legs'] for s in ('pickup','delivery'))
        good = all(t is not None and t <= order['deadline'] for t in order['deliveredAt'])
        for key in [('slack hours', next((str(n) for n in (12,24,48,72) if slack < n*60), '72+')), ('drive hours', next((str(n) for n in (2,4,6) if drive < n*60), '6+')), ('private', str(private)), ('private slack', str(private) + ':' + next((str(n) for n in (24,48,72) if slack < n*60), '72+'))]:
            groups[key][0] += good; groups[key][1] += 1
for k,(good,n) in groups.items(): print(k, good, n, round(100*good/n,1))
