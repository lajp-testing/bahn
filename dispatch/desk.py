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
        self.booked_fee: dict[str, int] = {}  # gig id -> the fee its last driver booked it at
        self.late_posted: set[str] = set()  # orders posted again without windows after their last pickup minute
        self.urgent_gigs: set[str] = set()  # gigs that already carry an urgent fee schedule
        self.schedules: dict[str, list[Any]] = {}  # gig id -> its fee schedule in the app now (its post, or its last reprice)
        self.held: dict[str, dict[str, Any]] = {}  # order id -> a newly won car's post, held back for a partner until its "until" minute (Bundles.hold)
        self.split_at: dict[str, int] = {}  # bundle gig id -> the minute at which, still without a driver, it goes back to one gig per car
        self.refused: list[tuple[int, Action, str]] = []  # (minute, action, reason) for each action the world refused
        self.wake_on: list[DeskEventKind] = list(dict.fromkeys(WAKE_ON + [kind for part in parts.all() for kind in part.wake_on]))
        self._timers: set[int] = set()
        self.journal = None

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
        if getattr(self.parts.fees, "early", 0):  # the desk's own, earlier deadline warning
            for order in list(self.orders.values()):
                if order["id"] not in self.urgent and self.now >= self.parts.fees.urgent_from(order) and any(at is None for at in order["deliveredAt"]):
                    gigs = self.gigs_of(order["id"])
                    if gigs and any(gig_id not in self.booked for gig_id in gigs):
                        self.raise_fees(order["id"])
        if getattr(self.parts.fees, "rescue", 0):
            self.rescue()
        repairs = self.parts.repairs
        if "late" in repairs:  # past its last pickup minute an open gig can find no driver: post it again, without windows
            for order in list(self.orders.values()):
                gigs = self.gigs_of(order["id"])
                if (order["id"] not in self.late_posted and self.now > order["lastPickupAt"] and gigs
                        and not any(gig_id in self.booked for gig_id in gigs) and any(at is None for at in order["deliveredAt"])):
                    self.late_posted.add(order["id"])
                    if self.withdraw(order["id"]):
                        self.post_bare(order)
        if "orphans" in repairs:  # an undelivered car with no gig, after a refused post: post it again, without windows
            waiting = {stop["orderId"] for action in self.outbox if action["type"] == "post" for stop in action["stops"]} | set(self.held)
            for order in list(self.orders.values()):
                legs = [leg for leg in undelivered(order) if leg not in self.leg_gigs.get(order["id"], {})]
                if legs and order["id"] not in waiting and order["status"] != "cancelled":
                    self.post_bare(order, legs)

    # --- events ---

    def rejoin(self, snapshot: DeskSnapshot, history: list[DeskEvent], journal: Optional[list[dict[str, Any]]] = None) -> None:
        """Rebuilds the books from the world, so a desk that stopped keeps its orders. The parts see the
        whole history first, so what they learned is back too. Then the desk answers what it missed: open
        requests, orders without a gig, failed visits without a new gig, and the deadline warnings."""
        timeline = [(event["at"], 0, i, event) for i, event in enumerate(history)]
        timeline += [(line["at"], 1, i, line) for i, line in enumerate(journal or [])]
        for minute, kind, _, item in sorted(timeline, key=lambda row: row[:3]):
            self.now = minute
            if kind == 0:
                if item["kind"] == "price_request":
                    self.requests[item["request"]["id"]] = item["request"]
                for part in self.parts.all():
                    part.observe(item, self, replay=True)
            else:
                action, result = item["action"], item["result"]
                if action["type"] == "quote":
                    intake = self.parts.intake
                    request = self.requests.get(action["requestId"])
                    if request is not None and hasattr(intake, "pending"):
                        from .quote import decline
                        intake.pending = {k: v for k, v in intake.pending.items() if v > minute}
                        if action["prices"] != decline(request):
                            intake.pending[request["id"]] = request["respondBy"]
                if action["type"] == "post" and result.get("ok") and pickups(action) == 1:
                    members = orders_in(action["stops"])
                    if len(members) == 1:
                        self.clock[members[0]] = action["schedule"]
                for part in self.parts.all():
                    part.result(action, result, self)
        self.now = snapshot["now"]
        if journal is not None and hasattr(self.parts.intake, "pending"):
            self.parts.intake.pending = {k: v for k, v in self.parts.intake.pending.items() if v > self.now}
        self.orders = {o["id"]: o for o in snapshot["orders"] if o["id"] in self.requests and o["status"] != "cancelled"}
        posted: dict[str, list[Gig]] = {}  # order id -> its gigs, oldest first
        self.booked = {gig["id"] for gig in snapshot["gigs"] if gig["status"] in ("booked", "working", "done")}
        for gig in snapshot["gigs"]:
            for order_id in orders_in(gig["stops"]):
                posted.setdefault(order_id, []).append(gig)
            if gig["status"] in ("open", "booked", "working"):
                self.carry({"type": "post", "stops": gig["stops"], "audience": gig["audience"], "schedule": gig["schedule"]}, gig["id"])
        self.urgent = {e["orderId"] for e in history if e["kind"] == "deadline_close"}
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
            self.booked_fee[event["gigId"]] = event["feeCents"]
        elif kind == "offer_answered" and event["answer"] == "accepted":  # a direct offer booked the driver (dispatch/offers.py)
            self.booked.add(event["gigId"])
        elif kind in ("gig_dropped", "no_show"):  # after a no-show the gig is open again; a late driver still comes
            self.booked.discard(event["gigId"])
            if "drops" in self.parts.repairs and kind == "gig_dropped":
                self.after_drop(event["gigId"])
            elif getattr(self.parts.fees, "flat_drop", 0) and kind == "gig_dropped":
                self.last_day_drop(event["gigId"])
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
            self.post(order, undelivered(order), hold=True)
            if "late" in self.parts.repairs:
                self.wake(order["lastPickupAt"] + 1)
            if getattr(self.parts.fees, "early", 0):
                self.wake(self.parts.fees.urgent_from(order))
            if getattr(self.parts.fees, "rescue", 0):
                self.wake(self.parts.fees.rescue_from(order))

    def change(self, order: Order) -> None:
        if order["id"] in self.orders:
            self.orders[order["id"]] = order
            if "late" in self.parts.repairs:
                self.wake(order["lastPickupAt"] + 1)
            if getattr(self.parts.fees, "rescue", 0):
                self.wake(self.parts.fees.rescue_from(order))
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
        self.outbox.append({"type": "post", "stops": self.cut(stops), "audience": audience, "schedule": self.fees_for(order, pickups(action))})

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
            if "keep_urgent" in self.parts.repairs and gig_id in self.urgent_gigs:
                continue  # a second warning does not start the urgent ladder again from its bottom
            if len(orders_in(self.posts[gig_id]["stops"])) > 1:  # the urgent car needs its own fee, so the bundle ends
                self.split(gig_id)
            else:
                self.outbox.append({"type": "reprice", "gigId": gig_id, "schedule": self.fees_for(order, pickups(self.posts[gig_id]))})
                self.urgent_gigs.add(gig_id)

    def rescue(self) -> None:
        """A single car without a driver and with little of the drivers' day left before its last pickup goes at once to the
        top of its normal ladder (`MeasuredFees.rescue`), also right after a drop. Urgent cars keep the urgent ladder."""
        for order in list(self.orders.values()):
            if order["id"] in self.urgent or not self.parts.fees.rescuing(order, 1, self.now):
                continue
            for gig_id in self.gigs_of(order["id"]):
                action = self.posts.get(gig_id)
                if gig_id in self.booked or action is None or len(orders_in(action["stops"])) > 1 or pickups(action) != 1:
                    continue
                top = self.fees_for(order, 1)
                steps = self.schedules.get(gig_id) or action["schedule"]
                started = [step["feeCents"] for step in steps if step["at"] <= self.now]
                if (max(started) if started else steps[0]["feeCents"]) < top[0]["feeCents"]:
                    self.outbox.append({"type": "reprice", "gigId": gig_id, "schedule": top})
                    self.schedules[gig_id] = top  # so the next tick does not send it again before the world answers

    def fees_for(self, order: Order, cars: int) -> list[Any]:
        """The fee schedule for `cars` of the order's cars, from now."""
        urgent = order["id"] in self.urgent
        if urgent and "calm" in self.parts.repairs and self.now > order["lastPickupAt"]:
            # past its last pickup minute the car is late anyway, and an urgent fee does not deliver it sooner (t3s10-calm: +EUR 5,347 / 30 weeks)
            calm = self.parts.fees.schedule(order, cars, False, self)
            if "guard" not in self.parts.repairs:
                return calm
            # untested: from 6 hours before the car leaves the 24-hour refund tier (about lastPickupAt + 24 h), the urgent ladder again
            turn = order["lastPickupAt"] + 18 * 60
            rush = [step for step in self.parts.fees.schedule(order, cars, True, self) if step["at"] >= turn]
            kept = [step for step in calm if step["at"] < turn]
            floor = kept[-1]["feeCents"] if kept else 0
            return kept + [{"at": max(step["at"], turn), "feeCents": max(step["feeCents"], floor)} for step in rush] if kept else self.parts.fees.schedule(order, cars, True, self)
        return self.parts.fees.schedule(order, cars, urgent, self)

    def retry(self, order_id: str, leg: int, reason: str) -> None:
        if order_id in self.orders:
            order = self.orders[order_id]
            self.leg_gigs.get(order_id, {}).pop(leg, None)  # the world has taken the car out of the failed gig
            car_not_there = reason in ("not_ready", "closed")
            pickup_from = retry_from(order, self.requests[order_id], leg, self.now) if car_not_there else 0
            self.post(order, [leg], Retry(pickup_from, manual_licence=reason == "licence", plates=reason == "no_plates"))

    def post(self, order: Order, legs: list[int], retry: Retry = Retry(), hold: bool = False) -> None:
        self.held.pop(order["id"], None)
        stops, audience = self.parts.notes.plan(order, legs, self.requests[order["id"]], retry, self)
        stops, schedule = self.cut(stops), self.fees_for(order, len(legs))
        if len(order["legs"]) == 1:
            self.clock[order["id"]] = schedule
            bundles = self.parts.bundles
            joined = bundles.join(order, stops, audience, self) if bundles and retry == Retry() else None
            if joined:  # the car joins a gig: that gig leaves the app, or is not sent, and one gig with all its cars takes its place
                gig, stops, audience = joined
                if isinstance(gig, str):
                    self.outbox.append({"type": "withdraw", "gigId": gig})
                    for member in orders_in(self.posts[gig]["stops"]):  # so that no second car joins the gig that is leaving
                        self.leg_gigs.pop(member, None)
                else:
                    self.outbox = [action for action in self.outbox if action is not gig]
                    self.held = {key: action for key, action in self.held.items() if action is not gig}
                schedule = bundles.fees([self.clock.get(member) or self.fees_for(self.orders[member], 1) for member in orders_in(stops)], self.now)
            elif hold and bundles and bundles.holds(order, stops, self):  # no gig to join: wait a little for a partner
                self.held[order["id"]] = {"type": "post", "stops": stops, "audience": audience, "schedule": schedule, "until": self.now + bundles.hold}
                self.wake(self.now + bundles.hold)
                return
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
        self.outbox.append({"type": "post", "stops": self.cut(stops), "audience": audience, "schedule": schedule})

    def after_drop(self, gig_id: str) -> None:
        """A dropped gig comes back with its old schedule, whose steps have all started: its top fee. It goes back to
        the fee it was booked at instead, and climbs again from there on a fresh ladder."""
        action = self.posts.get(gig_id)
        members = orders_in(action["stops"]) if action else []
        if len(members) != 1 or members[0] not in self.orders or members[0] in self.urgent:
            return
        order, fee = self.orders[members[0]], self.booked_fee.get(gig_id, 0)
        if fee and getattr(self.parts.fees, "flat", 0):  # flat fees: the fee the gig had, not more
            self.outbox.append({"type": "reprice", "gigId": gig_id, "schedule": [{"at": self.now, "feeCents": fee}]})
            return
        fresh = self.fees_for(order, pickups(action))
        schedule = [{"at": self.now, "feeCents": fee}] + [step for step in fresh if step["feeCents"] > fee and step["at"] > self.now]
        self.outbox.append({"type": "reprice", "gigId": gig_id, "schedule": schedule[:48]})

    def last_day_drop(self, gig_id: str) -> None:
        """A single car dropped inside its last `flat_last` minutes has no look-again step left: it comes back at once at
        the top a new post would reach, if that is above the fee it was booked at (t1s16)."""
        action = self.posts.get(gig_id)
        members = orders_in(action["stops"]) if action else []
        if len(members) != 1 or members[0] not in self.orders or members[0] in self.urgent:
            return
        order = self.orders[members[0]]
        if order["lastPickupAt"] - self.now >= self.parts.fees.flat_last:
            return
        top = self.fees_for(order, pickups(action))[-1]["feeCents"]
        if top > self.booked_fee.get(gig_id, 0):
            self.outbox.append({"type": "reprice", "gigId": gig_id, "schedule": [{"at": self.now, "feeCents": top}]})

    def cut(self, stops: list[Any]) -> list[Any]:
        """The stops without the windows that have ended. With the "windows" repair a window that ends this minute
        has ended too: the world refuses a gig whose window ends now, and the car would never be posted again."""
        return without_windows(stops, self.now + ("windows" in self.parts.repairs))

    def post_bare(self, order: Order, legs: Optional[list[int]] = None) -> None:
        """Posts the order's undelivered cars, one gig each, without stop windows of their own: the world then lets
        the stops run to the end of the week once no driver can be on time."""
        for leg in legs if legs is not None else undelivered(order):
            stops, audience = self.parts.notes.plan(order, [leg], self.requests[order["id"]], Retry(), self)
            stops = [{k: v for k, v in stop.items() if k != "window"} for stop in stops]
            self.outbox.append({"type": "post", "stops": stops, "audience": audience, "schedule": self.fees_for(order, 1)})

    def gigs_of(self, order_id: str) -> list[str]:
        """The gigs that carry the order's undelivered legs: one, or one for each leg of a split trade-in."""
        return list(dict.fromkeys(self.leg_gigs.get(order_id, {}).values()))

    def carry(self, action: PostAction, gig_id: str) -> None:
        """Remembers a gig that the world accepted: the post that made it, and the legs it carries."""
        for stop in action["stops"]:
            self.leg_gigs.setdefault(stop["orderId"], {})[stop["leg"]] = gig_id
        self.posts[gig_id] = action
        self.schedules[gig_id] = action["schedule"]
        if any(order_id in self.urgent for order_id in orders_in(action["stops"])):
            self.urgent_gigs.add(gig_id)
        if len(orders_in(action["stops"])) > 1 and self.parts.bundles:
            self.split_at[gig_id] = self.parts.bundles.split_at(action["stops"], self)
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
            results = self.world.act(actions)
            if self.journal is not None:
                self.journal(actions, results, self.now)
            self.read_results(actions, results)

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
            elif action["type"] == "reprice":
                self.schedules[action["gigId"]] = action["schedule"]
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
