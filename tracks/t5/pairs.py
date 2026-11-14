"""Does one gig with two cars cost less than two gigs with one car each?

Plays a week with the mainline. When an order is won that fits before or after an open order
(the second pickup is at most `--dead` minutes from the first delivery), copies of the world
find the lowest flat fee that books within 3 hours: for each car alone, and for both in one gig.
The parent world is not changed.
"""
import argparse, json, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from dispatch.context import Context
from dispatch.desk import Desk, DAY, HOUR
from dispatch.policies import main
from harness import config, slots
from harness.play import world_map

p = argparse.ArgumentParser()
p.add_argument('--seed', required=True)
p.add_argument('--sample', type=int, default=14)
p.add_argument('--dead', type=int, default=30)
p.add_argument('--every', type=int, default=2)
a = p.parse_args()
c = config.client(); start = time.monotonic()
out = Path('tracks/t5') / (a.seed + '-pairs.jsonl')
HORIZON, LOW, HIGH, STEPS = 3 * HOUR, 0.3, 2.3, 5


def trial(world, before, post, cents, end):
    """True when a gig posted now at the flat fee `cents` has a driver at `end`."""
    with slots.fork(world) as copy:
        action = {**post, 'schedule': [{'at': now, 'feeCents': max(1, round(cents))}]}
        step = copy.advance(to=end, actions=before + [action])
        result = step['results'][-1]
        if not result['ok']:
            return {'error': result.get('reason')}
        gid = result['id']; booked = False
        for e in step['events']:
            if e.get('gigId') == gid:
                if e['kind'] == 'gig_booked': booked = True
                if e['kind'] in ('gig_dropped', 'no_show'): booked = False
        return {'kept': booked}


def lowest(world, before, post, typical, end):
    """The lowest fee, in typical fees, that books by `end`; None when even the highest does not."""
    top = trial(world, before, post, HIGH * typical, end)
    if top.get('error'): return {'error': top['error']}
    if not top['kept']: return None
    lo, hi = LOW, HIGH
    for _ in range(STEPS):
        mid = (lo + hi) / 2
        if trial(world, before, post, mid * typical, end).get('kept'): hi = mid
        else: lo = mid
    return round(hi, 3)


def fits(first, second, now):
    """True when one driver can plausibly do `first` then `second` inside both orders' windows, starting after the horizon."""
    x, y = first['legs'][0], second['legs'][0]
    drive_x = ctx.minutes(x['pickup']['placeId'], x['delivery']['placeId'])
    drive_y = ctx.minutes(y['pickup']['placeId'], y['delivery']['placeId'])
    dead = ctx.minutes(x['delivery']['placeId'], y['pickup']['placeId']) if x['delivery']['placeId'] != y['pickup']['placeId'] else 0
    if dead > a.dead or drive_x + dead + drive_y > 12 * HOUR: return None
    at = max(now + HORIZON + HOUR, x['pickup']['window']['from'])
    if at > min(x['pickup']['window']['to'], first['lastPickupAt']): return None
    at = max(at + drive_x + dead, y['pickup']['window']['from'])
    if at > min(y['pickup']['window']['to'], second['lastPickupAt']) or at + drive_y > y['delivery']['window']['to']: return None
    return dead


with slots.create(c, level=8, seed=a.seed) as world, out.open('w') as f:
    ctx = Context.build(8, world_map(c), world.roster())
    desk = Desk(world, ctx, main.build(ctx), 0); seen = 0; scanned = 0; used = set()
    while desk.now < 7 * DAY:
        slots.wait_while_paused()
        stop = min(7 * DAY, (desk.now // DAY + 1) * DAY, desk.next_timer() or 7 * DAY)
        actions, desk.outbox = desk.outbox, []
        step = world.advance(until=desk.wake_on, max=stop, actions=actions)
        desk.read_results(actions, step['results']); desk.now = step['now']
        for event in step['events']:
            desk.handle(event)
            if event['kind'] != 'order_won' or scanned >= a.sample: continue
            new = event['order']; now = desk.now
            posts = [x for x in desk.outbox if x['type'] == 'post' and x['stops'][0]['orderId'] == new['id']]
            if len(new['legs']) != 1 or not posts or not 7 * HOUR <= now % DAY <= 16 * HOUR: continue
            best = None
            for other in desk.orders.values():
                gigs = desk.gigs_of(other['id'])
                if other['id'] == new['id'] or other['id'] in used or len(other['legs']) != 1 or len(gigs) != 1 or gigs[0] in desk.booked: continue
                for first, second in ((new, other), (other, new)):
                    dead = fits(first, second, now)
                    if dead is not None and (best is None or dead < best[0]): best = (dead, first, second, other, gigs[0])
            if best is None: continue
            seen += 1
            if (seen - 1) % a.every: continue
            dead, first, second, other, gig = best; used.add(other['id'])
            new_post, old_post = posts[0], desk.posts[gig]
            order_posts = {new['id']: new_post, other['id']: old_post}
            typical = {o['id']: desk.requests[o['id']]['referenceFeeCents'] for o in (new, other)}
            both = {'type': 'post', 'stops': order_posts[first['id']]['stops'] + order_posts[second['id']]['stops'],
                    'audience': {key: new_post['audience'].get(key) or old_post['audience'].get(key) for key in set(new_post['audience']) | set(old_post['audience'])}}
            end = now + HORIZON; withdraw = [{'type': 'withdraw', 'gigId': gig}]
            fx, fy = first['legs'][0], second['legs'][0]
            row = dict(seed=a.seed, minute=now, first=first['id'], second=second['id'], new=new['id'], dead=dead,
                       route=[ctx.places[x]['name'] for x in (fx['pickup']['placeId'], fx['delivery']['placeId'], fy['pickup']['placeId'], fy['delivery']['placeId'])],
                       km=[ctx.km(fx['pickup']['placeId'], fx['delivery']['placeId']), ctx.km(fy['pickup']['placeId'], fy['delivery']['placeId'])],
                       home_km=ctx.km(fy['delivery']['placeId'], fx['pickup']['placeId']) if fy['delivery']['placeId'] != fx['pickup']['placeId'] else 0,
                       typical=[typical[first['id']], typical[second['id']]], audience=both['audience'])
            row['new_alone'] = lowest(world, [], new_post, typical[new['id']], end)
            row['old_alone'] = lowest(world, withdraw, old_post, typical[other['id']], end)
            row['both'] = lowest(world, withdraw, both, sum(typical.values()), end)
            f.write(json.dumps(row) + '\n'); f.flush(); scanned += 1
            print(json.dumps(row), flush=True)
        desk.tick()
    print('scanned', scanned, 'requests', c.requests, 'seconds', round(time.monotonic() - start, 1), flush=True)
