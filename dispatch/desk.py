"""The desk: what the dispatcher remembers, and its answer to each event.

It is the kit starter's desk with its decisions moved into four parts (`dispatch.parts`):
the quoter prices a request, the intake decides how much work to take, the fees set a gig's
fee schedule, and the notes turn a dealer's note into stop windows. A fifth part, the bundles,
may put a newly won car into an open gig with another car. A policy is one choice of parts
(`dispatch.policies`). The desk itself only keeps the books and the mechanics.

The same desk plays practice worlds (`harness.play`) and the final (`dispatch.live`).
"""
from __future__ import annotations

from typing import Any, Optional

from spread.client import World
from spread.types import Action, ActionResult, Audience, DeskEvent, DeskEventKind, DeskSnapshot, Gig, Order, PostAction, PriceRequest

from .bundles import orders_in, resume
from .context import Context
from .parts import Parts, Retry

HOUR, DAY = 60, 24 * 60
# The events that need an answer. Every other event arrives with the next one of these.
WAKE_ON: list[DeskEventKind] = ["price_request", "order_won", "order_changed", "order_cancelled", "visit_failed", "gig_expired", "deadline_close"]


class Desk:
    def __init__(self, world: World, ctx: Context, parts: Parts, now: int):
        self.world, self.ctx, self.parts, self.now = world, ctx, parts, now
        self.level = ctx.level
        self.outbox: list[Action] = []  # the actions decided since the desk last sent
        self.requests: dict[str, PriceRequest] = {}
        self.orders: dict[str, Order] = {}  # the orders won and not cancelled
        self.leg_gigs: dict[str, dict[int, str]] = {}  # order id -> leg -> the gig that carries the leg
        self.booked: set[str] = set()  # the gigs that a driver holds now
        self.posts: dict[str, PostAction] = {}  # gig id -> the post that made it
        self.urgent: set[str] = set()  # the orders whose deadline warning has come
        self.clock: dict[str, list[Any]] = {}  # order id -> the fee schedule of its car alone, which a bundle and a split keep to
        self.split_at: dict[str, int] = {}  # bundle gig id -> the minute at which, still without a driver, it goes back to one gig per car
        self.refused: list[tuple[int, Action, str]] = []  # (minute, action, reason) for each action the world refused
        self.wake_on: list[DeskEventKind] = list(dict.fromkeys(WAKE_ON + [kind for part in parts.all() for kind in part.wake_on]))
        self._timers: set[int] = set()

    # --- timers: a part asks to be woken at a minute, and gets `tick` then ---

    def wake(self, minute: int) -> None:
        """Asks for a `tick` at `minute`. In practice the clock stops there; in the final the desk ticks about once a second anyway."""
        if minute > self.now:
            self._timers.add(int(minute))

    def next_timer(self) -> Optional[int]:
        self._timers = {minute for minute in self._timers if minute > self.now}
        return min(self._timers) if self._timers else None

    def tick(self) -> None:
        """Called after each step of the clock, with `self.now` current."""
        for part in self.parts.all():
            part.tick(self)
        for gig_id, minute in list(self.split_at.items()):
            if gig_id not in self.booked and self.now >= minute:
                self.split(gig_id)

    # --- events ---

    def rejoin(self, snapshot: DeskSnapshot, history: list[DeskEvent]) -> None:
        """Rebuilds the books from the world, so a desk that stopped keeps its orders. The parts see the
        whole history first, so what they learned is back too. Then the desk answers what it missed: open
        requests, orders without a gig, failed visits without a new gig, and the deadline warnings."""
        for event in history:
            self.now = event["at"]  # a part that learns reads the minute from the desk
            if event["kind"] == "price_request":
                self.requests[event["request"]["id"]] = event["request"]
            for part in self.parts.all():
                part.observe(event, self, replay=True)
        self.now = snapshot["now"]
        posted: dict[str, list[Gig]] = {}  # order id -> its gigs, oldest first
        self.booked = {gig["id"] for gig in snapshot["gigs"] if gig["status"] in ("booked", "working", "done")}
        for gig in snapshot["gigs"]:
            for order_id in orders_in(gig["stops"]):
                posted.setdefault(order_id, []).append(gig)
            if gig["status"] in ("open", "booked", "working"):
                self.carry({"type": "post", "stops": gig["stops"], "audience": gig["audience"], "schedule": gig["schedule"]}, gig["id"])
        self.urgent = {e["orderId"] for e in history if e["kind"] == "deadline_close"}
        self.orders = {o["id"]: o for o in snapshot["orders"] if o["id"] in self.requests and o["status"] != "cancelled"}
        for order in self.orders.values():
            if order["status"] == "waiting" and not self.gigs_of(order["id"]):
                self.post(order, undelivered(order))
        for event in history:
            order = self.orders.get(event.get("orderId", ""))
            if order is None:
                continue
            if event["kind"] == "visit_failed" and order["deliveredAt"][event["leg"]] is None:
                later = [g for g in posted.get(order["id"], []) if g["postedAt"] >= event["at"] and g["id"] != event["gigId"]]
                if not any(stop["leg"] == event["leg"] for gig in later for stop in gig["stops"]):
                    self.retry(order["id"], event["leg"], event["reason"])
        for request in snapshot["openRequests"]:
            self.quote(request)

    def handle(self, event: DeskEvent) -> None:
        kind = event["kind"]
        if kind == "price_request":
            self.requests[event["request"]["id"]] = event["request"]
        for part in self.parts.all():
            part.observe(event, self, replay=False)
        if kind == "price_request":
            self.quote(event["request"])
        elif kind == "order_won":
            self.win(event["order"])
        elif kind == "order_changed":
            self.change(event["order"])
        elif kind == "order_cancelled":  # the world has stopped the car and told each of its gigs what happens
            for books in (self.orders, self.leg_gigs):
                books.pop(event["orderId"], None)
            for gig in event["gigs"]:  # an open bundle left the app with the cancelled car: its other cars go alone
                if gig["outcome"] == "withdrawn" and gig["gigId"] in self.posts:
                    self.split(gig["gigId"], live=False)
        elif kind == "visit_failed":
            self.retry(event["orderId"], event["leg"], event["reason"])
        elif kind == "gig_expired":
            self.repost(event["gigId"])
        elif kind == "deadline_close":  # it comes again when a driver drops the car after the first warning
            self.raise_fees(event["orderId"])
        elif kind == "gig_booked":
            self.booked.add(event["gigId"])
        elif kind in ("gig_dropped", "no_show"):  # after a no-show the gig is open again; a late driver still comes
            self.booked.discard(event["gigId"])
        elif kind == "delivered":
            self.delivered(event["orderId"], event["leg"], event["at"])

    def delivered(self, order_id: str, leg: int, at: int) -> None:
        self.leg_gigs.get(order_id, {}).pop(leg, None)
        if order_id in self.orders:
            self.orders[order_id]["deliveredAt"][leg] = at

    # --- quotes ---

    def quote(self, request: PriceRequest) -> None:
        """The quoter names a price for each option it wants; the intake may raise them or decline."""
        self.requests[request["id"]] = request
        prices = self.parts.quoter.prices(request, self)
        prices = self.parts.intake.admit(request, prices, self)
        if prices:
            self.outbox.append({"type": "quote", "requestId": request["id"], "prices": {kind: int(cents) for kind, cents in prices.items()}})

    def win(self, order: Order) -> None:
        if order["id"] in self.requests and order["id"] not in self.orders:  # rejoin can know it already
            self.orders[order["id"]] = order
            self.post(order, undelivered(order))

    def change(self, order: Order) -> None:
        if order["id"] in self.orders:
            self.orders[order["id"]] = order
            if self.withdraw(order["id"]):
                self.post(order, undelivered(order))

    # --- gigs ---

    def repost(self, gig_id: str) -> None:
        """Posts a gig again when one of its windows ended before a driver booked it."""
        action = self.posts.get(gig_id)
        # A gig the desk has already taken off and posted again, after a change of plan, needs nothing.
        if action is None or not any(self.leg_gigs.get(s["orderId"], {}).get(s["leg"]) == gig_id for s in action["stops"]):
            return
        if len(orders_in(action["stops"])) > 1:
            return self.split(gig_id, live=False, bare=True)
        for stop in action["stops"]:
            self.leg_gigs.get(stop["orderId"], {}).pop(stop["leg"], None)
        order = self.orders.get(action["stops"][0]["orderId"])
        if order is None:
            return
        stops, audience = self.parts.notes.again(action, order, self)
        self.outbox.append({"type": "post", "stops": without_windows(stops, self.now), "audience": audience, "schedule": self.fees_for(order, pickups(action))})

    def raise_fees(self, order_id: str) -> None:
        """From the order's deadline warning on, its gigs that no driver holds go at the urgent fees."""
        order = self.orders.get(order_id)
        if order is None:
            return
        self.urgent.add(order_id)
        self.send_post_of(order_id)
        for gig_id in self.gigs_of(order_id):
            if gig_id in self.booked:
                continue
            if len(orders_in(self.posts[gig_id]["stops"])) > 1:  # the urgent car needs its own fee, so the bundle ends
                self.split(gig_id)
            else:
                self.outbox.append({"type": "reprice", "gigId": gig_id, "schedule": self.fees_for(order, pickups(self.posts[gig_id]))})

    def fees_for(self, order: Order, cars: int) -> list[Any]:
        """The fee schedule for `cars` of the order's cars, from now."""
        return self.parts.fees.schedule(order, cars, order["id"] in self.urgent, self)

    def retry(self, order_id: str, leg: int, reason: str) -> None:
        if order_id in self.orders:
            order = self.orders[order_id]
            self.leg_gigs.get(order_id, {}).pop(leg, None)  # the world has taken the car out of the failed gig
            car_not_there = reason in ("not_ready", "closed")
            pickup_from = retry_from(order, self.requests[order_id], leg, self.now) if car_not_there else 0
            self.post(order, [leg], Retry(pickup_from, manual_licence=reason == "licence", plates=reason == "no_plates"))

    def post(self, order: Order, legs: list[int], retry: Retry = Retry()) -> None:
        stops, audience = self.parts.notes.plan(order, legs, self.requests[order["id"]], retry, self)
        stops, schedule = without_windows(stops, self.now), self.fees_for(order, len(legs))
        if len(order["legs"]) == 1:
            self.clock[order["id"]] = schedule
            bundles = self.parts.bundles
            joined = bundles.join(order, stops, audience, self) if bundles and retry == Retry() else None
            if joined:  # the car joins an open gig: that gig leaves the app, and one gig with both cars takes its place
                gig_id, stops, audience = joined
                self.outbox.append({"type": "withdraw", "gigId": gig_id})
                for member in orders_in(self.posts[gig_id]["stops"]):  # so that no second car joins the gig that is leaving
                    self.leg_gigs.pop(member, None)
                schedule = bundles.fees([self.clock[member] for member in orders_in(stops)], self.now)
        self.outbox.append({"type": "post", "stops": stops, "audience": audience, "schedule": schedule})
        if len(legs) == 1:
            return
        # A trade-in over the 12-hour limit for a gig with two cars goes as one gig per car.
        self.send()
        if not self.gigs_of(order["id"]):
            for leg in legs:
                self.post(order, [leg], retry)

    def split(self, gig_id: str, live: bool = True, bare: bool = False) -> None:
        """A bundle goes back to one gig per car, each at the fee its own schedule shows now. `live`: the bundle
        is still in the app. `bare`: one of its windows ended, so the cars go without stop windows of their own."""
        action = self.posts[gig_id]
        self.split_at.pop(gig_id, None)
        if live:
            self.outbox.append({"type": "withdraw", "gigId": gig_id})
        for order_id in orders_in(action["stops"]):
            if order_id in self.orders and self.leg_gigs.get(order_id, {}).get(0) == gig_id:  # not cancelled, and its car is still in this gig
                self.leg_gigs.pop(order_id)
                self.alone(self.orders[order_id], bare)

    def alone(self, order: Order, bare: bool = False) -> None:
        """Posts a bundle's car as a gig of its own, at the fee its own schedule shows now."""
        stops, audience = self.parts.notes.plan(order, [0], self.requests[order["id"]], Retry(), self)
        if bare:
            stops = [{k: v for k, v in stop.items() if k != "window"} for stop in stops]
        fresh = order["id"] in self.urgent or order["id"] not in self.clock
        schedule = self.fees_for(order, 1) if fresh else resume(self.clock[order["id"]], self.now)
        self.outbox.append({"type": "post", "stops": without_windows(stops, self.now), "audience": audience, "schedule": schedule})

    def gigs_of(self, order_id: str) -> list[str]:
        """The gigs that carry the order's undelivered legs: one, or one for each leg of a split trade-in."""
        return list(dict.fromkeys(self.leg_gigs.get(order_id, {}).values()))

    def carry(self, action: PostAction, gig_id: str) -> None:
        """Remembers a gig that the world accepted: the post that made it, and the legs it carries."""
        for stop in action["stops"]:
            self.leg_gigs.setdefault(stop["orderId"], {})[stop["leg"]] = gig_id
        self.posts[gig_id] = action
        if len(orders_in(action["stops"])) > 1 and self.parts.bundles:
            self.split_at[gig_id] = self.parts.bundles.last_start(action["stops"], self) - self.parts.bundles.split
            self.wake(self.split_at[gig_id])

    def withdraw(self, order_id: str) -> bool:
        """Takes an order's gigs out of the drivers' app. False, and nothing withdrawn, when a driver holds one of them."""
        self.send_post_of(order_id)
        gigs = self.gigs_of(order_id)
        if any(gig_id in self.booked for gig_id in gigs):
            return False
        self.leg_gigs.pop(order_id, None)
        for gig_id in gigs:
            if len(orders_in(self.posts[gig_id]["stops"])) > 1:  # the other cars of a bundle go alone
                self.split(gig_id)
            else:
                self.outbox.append({"type": "withdraw", "gigId": gig_id})
        return True

    # --- sending ---

    def send_post_of(self, order_id: str) -> None:
        """A post of the order still in the outbox goes to the world now, so the desk knows its gig."""
        if any(action["type"] == "post" and order_id in orders_in(action["stops"]) for action in self.outbox):
            self.send()

    def send(self) -> None:
        """Sends the outbox now. In practice, the outbox goes with the next advance instead."""
        actions, self.outbox = self.outbox, []
        if actions:
            self.read_results(actions, self.world.act(actions))

    def read_results(self, actions: list[Action], results: list[ActionResult]) -> None:
        """Remembers the gig of each post that the world accepted, and each action that it refused."""
        for action, result in zip(actions, results):
            if result["ok"] is not True:
                self.refused.append((self.now, action, result.get("reason", "")))
                if action["type"] == "post" and len(orders_in(action["stops"])) > 1:  # a refused bundle: each car without a gig goes alone
                    for order_id in orders_in(action["stops"]):
                        if order_id in self.orders and len(self.orders[order_id]["legs"]) == 1 and not self.gigs_of(order_id):
                            self.alone(self.orders[order_id])
                if action["type"] == "withdraw" and action["gigId"] in self.posts:  # a driver booked it first: the gig still carries its cars
                    self.booked.add(action["gigId"])
                    for stop in self.posts[action["gigId"]]["stops"]:
                        if stop["orderId"] in self.orders and self.orders[stop["orderId"]]["deliveredAt"][stop["leg"]] is None:
                            self.leg_gigs.setdefault(stop["orderId"], {}).setdefault(stop["leg"], action["gigId"])
            elif action["type"] == "post":
                self.carry(action, result["id"])
            for part in self.parts.all():
                part.result(action, result, self)


def retry_from(order: Order, request: PriceRequest, leg: int, now: int) -> int:
    """When to try a car again after a visit found it not ready or the site closed: two hours on, or,
    when the dealer moved the deadline for a car that is late, when the car should be ready by the
    same delay."""
    promised = next((o["deadline"] for o in request["options"] if o["kind"] == order["option"]), order["deadline"])
    delay = max(0, order["deadline"] - promised)
    return max(now + 2 * HOUR, order["legs"][leg]["pickup"]["window"]["from"] + delay)


def undelivered(order: Order) -> list[int]:
    return [leg for leg in range(len(order["legs"])) if order["deliveredAt"][leg] is None]


def pickups(action: PostAction) -> int:
    """The cars a post carries."""
    return sum(1 for stop in action["stops"] if stop["kind"] == "pickup")


def without_windows(stops: list[Any], before: float) -> list[Any]:
    """Leaves out the stop windows that end before `before`, so the world's window applies: once the order's
    window has ended, it runs to the end of the world."""
    return [{k: v for k, v in stop.items() if k != "window"} if "window" in stop and stop["window"]["to"] < before else stop for stop in stops]


__all__ = ["Desk", "Audience", "WAKE_ON", "HOUR", "DAY", "undelivered", "pickups", "without_windows", "retry_from"]
