"""Summarise first-post booking and order outcomes from indexed base dev runs."""
import glob, gzip, json, statistics, collections, sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[2]))
from pathlib import Path
from dispatch.context import Context

world_map=json.loads(Path("/home/agent/.t3/projects/bahn/data/map.json").read_text())

def read(p):
    with gzip.open(p, 'rt') as f: return json.load(f)
def lines(p):
    with gzip.open(p, 'rt') as f: return [json.loads(x) for x in f]
rows=[]
seen=set()
for p in sorted(glob.glob('/home/agent/.t3/projects/bahn/data/runs/*')):
    try:
        meta=json.loads(Path(p,'result.json').read_text())
        if meta['label']!='base' or meta['seed'] not in [f'dev-{i:02}' for i in range(1,11)] or meta['seed'] in seen: continue
        seen.add(meta['seed'])
        req={x['request']['id']:x['request'] for x in read(p+'/reveal.json.gz')['requests']}
        orders={x['id']:x for x in read(p+'/snapshot.json.gz')['orders']}
        drivers=read(p+'/roster.json.gz')
        roster=collections.Counter(x['homePlaceId'] for x in drivers)
        ctx=Context.build(8, world_map, drivers)
        posts={}
        for x in lines(p+'/actions.jsonl.gz'):
            a=x['action']; result=x['result']
            if a['type']=='post' and result.get('ok'):
                oid=a['stops'][0]['orderId']
                if oid not in posts: posts[oid]=(result['id'],x['at'])
        books={}
        paid=collections.Counter()
        for e in lines(p+'/events.jsonl.gz'):
            if e['kind']=='gig_booked': books.setdefault(e['gigId'],e)
            if e['kind']=='ledger' and e['line']['kind']=='driver_fee' and e['line'].get('orderId'): paid[e['line']['orderId']] += -e['line']['cents']
        for oid,(gid,at) in posts.items():
            if oid not in orders or oid not in req: continue
            o=orders[oid]; q=req[oid]; leg=q['legs'][0]; b=books.get(gid)
            rows.append(dict(paidratio=paid[oid]/q['referenceFeeCents'] if paid[oid] else None, book=bool(b),ratio=b['feeCents']/q['referenceFeeCents'] if b else None,wait=b['at']-at if b else None,ontime=all(t is not None and t<=o['deadline'] for t in o['deliveredAt']),home=roster[leg['pickup']['placeId']],dest=roster[leg['delivery']['placeId']],private=any(x['pickup']['privateAddress'] or x['delivery']['privateAddress'] for x in q['legs']),trade=len(q['legs'])>1, km=ctx.km(leg['pickup']['placeId'], leg['delivery']['placeId']), near=sum(n for place,n in roster.items() if ctx.straight_km(leg['pickup']['placeId'],place)<=30), day=at//1440,hour=(at%1440)//60,slack=o['lastPickupAt']-at))
    except FileNotFoundError: continue
print('first posts',len(rows))
def show(name, select):
 r=[x for x in rows if select(x)]; b=[x for x in r if x['book']]
 if r: print(name, 'n',len(r),'book%',round(100*len(b)/len(r),1),'on-time%',round(100*sum(x['ontime'] for x in r)/len(r),1),'median ratio',round(statistics.median(x['ratio'] for x in b),2) if b else '-', 'median wait',statistics.median(x['wait'] for x in b) if b else '-')
show('all',lambda x:True)
for k,fn in [('home 0',lambda x:x['home']==0),('home 1-9',lambda x:0<x['home']<10),('home 10+',lambda x:x['home']>=10),('dest 0',lambda x:x['dest']==0),('dest 10+',lambda x:x['dest']>=10),('private',lambda x:x['private']),('nonprivate',lambda x:not x['private']),('trade',lambda x:x['trade']),('single',lambda x:not x['trade']),('slack <3h',lambda x:x['slack']<180),('slack 3-12h',lambda x:180<=x['slack']<720),('slack 12h+',lambda x:x['slack']>=720)]: show(k,fn)
for d in range(5): show('day '+str(d),lambda x:x['day']==d)
for lo,hi in [(0,9),(9,12),(12,15),(15,24)]: show(f'hour {lo}-{hi}',lambda x:lo<=x['hour']<hi)

for lo,hi in [(0,50),(50,150),(150,300),(300,100000)]: show(f'km {lo}-{hi}',lambda x:lo<=x['km']<hi)
for lo,hi in [(0,1),(1,10),(10,50),(50,100000)]: show(f'near {lo}-{hi}',lambda x:lo<=x['near']<hi)

paid=[x['paidratio'] for x in rows if x['paidratio'] is not None]
print('paid ratios',len(paid), 'median',round(statistics.median(paid),2),'mean',round(statistics.mean(paid),2))
