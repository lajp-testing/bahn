"""The offers: direct offers for a gig that the app has not filled in time, and for our drivers who finish near a new gig. Track 5 (more cars per driver).

When an order's deadline warning comes (`urgent`), or a driver drops its gig (`drops`), the gig goes as a
direct offer to the few drivers most likely to take it, at the fee the app shows now plus `up` times the
gig's typical fee. An offer reaches drivers that a notification does not (one of our drivers who finishes
near the pickup), and a driver who reads it has no raise to wait for (RULES.md, Direct offers).

When we post a gig for a single car (`new`), it also goes as an offer to our drivers who finish near its
pickup, at the fee the app shows now times `new_fee`: a second gig costs such a driver only the extra time
and tickets, and the app does not notify them where our gigs have taken them. The gig stays in the app, so
nothing is lost when nobody takes it. Such a driver gets the offer only when they reach the pickup inside
its window from where we leave them; when the window or the road is unknown, nobody does.

The drivers, best first: our drivers whose last delivery is within `near` km of the pickup, in the last
`fresh` minutes or still to come; then the drivers who viewed this gig, last viewer first. Never the driver
who dropped it, a driver without the manual licence the gig asks for, or one who already has three offers
today. At most `n` open offers per gig; after the answers, the next drivers, `rounds` times in all.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .bundles import orders_in
from .parts import Part

if TYPE_CHECKING:
    from .desk import Desk

DAY = 24 * 60
OPEN = 10  # an offer is open for 10 minutes; its answer comes by then


class Offers(Part):
    def __init__(self, on: str = "urgent", n: int = 3, up: float = 0.1, near: float = 30.0, fresh: int = 180, rounds: int = 2, new_fee: float = 1.0):
        self.on = frozenset(on.replace("+", ",").split(",")) - {""}
        self.n, self.up, self.near, self.fresh, self.rounds = int(n), float(up), float(near), int(fresh), int(rounds)
        self.new_fee = float(new_fee)
        self.schedule: dict[str, list[dict[str, int]]] = {}  # gig id -> its fee schedule now
        self.viewers: dict[str, list[str]] = {}  # gig id -> drivers who viewed it, in order
        self.dropped_by: dict[str, set[str]] = {}  # gig id -> drivers who dropped it or did not show
        self.driver_of: dict[str, str] = {}  # gig id -> the driver who holds it
        self.at: dict[str, tuple[str, int]] = {}  # driver id -> (place, minute) of their last or next delivery for us
        self.per_day: dict[tuple[str, int], int] = {}  # (driver, day) -> offers sent
        self.open: dict[str, dict[str, int]] = {}  # gig id -> driver -> minute the offer was sent
        self.asked: dict[str, set[str]] = {}  # order id -> drivers already offered its car
        self.wanted: dict[str, int] = {}  # order id -> rounds left
        self.chain: set[str] = set()  # order ids wanted by the `new` trigger, which offer at the app's fee times `new_fee`
        self.sent: dict[str, int] = {}  # (driver, gig) key -> fee, for the counts
        self.counts = {"sent": 0, "accepted": 0, "declined": 0, "expired": 0}
        self.accepted_fees: list[tuple[int, int]] = []  # (fee, typical fee of the gig's cars)

    # --- what the part learns ---

    def observe(self, event: dict[str, Any], desk: "Desk", replay: bool) -> None:
        kind, gig = event["kind"], event.get("gigId")
        if kind == "gig_viewed":
            self.viewers.setdefault(gig, []).append(event["driverId"])
        elif kind == "gig_booked":
            self.driver_of[gig] = event["driverId"]
            self.place_driver(gig, event["driverId"], desk)
        elif kind in ("gig_dropped", "no_show"):
            self.dropped_by.setdefault(gig, set()).add(event["driverId"])
            self.driver_of.pop(gig, None)
            if "drops" in self.on:
                for order_id in self.orders_of(gig, desk):
                    self.want(order_id, desk)
        elif kind == "delivered" and gig in self.driver_of:
            self.at[self.driver_of[gig]] = (event["placeId"], event["at"])
        elif kind == "deadline_close" and "urgent" in self.on:
            self.want(event["orderId"], desk)
        elif kind == "offer_answered":
            self.open.get(gig, {}).pop(event["driverId"], None)
            self.counts[event["answer"]] = self.counts.get(event["answer"], 0) + 1
            if event["answer"] == "accepted":
                self.driver_of[gig] = event["driverId"]
                self.place_driver(gig, event["driverId"], desk)
                fee = self.sent.get(f"{event['driverId']} {gig}", 0)
                self.accepted_fees.append((fee, self.typical(gig, desk)))

    def result(self, action: dict[str, Any], result: dict[str, Any], desk: "Desk") -> None:
        if not result.get("ok"):
            if action["type"] == "offer":
                self.open.get(action["gigId"], {}).pop(action["driverId"], None)
            return
        if action["type"] == "post":
            self.schedule[result["id"]] = action["schedule"]
            if "new" in self.on and sum(1 for stop in action["stops"] if stop["kind"] == "pickup") == 1:
                for order_id in orders_in(action["stops"]):
                    if order_id in desk.orders and order_id not in desk.urgent and order_id not in self.wanted:
                        self.want(order_id, desk, rounds=1, chain=True)  # one round: the gig is in the app at the same time
        elif action["type"] == "reprice":
            self.schedule[action["gigId"]] = action["schedule"]
        elif action["type"] == "offer":  # also from the journal after a restart, so the limits hold
            driver, gig = action["driverId"], action["gigId"]
            self.open.setdefault(gig, {})[driver] = desk.now
            self.per_day[(driver, desk.now // DAY)] = self.per_day.get((driver, desk.now // DAY), 0) + 1
            for order_id in self.orders_of(gig, desk):
                self.asked.setdefault(order_id, set()).add(driver)
            self.sent[f"{driver} {gig}"] = action["feeCents"]
            self.counts["sent"] += 1

    def place_driver(self, gig: str, driver: str, desk: "Desk") -> None:
        """Where the driver will be: the last delivery of the gig they hold, at its window's end, or now."""
        post = desk.posts.get(gig)
        if not post:
            return
        last = post["stops"][-1]
        order = desk.orders.get(last["orderId"])
        if order is not None and last["kind"] == "delivery":
            window = last.get("window") or order["legs"][last["leg"]]["delivery"].get("window") or {}
            self.at[driver] = (order["legs"][last["leg"]]["delivery"]["placeId"], max(desk.now, window.get("to", desk.now)))

    # --- the decision ---

    def want(self, order_id: str, desk: "Desk", rounds: int | None = None, chain: bool = False) -> None:
        self.wanted[order_id] = self.rounds if rounds is None else rounds
        self.chain.discard(order_id)
        if chain:
            self.chain.add(order_id)
        desk.wake(desk.now + 1)  # the urgent repost or reprice goes first; the offer follows at the next stop

    def unwant(self, order_id: str) -> None:
        self.wanted.pop(order_id, None)
        self.chain.discard(order_id)

    def tick(self, desk: "Desk") -> None:
        if not self.wanted:
            return
        minute = desk.now % DAY
        if minute >= 23 * 60 - OPEN or minute < 7 * 60:  # no driver reads an offer from 23:00 to 07:00
            desk.wake((desk.now // DAY + (1 if minute >= 7 * 60 else 0)) * DAY + 7 * 60)
            return
        pending = {gig for action in desk.outbox if action["type"] in ("post", "reprice", "withdraw") for gig in [action.get("gigId")]}
        for order_id in list(self.wanted):
            order = desk.orders.get(order_id)
            if order is None or desk.now >= order["lastPickupAt"]:
                self.unwant(order_id)
                continue
            mine = desk.gigs_of(order_id)
            gigs = [g for g in mine if g not in desk.booked]
            if mine and not gigs:  # a driver holds it now
                self.unwant(order_id)
                continue
            if not mine:  # its new gig is not in the app yet
                desk.wake(desk.now + 5)
                continue
            for gig in gigs:
                if len(orders_in(desk.posts[gig]["stops"])) > 1:  # a bundle: the urgent fees split it first
                    continue
                if gig in pending:
                    desk.wake(desk.now + 1)
                    continue
                if self.open.get(gig):
                    desk.wake(max(self.open[gig].values()) + OPEN + 1)
                    continue
                if self.wanted.get(order_id, 0) <= 0:
                    self.unwant(order_id)
                    continue
                chain = order_id in self.chain
                drivers = self.candidates(gig, order, desk, chain)
                if not drivers:
                    self.unwant(order_id)
                    continue
                fee = self.fee(gig, desk, chain)
                for driver in drivers:
                    desk.outbox.append({"type": "offer", "gigId": gig, "driverId": driver, "feeCents": fee})
                    self.open.setdefault(gig, {})[driver] = desk.now  # until the world's answer replaces it
                self.wanted[order_id] -= 1
                desk.wake(desk.now + OPEN + 1)

    def candidates(self, gig: str, order: dict[str, Any], desk: "Desk", chain: bool = False) -> list[str]:
        post = desk.posts[gig]
        stop = post["stops"][0]
        pickup = order["legs"][stop["leg"]]["pickup"]["placeId"]
        manual = post["audience"].get("manualLicence")
        roster = {d["id"]: d for d in desk.ctx.roster}
        skip = self.dropped_by.get(gig, set()) | self.asked.get(order["id"], set())
        day = desk.now // DAY

        def fits(driver: str) -> bool:
            profile = roster.get(driver)
            return (profile is not None and driver not in skip and self.per_day.get((driver, day), 0) < 3
                    and (not manual or profile.get("licence") == "manual"))

        window = (stop.get("window") or order["legs"][stop["leg"]]["pickup"].get("window") or {}).get("to")
        near = []
        for driver, (place, at) in self.at.items():
            km = 0.0 if place == pickup else desk.ctx.straight_km(place, pickup)
            drive = 0 if place == pickup else desk.ctx.road_minutes.get((place, pickup))
            if chain and (window is None or drive is None):
                continue  # a chain offer must fit the pickup's window from where we leave the driver; unsure offers nobody
            latest = min(order["lastPickupAt"], window - drive) if chain else order["lastPickupAt"]
            if at >= desk.now - self.fresh and at <= latest and km <= self.near:
                near.append((km, driver))
        chosen = [driver for _, driver in sorted(near) if fits(driver)]
        if not chain:  # a chain offer goes only to our drivers nearby; the gig is in the app for everyone else
            chosen += [driver for driver in reversed(self.viewers.get(gig, [])) if fits(driver)]
        return list(dict.fromkeys(chosen))[: self.n]

    def fee(self, gig: str, desk: "Desk", chain: bool = False) -> int:
        """The fee the app shows now, plus `up` times the typical fee of the gig's cars; a chain offer: the app's fee times `new_fee`."""
        steps = self.schedule.get(gig) or desk.posts[gig]["schedule"]
        now = [step["feeCents"] for step in steps if step["at"] <= desk.now] or [steps[0]["feeCents"]]
        if chain:
            return int(now[-1] * self.new_fee + 0.5)
        return int(now[-1] + self.up * self.typical(gig, desk) + 0.5)

    def typical(self, gig: str, desk: "Desk") -> int:
        post = desk.posts.get(gig)
        if not post:
            return 0
        total = 0.0
        for order_id in orders_in(post["stops"]):
            request, order = desk.requests.get(order_id), desk.orders.get(order_id)
            if request and order:
                cars = sum(1 for s in post["stops"] if s["kind"] == "pickup" and s["orderId"] == order_id)
                total += request["referenceFeeCents"] * cars / len(order["legs"])
        return int(total + 0.5)

    def orders_of(self, gig: str, desk: "Desk") -> list[str]:
        post = desk.posts.get(gig)
        return orders_in(post["stops"]) if post else []
