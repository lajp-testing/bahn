"""Fork sampled single-car wins; measure flat-fee outcomes without altering the parent."""
import argparse, json, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from dispatch.context import Context
from dispatch.desk import Desk, DAY
from dispatch.policies import main
from harness import config, slots
from harness.play import world_map

p = argparse.ArgumentParser()
p.add_argument('--seed', required=True)
p.add_argument('--sample', type=int, default=12)
p.add_argument('--check', action='store_true')
a = p.parse_args()
c = config.client(); start = time.monotonic()
out = Path('tracks/t3') / (a.seed + ('-check' if a.check else '-scan') + '.jsonl')

def trial(world, post, fee, end):
    with slots.fork(world) as copy:
        action = {**post, 'schedule': [{'at': now, 'feeCents': max(1, round(fee * typical))}]}
        step = copy.advance(to=end, actions=[action])
        result = step['results'][0]
        if not result['ok']:
            return {'error': result.get('reason')}
        gid = result['id']; booked = False; drops = 0
        for e in step['events']:
            if e.get('gigId') == gid:
                if e['kind'] == 'gig_booked': booked = True
                if e['kind'] in ('gig_dropped', 'no_show'): booked = False; drops += 1
        return {'kept': booked, 'drops': drops}

with slots.create(c, level=8, seed=a.seed) as world, out.open('w') as f:
    ctx = Context.build(8, world_map(c), world.roster())
    desk = Desk(world, ctx, main.build(ctx), 0); seen = 0; scanned = 0
    while desk.now < 7 * DAY:
        slots.wait_while_paused()
        stop = min(7 * DAY, (desk.now // DAY + 1) * DAY, desk.next_timer() or 7 * DAY)
        actions, desk.outbox = desk.outbox, []
        step = world.advance(until=desk.wake_on, max=stop, actions=actions)
        desk.read_results(actions, step['results']); desk.now = step['now']
        for event in step['events']:
            desk.handle(event)
            if event['kind'] != 'order_won': continue
            order = event['order']; req = desk.requests.get(order['id'])
            posts = [x for x in desk.outbox if x['type'] == 'post' and x['stops'][0]['orderId'] == order['id']]
            if not req or not posts: continue
            seen += 1
            if len(order['legs']) == 1 and (scanned >= a.sample or (not a.check and (seen - 1) % 3)): continue
            now = desk.now; post = posts[0]; typical = req['referenceFeeCents'] * sum(s['kind'] == 'pickup' for s in post['stops']) / len(req['legs'])
            leg = req['legs'][0]; pickup = leg['pickup']['placeId']; delivery = leg['delivery']['placeId']
            ends = {'2h': min(now + 120, 7*DAY), 'warning': min(max(now + 1, order['lastPickupAt'] - 180), 7*DAY)}
            row = dict(seed=a.seed, id=order['id'], minute=now, slack=order['lastPickupAt']-now, option=order['option'], typical=typical, pickup=ctx.places[pickup]['name'], delivery=ctx.places[delivery]['name'], km=ctx.km(pickup, delivery), pickup_near=sum(ctx.straight_km(pickup,d['homePlaceId']) <= 30 for d in ctx.roster), delivery_near=sum(ctx.straight_km(delivery,d['homePlaceId']) <= 30 for d in ctx.roster), private=any(x['pickup']['privateAddress'] or x['delivery']['privateAddress'] for x in req['legs']), trade=len(req['legs']) > 1, outcomes={})
            for name, end in ends.items():
                if a.check:
                    row['outcomes'][name] = [(v, trial(world, post, v, end)) for v in (0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.5, 2.0, 3.0)]
                else:
                    high = trial(world, post, 3, end)
                    if high.get('kept'):
                        lo, hi = 0., 3.
                        for _ in range(6):
                            mid = (lo+hi)/2; result = trial(world, post, mid, end)
                            if result.get('error'): raise RuntimeError(result)
                            if result['kept']: hi = mid
                            else: lo = mid
                        row['outcomes'][name] = hi
                    else: row['outcomes'][name] = None
            f.write(json.dumps(row)+'\n'); f.flush(); scanned += 1
            print(json.dumps(row), flush=True)
        desk.tick()
    print('scanned', scanned, 'requests', c.requests, 'seconds', round(time.monotonic()-start,1), flush=True)
