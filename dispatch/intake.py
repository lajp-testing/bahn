"""The intake: how much work to take. Owned by track 1 (intake and on-time).

It sees the quoter's prices for a request and returns the prices to send: the same, higher, or a
decline (`dispatch.quote.decline`). An empty answer sends no quote, which costs a little goodwill.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .parts import Part

if TYPE_CHECKING:
    from .desk import Desk


class Intake(Part):
    """The starter's intake: take everything."""

    def admit(self, request: dict[str, Any], prices: dict[str, int], desk: "Desk") -> dict[str, int]:
        return prices


class ReachIntake(Intake):
    """Takes only the cars that drivers can reach: it declines a request whose leg drives longer than
    `max_drive` road minutes, or whose pickup has fewer than `min_drivers` drivers living within `near_km`
    (straight line), and it leaves out `same_day` unless `same_day` is true. A declined request gets a
    losing quote, which costs nothing, instead of no quote, which costs goodwill.

    Measured on dev-01 to dev-04 at level 8, with markup 1.5 on every other option and the starter's fees:
    margin €1,961 / €5,503 / €5,711 / €6,165 at 95.0-96.9% on time (the starter: about -€72k at 45% on time)."""

    def __init__(self, max_drive: int = 300, min_drivers: int = 3, near_km: float = 60.0, same_day: bool = False,
                 future_same_day: bool = False, late_budget: float = 0.0, budget_after: int = 40,
                 brake_drivers: int = 10, brake_drive: int = 180, long_lanes: bool = False,
                 batch_slots: bool = False, noted_slots: bool = False, private_slots: bool = False,
                 trade_ins: bool = False, no_private: bool = False, no_trade_ins: bool = False, thin_drivers: int = 0,
                 thin_both: bool = False, long_max: int = 600, long_markup: float = 1.0, expand_brake: float = 0.06):
        self.long_max, self.long_markup, self.expand_brake = long_max, long_markup, expand_brake
        self.no_private, self.no_trade_ins, self.thin_drivers, self.thin_both = no_private, no_trade_ins, thin_drivers, thin_both
        self.max_drive, self.min_drivers, self.near_km, self.same_day = max_drive, min_drivers, near_km, same_day
        # future_same_day: a `same_day` option on a car that is ready a day or more after the request is not an
        # urgent order, so quote it on a plain single-car request (the fresh-angles thread's future_ready).
        self.future_same_day = future_same_day
        # late_budget: when the late and at-risk orders reach this share of the orders won (after `budget_after`
        # orders), brake: no same_day, and only short legs from pickups with many drivers. 0 turns it off.
        self.late_budget, self.budget_after = late_budget, budget_after
        self.brake_drivers, self.brake_drive = brake_drivers, brake_drive
        self.won: set[str] = set()
        self.late: set[str] = set()
        self._near: dict[str, int] = {}
        self.long_lanes, self.batch_slots, self.noted_slots = long_lanes, batch_slots, noted_slots
        self.private_slots, self.trade_ins = private_slots, trade_ins
        self.expanding = any((long_lanes, batch_slots, noted_slots, private_slots, trade_ins))
        self.pending: dict[str, dict[str, Any]] = {}

    def observe(self, event: dict[str, Any], desk: "Desk", replay: bool) -> None:
        kind = event["kind"]
        if kind == "order_won":
            self.won.add(event["order"]["id"])
            self.pending.pop(event["order"]["id"], None)
        elif kind == "order_cancelled":
            self.won.discard(event["orderId"])
            self.late.discard(event["orderId"])
        elif kind == "ledger" and event["line"]["kind"] in ("late_refund", "undelivered_penalty") and event["line"]["orderId"]:
            self.late.add(event["line"]["orderId"])

    def at_risk(self, desk: "Desk") -> int:
        """Orders not yet late in the account that will probably be: past their deadline and undelivered, or
        warned and without a driver."""
        count = 0
        for order_id, order in desk.orders.items():
            if order_id in self.late or all(at is not None for at in order["deliveredAt"]):
                continue
            unbooked = not any(gig in desk.booked for gig in desk.gigs_of(order_id))
            if desk.now > order["deadline"] or (order_id in desk.urgent and unbooked):
                count += 1
        return count

    def braking(self, desk: "Desk") -> bool:
        if self.late_budget <= 0 or len(self.won) < self.budget_after:
            return False
        return (len(self.late) + self.at_risk(desk)) / len(self.won) >= self.late_budget

    def future_ready(self, request: dict[str, Any]) -> bool:
        leg = request["legs"][0]
        return (len(request["legs"]) == 1 and not leg["pickup"]["privateAddress"] and not leg["delivery"]["privateAddress"]
                and all(o["kind"] == "same_day" and o["deadline"] - request["respondBy"] >= 1440 for o in request["options"]))

    def drivers_near(self, place_id: str, desk: "Desk") -> int:
        if place_id not in self._near:
            homes = [driver["homePlaceId"] for driver in desk.ctx.roster]
            self._near[place_id] = sum(1 for home in homes if desk.ctx.straight_km(place_id, home) <= self.near_km)
        return self._near[place_id]

    def expansion_options(self, request: dict[str, Any], prices: dict[str, int], desk: "Desk") -> dict[str, int]:
        """Extra orders need reachable windows, qualified supply and room in the local unbooked queue.
        Existing intake is unchanged. The risk brake (`expand_brake`, six percent) applies to extra volume even
        when the optional whole-portfolio late budget is off. A long lane is taken up to `long_max` road minutes,
        at `long_markup` times the quoter's prices for its risk."""
        if len(self.late) + self.at_risk(desk) >= self.expand_brake * max(40, len(self.won)):
            return {}
        legs = request["legs"]
        private = any(leg[end]["privateAddress"] for leg in legs for end in ("pickup", "delivery"))
        trade = len(legs) > 1
        drives = [desk.ctx.minutes(leg["pickup"]["placeId"], leg["delivery"]["placeId"]) for leg in legs]
        long = max(drives) > self.max_drive
        if (trade and not self.trade_ins) or (private and not trade and not self.private_slots):
            return {}
        if long and (not self.long_lanes or max(drives) > self.long_max):
            return {}
        enabled = long or (trade and self.trade_ins) or (private and self.private_slots)
        enabled |= bool(self.batch_slots and request["batchId"]) or bool(self.noted_slots and request["note"])
        if not enabled or not desk.parts.notes.expansion_safe(request):
            return {}
        # Keep trade-ins together: splitting removes the old-car pickup's same-visit exception.
        road = sum(drives) + sum(desk.ctx.minutes(a["delivery"]["placeId"], b["pickup"]["placeId"])
                                 for a, b in zip(legs, legs[1:]))
        if trade and road > 720:
            return {}
        manual, plates = desk.parts.notes.requirements(request)
        premium = any(leg["car"]["premium"] for leg in legs)
        first = legs[0]["pickup"]
        drivers = [d for d in desk.ctx.roster
                   if desk.ctx.straight_km(first["placeId"], d["homePlaceId"]) <= self.near_km
                   and (not manual or d["licence"] == "manual")
                   and (not premium or (d["rating"] >= 4.8 and d["completedGigs"] >= 50))]
        if len(drivers) < max(6, self.min_drivers):
            return {}
        # Reserve quotes immediately, before a simultaneous batch resolves. Count existing unbooked
        # work as well as extra work; a booked driver is not evidence that another one is free.
        day = first["window"]["from"] // 1440
        waiting = list(self.pending.values()) + [o for oid, o in desk.orders.items()
                    if not all(at is not None for at in o["deliveredAt"])
                    and not any(g in desk.booked for g in desk.gigs_of(oid))]
        load = 0
        for other in waiting:
            if other["id"] == request["id"]:
                continue
            pickup = other["legs"][0]["pickup"]
            if pickup["window"]["from"] // 1440 != day:
                continue
            if desk.ctx.straight_km(first["placeId"], pickup["placeId"]) <= self.near_km:
                minutes = sum(desk.ctx.minutes(l["pickup"]["placeId"], l["delivery"]["placeId"]) for l in other["legs"])
                load += max(1, (minutes + 299) // 300)
        if load + max(1, (road + 299) // 300) > max(3, len(drivers) // 3):
            return {}
        # Three nearby qualified drivers must have time to reach the first pickup, after allowing
        # four hours for booking/rebooking. Their actual working days are hidden, so this is a gate,
        # not a claim that those drivers are available.
        commute = sorted(desk.ctx.minutes(d["homePlaceId"], first["placeId"]) for d in drivers)[2]
        kept = {}
        for option in request["options"]:
            kind, deadline = option["kind"], option["deadline"]
            if kind not in prices:
                continue
            at = max(desk.now, request["respondBy"]) + 240 + commute
            for i, leg in enumerate(legs):
                if i:
                    at += desk.ctx.minutes(legs[i - 1]["delivery"]["placeId"], leg["pickup"]["placeId"])
                # The old car is collected in the same visit as delivery of the new one.
                paired = i > 0 and leg["pickup"]["placeId"] == legs[i - 1]["delivery"]["placeId"]
                at += 30 if plates else 0
                at = self.open_at(leg["pickup"], at, deadline, pickup=True, paired=paired)
                car = leg["car"]
                charging = car["electric"] and car["chargePercent"] is not None and car["chargePercent"] < 30
                charging &= desk.ctx.km(leg["pickup"]["placeId"], leg["delivery"]["placeId"]) > 200
                at += drives[i] + (40 if charging else 0)
                at = self.open_at(leg["delivery"], at, deadline, pickup=False)
            if at <= deadline - 60:
                kept[kind] = round(prices[kind] * self.long_markup) if long else prices[kind]
        return kept

    @staticmethod
    def open_at(place: dict[str, Any], at: int, deadline: int, pickup: bool, paired: bool = False) -> int:
        """Earliest visit inside stated hours and this option's windows, with a private-slot buffer."""
        start = place["window"]["from"]
        end = min(deadline, place["window"]["to"]) if pickup else deadline
        if place["privateAddress"]:
            end = deadline if paired else min(end, place["window"]["to"] - (90 if pickup else 0))
        at = max(at, start)
        hours = place["hours"]
        if hours:
            for day in range(at // 1440, end // 1440 + 1):
                weekday = day % 7
                opened = hours if weekday in hours["weekdays"] else hours["saturday"] if weekday == 5 else None
                if opened and weekday != 6:
                    candidate = max(at, day * 1440 + opened["opens"])
                    if candidate <= min(end, day * 1440 + opened["closes"]):
                        return candidate
            return 10**9
        return at if at <= end else 10**9

    def admit(self, request: dict[str, Any], prices: dict[str, int], desk: "Desk") -> dict[str, int]:
        from .quote import decline

        self.pending = {rid: r for rid, r in self.pending.items() if r["respondBy"] > desk.now}
        brake = self.braking(desk)
        max_drive, min_drivers = (min(self.max_drive, self.brake_drive), max(self.min_drivers, self.brake_drivers)) if brake else (self.max_drive, self.min_drivers)
        reachable = all(
            desk.ctx.minutes(leg["pickup"]["placeId"], leg["delivery"]["placeId"]) <= max_drive
            and self.drivers_near(leg["pickup"]["placeId"], desk) >= min_drivers
            for leg in request["legs"])
        same_day = not brake and (self.same_day or (self.future_same_day and self.future_ready(request)))
        kept = {kind: cents for kind, cents in prices.items() if same_day or kind != "same_day"} if reachable else {}
        legs = request["legs"]
        # thin_drivers: a leg of two hours or more from a pickup with fewer drivers near it is offered with
        # three days only; on base@f5a6b3b such legs were late 11.8% of the time on next_day, 0% on three days.
        # thin_both: instead, a leg of any length with that few drivers near both ends (12.5% late, €17 an order).
        def thin(place: str) -> bool:
            return self.drivers_near(place, desk) < self.thin_drivers
        if self.thin_drivers and any(thin(leg["pickup"]["placeId"]) and (
                thin(leg["delivery"]["placeId"]) if self.thin_both
                else desk.ctx.minutes(leg["pickup"]["placeId"], leg["delivery"]["placeId"]) >= 120) for leg in legs):
            kept = {kind: cents for kind, cents in kept.items() if kind == "within_3_days"}
        # no_private / no_trade_ins: these classes earn about nothing at the quoter's prices but are late
        # far more often, and a late order halves its dealer's trust count. With private_slots as well, a private
        # request is quoted only when it passes the expansion gate.
        if self.no_trade_ins and len(legs) > 1:
            return decline(request)
        if self.no_private and len(legs) == 1 and any(legs[0][end]["privateAddress"] for end in ("pickup", "delivery")):
            kept = {}
        if not kept and self.expanding and not brake:
            kept = self.expansion_options(request, prices, desk)
        if kept and self.expanding:
            self.pending[request["id"]] = request
        return kept or decline(request)
