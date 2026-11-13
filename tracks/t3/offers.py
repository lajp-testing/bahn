"""Compare direct offers and the app in matched world copies."""
import argparse, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from dispatch.context import Context
from dispatch.desk import Desk, DAY
from dispatch.policies import main
from harness import config, slots
from harness.play import world_map

p = argparse.ArgumentParser(); p.add_argument('--seed', required=True); p.add_argument('--sample', type=int, default=30); a = p.parse_args()
c = config.client(); out = Path('tracks/t3') / (a.seed + '-offers.jsonl')
with slots.create(c, level=8, seed=a.seed) as world, out.open('w') as f:
    ctx = Context.build(8, world_map(c), world.roster()); desk = Desk(world, ctx, main.build(ctx), 0); seen = scanned = 0
    while desk.now < 7*DAY:
        slots.wait_while_paused()
        stop = min(7*DAY, (desk.now//DAY+1)*DAY, desk.next_timer() or 7*DAY)
        actions, desk.outbox = desk.outbox, []
        step = world.advance(until=desk.wake_on, max=stop, actions=actions)
        desk.read_results(actions, step['results']); desk.now = step['now']
        for event in step['events']:
            desk.handle(event)
            if event['kind'] != 'order_won': continue
            order = event['order']; req = desk.requests.get(order['id'])
            posts = [x for x in desk.outbox if x['type']=='post' and x['stops'][0]['orderId']==order['id']]
            if not req or len(req['legs']) != 1 or not posts or not 7*60 <= desk.now%DAY < 23*60: continue
            seen += 1
            if scanned >= a.sample or (seen-1)%3: continue
            post=posts[0]; now=desk.now; pickup=req['legs'][0]['pickup']['placeId']; fee=desk.parts.fees.estimate(req,desk)
            near=sorted(ctx.roster,key=lambda d:ctx.straight_km(pickup,d['homePlaceId']))[:3]
            outcomes={}
            for variant in ('app','offer'):
                with slots.fork(world) as copy:
                    first=copy.advance(to=now+1,actions=[{**post,'schedule':[{'at':now,'feeCents':fee}]}])
                    result=first['results'][0]
                    if not result.get('ok'): outcomes[variant]={'error':result}; continue
                    gid=result['id']; ev=first['events']; offers=[]
                    if variant=='offer': offers=[{'type':'offer','gigId':gid,'driverId':d['id'],'feeCents':fee} for d in near]
                    second=copy.advance(to=now+11,actions=offers); ev += second['events']
                    outcomes[variant]={'booking':any(e['kind']=='gig_booked' and e['gigId']==gid for e in ev), 'answers':[e['answer'] for e in ev if e['kind']=='offer_answered' and e['gigId']==gid], 'offer_results':second['results']}
            row={'seed':a.seed,'id':order['id'],'minute':now,'fee':fee,'typical':req['referenceFeeCents'],'outcomes':outcomes}
            f.write(json.dumps(row)+'\n'); f.flush(); print(json.dumps(row),flush=True); scanned += 1
        desk.tick()
