"""Loose town/window upper bound and observed same-driver sequences in saved weeks."""
import collections, gzip, json, pathlib, statistics
P = pathlib.Path('/home/agent/.t3/projects/bahn/data')
rows = [json.loads(x) for x in (P/'runs.jsonl').read_text().splitlines()]
rows = [r for r in rows if r['label']=='main-c-measured-m16-nopriv' and r['seed'].startswith('dev-')]
byseed = {r['seed']: r for r in rows}
for seed, r in sorted(byseed.items()):
 d=P/'runs'/pathlib.Path(r['folder']).name
 def read(name):
  with gzip.open(d/name,'rt') as f: return json.load(f)
 rev=read('reveal.json.gz'); snap=read('snapshot.json.gz')
 with gzip.open(d/'events.jsonl.gz','rt') as f: events=[json.loads(x) for x in f]
 def candidates(items):
  pairs=[]
  for a in items:
   for b in items:
    if a['id']==b['id'] or len(a['legs'])!=1 or len(b['legs'])!=1: continue
    x,y=a['legs'][0],b['legs'][0]
    if x['delivery']['placeId']!=y['pickup']['placeId']: continue
    # optimistic: zero driving time; windows only, no opening hours
    t=max(x['pickup']['window']['from'], x['delivery']['window']['from'])
    u=max(t,y['pickup']['window']['from'],y['delivery']['window']['from'])
    if t<=min(x['pickup']['window']['to'],x['delivery']['window']['to'],a['deadline']) and u<=min(y['pickup']['window']['to'],y['delivery']['window']['to'],b['deadline']): pairs.append((a['id'],b['id']))
  return pairs
 req=[]
 for x in rev['requests']:
  a=dict(x['request']); a['deadline']=max(o['deadline'] for o in a['options']); req.append(a)
 orders=[o for o in snap['orders'] if o['status']!='cancelled']; pairs=candidates(orders)
 starts={e['gigId']:e['at'] for e in events if e['kind']=='gig_started'}
 gigs=[g for g in snap['gigs'] if g['status']=='done' and g['id'] in starts and g.get('driverId') and len({s['orderId'] for s in g['stops']})==1]
 groups=collections.defaultdict(list)
 for g in gigs: groups[(g['driverId'],starts[g['id']]//1440)].append(g)
 second=[]; first=[]; chain=0
 od={o['id']:o for o in orders}
 for gs in groups.values():
  gs.sort(key=lambda g:starts[g['id']]); first.append(gs[0]['feeCents'])
  for a,b in zip(gs,gs[1:]):
   second.append(b['feeCents']); ai=a['stops'][0]['orderId']; bi=b['stops'][0]['orderId']
   if ai in od and bi in od and len(od[ai]['legs'])==len(od[bi]['legs'])==1 and od[ai]['legs'][0]['delivery']['placeId']==od[bi]['legs'][0]['pickup']['placeId']: chain+=1
 rp=candidates(req)
 print(json.dumps(dict(seed=seed,requests=len(req),request_pairs_upper=len(rp),requests_with_pair=len(set(i for p in rp for i in p)),orders=len(orders),won_pairs_upper=len(pairs),won_with_pair=len(set(i for p in pairs for i in p)),driver_day_first_n=len(first),driver_day_first_mean=round(statistics.mean(first)) if first else None,subsequent_n=len(second),subsequent_mean=round(statistics.mean(second)) if second else None,adjacent_same_town=chain,marginCents=r['marginCents'],onTimeShare=r['onTimeShare'])))
