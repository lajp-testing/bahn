"""Measure direct offers in slot-managed copies while main plays the parent."""
import argparse, json, sys, time
from pathlib import Path
from collections import defaultdict
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from dispatch.context import Context
from dispatch.desk import Desk, DAY
from dispatch.policies import main
from harness import config, slots
from harness.play import world_map

p = argparse.ArgumentParser()
p.add_argument('--seed', required=True)
p.add_argument('--sample', type=int, default=15)
p.add_argument('--rule', choices=['pickup', 'delivery', 'position', 'viewed'])
a = p.parse_args()
c = config.client(); start = time.monotonic()
out = Path('tracks/t5') / (a.seed + ('-fees' if a.rule else '-rules') + '.jsonl')
with slots.create(c, level=8, seed=a.seed, track='t5') as world, out.open('w') as f:
    ctx = Context.build(8, world_map(c), world.roster())
    desk = Desk(world, ctx, main.build(ctx, slack=1440, private=True, queue_price=True, win_price=True), 0)
    due = {}; viewed = defaultdict(list); booked = {}; recent = {}; candidates = {}; count = 0
    def write(row):
        f.write(json.dumps(row, sort_keys=True) + '\n'); f.flush()
    while desk.now < 7 * DAY:
        slots.wait_while_paused()
        stop = min(7*DAY, (desk.now//DAY+1)*DAY, desk.next_timer() or 7*DAY, min(due.values(), default=7*DAY))
        actions, desk.outbox = desk.outbox, []
        sent = desk.now
        step = world.advance(until=desk.wake_on, max=stop, actions=actions)
        desk.read_results(actions, step['results']); desk.now = step['now']
        for action, result in zip(actions, step['results']):
            if action['type'] == 'post' and result['ok']:
                due[result['id']] = sent + 30
        for e in step['events']:
            if e['kind'] == 'gig_viewed': viewed[e['gigId']].append(e['driverId'])
            if e['kind'] == 'gig_booked':
                booked[e['gigId']] = e
                if e['gigId'] in candidates: write({'type':'parent_booking','seed':a.seed, **e})
            if e['kind'] == 'delivered' and e['gigId'] in booked:
                recent[booked[e['gigId']]['driverId']] = (e['placeId'], e['at'])
            desk.handle(e)
        desk.tick()
        for gid in [g for g,t in due.items() if t <= desk.now]:
            del due[gid]
            if count >= a.sample or gid in booked or desk.now//DAY >= 5 or not 7*60 <= desk.now%DAY < 22*60+45: continue
            snap = world.snapshot(); gig = next((g for g in snap['gigs'] if g['id']==gid and g['status']=='open'), None)
            if not gig: continue
            post = desk.posts[gid]; oid = post['stops'][0]['orderId']; req = desk.requests[oid]
            leg = req['legs'][post['stops'][0]['leg']]; pickup = leg['pickup']['placeId']; delivery = leg['delivery']['placeId']
            typical = req['referenceFeeCents']; roster = ctx.roster
            distance = lambda x,y: 0 if x==y else ctx.straight_km(x,y)
            rules = {'pickup': sorted(roster,key=lambda d:(distance(d['homePlaceId'],pickup),d['id'])), 'delivery':sorted(roster,key=lambda d:(distance(d['homePlaceId'],delivery),d['id']))}
            positions = {driver: place for driver, (place, at) in recent.items() if desk.now - at <= 120}
            positions.update({x['driverId']:x['placeId'] for x in snap['driverPositions']})
            for other in snap['gigs']:
                if other['status'] in ('booked', 'working') and other.get('driverId') and other['stops']:
                    last = other['stops'][-1]; order = desk.orders.get(last['orderId'])
                    if order and last['kind'] == 'delivery':
                        positions[other['driverId']] = order['legs'][last['leg']]['delivery']['placeId']
            rules['position'] = sorted((d for d in roster if d['id'] in positions and distance(positions[d['id']],pickup)<=30),key=lambda d:(distance(positions[d['id']],pickup),d['id']))
            ids = list(dict.fromkeys(viewed[gid])); lookup = {d['id']:d for d in roster}
            rules['viewed'] = [lookup[i] for i in ids if i in lookup]
            candidates[gid] = desk.now; count += 1
            write({'type':'sample','seed':a.seed,'gig':gid,'at':desk.now,'typical':typical,'pickup':pickup,'delivery':delivery})
            for rule in ([a.rule] if a.rule else rules):
                drivers = rules[rule][:3]
                for mult in ([0.5,0.7,0.9] if a.rule else [1.0]):
                    if not drivers:
                        write({'type':'empty','seed':a.seed,'gig':gid,'rule':rule,'multiple':mult}); continue
                    with slots.fork(world, track='orch') as copy:
                        offers = [{'type':'offer','gigId':gid,'driverId':d['id'],'feeCents':max(1,round(typical*mult))} for d in drivers]
                        result = copy.advance(to=desk.now+15, actions=offers)
                        answers = {e['driverId']:e['answer'] for e in result['events'] if e['kind']=='offer_answered' and e['gigId']==gid}
                        for offer, res in zip(offers, result['results']):
                            write({'type':'offer','seed':a.seed,'gig':gid,'rule':rule,'multiple':mult,'driver':offer['driverId'],'feeCents':offer['feeCents'],'answer':answers.get(offer['driverId'], 'missing' if res['ok'] else 'refused'),'result':res})
            print('sample', a.seed, count, gid, 'requests', c.requests, 'seconds', round(time.monotonic()-start,1), flush=True)
    print('finished', count, 'requests', c.requests, 'seconds', round(time.monotonic()-start,1), flush=True)
