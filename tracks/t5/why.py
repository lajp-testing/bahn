"""Why does a newly won car not join an open gig? Plays one week with bundles and counts the reasons."""
import argparse, json, sys
from collections import Counter
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from dispatch.bundles import Bundles, orders_in
from dispatch.context import Context
from dispatch.desk import Desk, DAY
from dispatch.policies import main
from harness import config, slots
from harness.play import world_map

p = argparse.ArgumentParser(); p.add_argument('--seed', required=True); p.add_argument('--cars', type=int, default=3); a = p.parse_args()
why = Counter()


class Asking(Bundles):
    def join(self, order, stops, audience, desk):
        found = super().join(order, stops, audience, desk)
        if found: why['joined'] += 1; return found
        if not self.plain(order, desk): why['not plain: private, trade-in or urgent'] += 1; return None
        open_gigs = [(g, act) for g, act in desk.posts.items() if g not in desk.booked and all(m in desk.orders and desk.gigs_of(m) == [g] for m in orders_in(act['stops']))]
        if not open_gigs: why['no open gig'] += 1; return None
        usable = [(g, act) for g, act in open_gigs if len(orders_in(act['stops'])) < self.cars and all(self.plain(desk.orders[m], desk) for m in orders_in(act['stops']))]
        if not usable: why['open gigs are full or not plain'] += 1; return None
        loose = Bundles(cars=self.cars, dead=10 ** 6, slack=0, drive=10 ** 6)
        best = 'no start reaches every stop'
        for g, act in usable:
            for joined in (act['stops'] + stops, stops + act['stops']):
                if loose.route(joined, desk) is None: continue
                near = Bundles(cars=self.cars, dead=self.dead, slack=0, drive=10 ** 6).route(joined, desk)
                if near is None: best = max(best, 'next pickup too far', key=['no start reaches every stop', 'next pickup too far', 'over 11 hours of driving', 'last start too soon'].index); continue
                if self.route(joined, desk) is None: best = max(best, 'over 11 hours of driving', key=['no start reaches every stop', 'next pickup too far', 'over 11 hours of driving', 'last start too soon'].index); continue
                best = 'last start too soon'
        why[best] += 1
        return None


with slots.create(config.client(), level=8, seed=a.seed) as world:
    ctx = Context.build(8, world_map(config.client()), world.roster())
    parts = main.build(ctx, fee_model=2, bundle=a.cars)
    parts.bundles = Asking(cars=a.cars)
    desk = Desk(world, ctx, parts, 0)
    while desk.now < 7 * DAY:
        stop = min(7 * DAY, (desk.now // DAY + 1) * DAY, desk.next_timer() or 7 * DAY)
        actions, desk.outbox = desk.outbox, []
        step = world.advance(until=desk.wake_on, max=stop, actions=actions)
        desk.read_results(actions, step['results']); desk.now = step['now']
        for event in step['events']:
            desk.handle(event)
        desk.tick()
    print(json.dumps(dict(why.most_common()), indent=1))
