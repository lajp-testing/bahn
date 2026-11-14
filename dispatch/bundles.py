"""The bundles: which cars share a gig.

One driver who moves two cars in a row needs one trip to the first car and one trip home, where two
drivers need two of each. In copies of the same world a gig with two cars found a driver for about
14% less than the two cars posted alone, and it found one for cars that no driver took alone
(tracks/t5/FINDINGS.md). A bundle also uses one of the week's few drivers for two cars.

A newly won car joins an open gig when one driver can do all stops in a row: the next pickup is near
the last delivery, and a start exists that reaches every stop inside its window and opening hours.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

from .parts import Part

if TYPE_CHECKING:
    from .desk import Desk

HOUR, DAY = 60, 24 * 60


class Bundles(Part):
    def __init__(self, cars: int = 2, dead: int = 30, slack: int = 6 * HOUR, split: int = 4 * HOUR, discount: float = 0.85, drive: int = 11 * HOUR, private: bool = False, patience: int = 0, room: int = 0, plan: int = 0, reach: int = 60, hold: int = 0, hold_slack: int = 12 * HOUR):
        self.cars = cars  # the most cars in one gig
        self.dead = dead  # the longest drive without a car between two cars, in minutes
        self.slack = slack  # a bundle is made only when its last possible start is at least this far away
        self.split = split  # a bundle without a driver this long before its last start goes back to one gig per car
        self.discount = discount  # a bundle's fee: this share of the sum of its cars' fees
        self.drive = drive  # the longest drive from first pickup to last delivery; the world's limit is 12 hours
        self.private = private  # whether a car at a private address may join a bundle
        self.patience = patience  # a bundle without a driver after this many minutes of the drivers' day goes back to one gig per car; 0: no limit
        self.room = room  # a bundle is made only when a driver can start it over at least this many minutes
        self.plan = plan  # every this many minutes, the open cars are rebuilt into chains (`chains`); 0: never
        self.reach = reach  # the longest drive without a car between two cars of a planned chain, in minutes
        self.hold = hold  # a newly won car that finds no gig waits this many minutes for a partner before it goes alone; 0: never
        self.hold_slack = hold_slack  # it waits only while a driver can still start it this many minutes from now
        self.planned_at = -1

    def plain(self, order: dict[str, Any], desk: "Desk") -> bool:
        """A car that may share a gig: one car, no deadline warning yet, and no private address."""
        legs = order["legs"]
        return len(legs) == 1 and order["id"] not in desk.urgent and (self.private or not (legs[0]["pickup"]["privateAddress"] or legs[0]["delivery"]["privateAddress"]))

    def join(self, order: dict[str, Any], stops: list[dict[str, Any]], audience: dict[str, bool], desk: "Desk") -> Optional[tuple[Any, list[dict[str, Any]], dict[str, bool]]]:
        """The gig that the order's car joins, with the joined stops and audience; None when it goes alone."""
        if not self.plain(order, desk):
            return None
        return self.search(order, stops, audience, desk, desk.orders)

    def fits(self, request: dict[str, Any], desk: "Desk") -> bool:
        """Whether the request's car, once won, could join a gig that is open now."""
        legs = request["legs"]
        if len(legs) != 1 or not (self.private or not (legs[0]["pickup"]["privateAddress"] or legs[0]["delivery"]["privateAddress"])):
            return False
        order = {"id": request["id"], "legs": legs, "deadline": max(option["deadline"] for option in request["options"])}
        stops = [{"orderId": order["id"], "leg": 0, "kind": kind} for kind in ("pickup", "delivery")]
        return self.search(order, stops, {}, desk, desk.orders | {order["id"]: order}) is not None

    def search(self, order: dict[str, Any], stops: list[dict[str, Any]], audience: dict[str, bool], desk: "Desk", orders: dict[str, Any]) -> Optional[tuple[Any, list[dict[str, Any]], dict[str, bool]]]:
        """The best gig to join: one that is open in the app (its id), or one that the desk has decided to post
        and not sent yet (the post itself), as when a dealer's cars are won in the same minute."""
        best: Optional[tuple[tuple[int, int], Any, list[dict[str, Any]], dict[str, bool]]] = None
        open_gigs = [(gig_id, action, [gig_id]) for gig_id, action in desk.posts.items() if gig_id not in desk.booked]
        unsent = [(action, action, []) for action in desk.outbox if action["type"] == "post"]
        unsent += [(action, action, []) for action in desk.held.values()]  # cars held back for a partner
        for gig_id, action, carried_by in open_gigs + unsent:
            members = orders_in(action["stops"])
            if len(members) >= self.cars or order["id"] in members:
                continue
            if not all(member in desk.orders and desk.gigs_of(member) == carried_by and self.plain(desk.orders[member], desk) for member in members):
                continue
            for joined in (action["stops"] + stops, stops + action["stops"]):
                found = self.route(joined, desk, orders)
                if found is None or found[1] - desk.now < self.slack or found[2] < self.room:
                    continue
                score = (found[0], drive(joined[-1], joined[0], desk, orders))
                if best is None or score < best[0]:
                    best = (score, gig_id, joined, {key: audience[key] or action["audience"][key] for key in audience})
        return best[1:] if best else None

    def holds(self, order: dict[str, Any], stops: list[dict[str, Any]], desk: "Desk") -> bool:
        """Whether a newly won car that found no gig waits for a partner: only a plain car with time to spare."""
        if not self.hold or not self.plain(order, desk):
            return False
        found = self.route(stops, desk)
        return found is not None and found[1] - desk.now >= self.hold_slack + self.hold

    def tick(self, desk: "Desk") -> None:
        for order_id, action in list(desk.held.items()):  # the hold ended without a partner: the car goes alone
            if desk.now >= action["until"]:
                del desk.held[order_id]
                if order_id in desk.orders and not desk.gigs_of(order_id):
                    desk.alone(desk.orders[order_id])
        if self.plan and desk.now >= self.planned_at + self.plan:
            self.planned_at = desk.now - desk.now % self.plan
            desk.wake(self.planned_at + self.plan)
            self.chains(desk)

    def chains(self, desk: "Desk") -> None:
        """The chain planner: one driver's day holds four times the work we give it, so every `plan` minutes the
        cars whose gig no driver holds are rebuilt greedily into chains that one driver can do, earliest last
        pickup first, each next car the one nearest to the chain's last delivery. Changed chains are posted
        again as one gig; a gig whose cars stay together is left alone."""
        desk.send()
        gigs: dict[str, list[str]] = {}  # open gig id -> its cars, for the gigs that the planner may rebuild
        for gig_id, action in desk.posts.items():
            members = orders_in(action["stops"])
            if (gig_id in desk.booked or gig_id in desk.urgent_gigs
                    or not all(m in desk.orders and desk.gigs_of(m) == [gig_id] and self.plain(desk.orders[m], desk) and m not in desk.late_posted for m in members)):
                continue
            gigs[gig_id] = members
        cars = {m: [s for s in desk.posts[g]["stops"] if s["orderId"] == m] for g, members in gigs.items() for m in members}
        audience = {m: desk.posts[g]["audience"] for g, members in gigs.items() for m in members}
        left = sorted(cars, key=lambda m: desk.orders[m]["lastPickupAt"])
        chains: list[list[str]] = []
        while left:
            chain = [left.pop(0)]
            stops = list(cars[chain[0]])
            while len(chain) < self.cars:
                best = None
                for m in left:
                    gap = drive(stops[-1], cars[m][0], desk, desk.orders)
                    if gap > self.reach or (best and gap >= best[0]):
                        continue
                    found = self.route(stops + cars[m], desk, reach=self.reach)
                    if found and found[1] - desk.now >= self.slack and found[2] >= self.room:
                        best = (gap, m)
                if best is None:
                    break
                chain.append(best[1])
                left.remove(best[1])
                stops += cars[best[1]]
            chains.append(chain)
        old = {tuple(members): g for g, members in gigs.items()}
        changed = [chain for chain in chains if tuple(chain) not in old]
        if not changed:
            return
        for chain in changed:  # withdraw first, so that a car a driver booked meanwhile stays where it is
            for m in chain:
                gig_id = desk.leg_gigs.get(m, {}).get(0)
                if gig_id in gigs:
                    desk.outbox.append({"type": "withdraw", "gigId": gig_id})
                    desk.split_at.pop(gig_id, None)
                    for member in gigs.pop(gig_id):
                        desk.leg_gigs.pop(member, None)
        desk.send()
        for chain in changed:
            free = [m for m in chain if not desk.gigs_of(m)]
            stops = [s for m in free for s in cars[m]]
            if len(free) > 1 and self.route(stops, desk, reach=self.reach):
                look = {key: any(audience[m][key] for m in free) for key in audience[free[0]]}
                schedule = self.fees([desk.clock.get(m) or desk.fees_for(desk.orders[m], 1) for m in free], desk.now)
                desk.outbox.append({"type": "post", "stops": desk.cut(stops), "audience": look, "schedule": schedule})
            else:
                for m in free:
                    desk.alone(desk.orders[m])
        # cars of a withdrawn gig that no changed chain holds (its partner went elsewhere) go alone
        held = {m for chain in changed for m in chain}
        for m in cars:
            if m not in held and not desk.gigs_of(m) and not any(m in orders_in(a["stops"]) for a in desk.outbox if a["type"] == "post"):
                desk.alone(desk.orders[m])

    def route(self, stops: list[dict[str, Any]], desk: "Desk", orders: Optional[dict[str, Any]] = None, reach: Optional[int] = None) -> Optional[tuple[int, int, int]]:
        """The minutes driven without a car, the last minute a driver can start the first stop and reach every
        stop inside its window while its site is open, and for how many minutes such a start exists. None
        when the stops do not fit in one gig."""
        orders = desk.orders if orders is None else orders
        dead = total = 0
        for a, b in zip(stops, stops[1:]):
            minutes = drive(a, b, desk, orders)
            total += minutes
            if a["kind"] == "delivery":
                if minutes > (self.dead if reach is None else reach):
                    return None
                dead += minutes
        if total > self.drive:
            return None
        first = max(desk.now, window(stops[0], orders)["from"])
        last = min(window(stop, orders)["to"] for stop in stops)
        starts = [start for start in range(last - last % 15, first - 1, -15) if self.reaches(stops, start, desk, orders)]
        return (dead, starts[0], 15 * len(starts)) if starts else None

    def reaches(self, stops: list[dict[str, Any]], start: int, desk: "Desk", orders: dict[str, Any]) -> bool:
        at = start
        for i, stop in enumerate(stops):
            if i:
                at += drive(stops[i - 1], stop, desk, orders)
            span = window(stop, orders)
            if not (span["from"] <= at <= span["to"] and is_open(side(stop, orders)["hours"], at)):
                return False
            at += 30 * bool(stop.get("withPlates")) + 40 * bool(stop.get("withCharging"))
        return True

    def split_at(self, stops: list[dict[str, Any]], desk: "Desk") -> int:
        """When a bundle that still has no driver gives up: `split` before its last possible start, or
        after `patience` minutes of the drivers' day in the app. Now, when it no longer fits."""
        found = self.route(stops, desk)
        last = found[1] - self.split if found else desk.now
        fees = desk.parts.fees
        waited = (fees.after(desk.now, self.patience) if hasattr(fees, "after") else desk.now + self.patience) if self.patience else last
        return min(last, waited)

    def fees(self, schedules: list[list[dict[str, int]]], now: int) -> list[dict[str, int]]:
        """A bundle's fee schedule: at each minute, the sum of what its cars' own schedules pay then, less the discount."""
        times = sorted({max(now, step["at"]) for schedule in schedules for step in schedule})[:48]
        return [{"at": at, "feeCents": max(1, round(self.discount * sum(fee_at(schedule, at) for schedule in schedules)))} for at in times]


def orders_in(stops: list[Any]) -> list[str]:
    """The orders whose cars a list of stops carries, in the order of the stops."""
    return list(dict.fromkeys(stop["orderId"] for stop in stops))


def fee_at(schedule: list[dict[str, int]], at: int) -> int:
    """The fee that a schedule shows at a minute: its latest step that has started, or its first step."""
    started = [step["feeCents"] for step in schedule if step["at"] <= at]
    return started[-1] if started else schedule[0]["feeCents"]


def resume(schedule: list[dict[str, int]], now: int) -> list[dict[str, int]]:
    """A schedule taken up again at `now`: the fee it shows now, then its later steps."""
    return [{"at": now, "feeCents": fee_at(schedule, now)}] + [step for step in schedule if step["at"] > now]


def side(stop: dict[str, Any], orders: dict[str, Any]) -> dict[str, Any]:
    return orders[stop["orderId"]]["legs"][stop["leg"]][stop["kind"]]


def drive(a: dict[str, Any], b: dict[str, Any], desk: "Desk", orders: dict[str, Any]) -> int:
    """The road minutes from one stop to the next."""
    start, end = side(a, orders)["placeId"], side(b, orders)["placeId"]
    return desk.ctx.minutes(start, end) if start != end else 0


def window(stop: dict[str, Any], orders: dict[str, Any]) -> dict[str, int]:
    """The stop's own window, or the order's: the pickup window, and for a delivery up to the deadline."""
    if "window" in stop:
        return stop["window"]
    order = orders[stop["orderId"]]
    span = side(stop, orders)["window"]
    return span if stop["kind"] == "pickup" else {"from": span["from"], "to": max(span["from"], order["deadline"])}


def is_open(hours: Optional[dict[str, Any]], minute: int) -> bool:
    """Whether a site's stated hours show it open at a minute. A private address has no hours."""
    if not hours:
        return True
    day, clock = minute // DAY % 7, minute % DAY
    if day == 5 and hours.get("saturday"):
        return hours["saturday"]["opens"] <= clock <= hours["saturday"]["closes"]
    return day in hours["weekdays"] and hours["opens"] <= clock <= hours["closes"]
