"""The fees: the fee schedule of a gig. Owned by track 3 (fees and drivers)."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .parts import Part

if TYPE_CHECKING:
    from .desk import Desk

HOUR = 60
# Model 2, fitted on the mainline's own weeks (tracks/t3/cost.py): an additive yes/no model on what
# the desk knows when the request arrives. The reference order has its pickup window opening 12 to 24
# hours away, arrives before noon, has no private address, a lane under 500 km and 30 or more drivers
# living near each end.
MODEL2 = ("lead<=3", "lead3-12", "lead>=24", "hour>=15", "hour12-15", "private", "km>=500", "pickup<30", "delivery<10")
MODEL2_EXPECTED = (0.9090, 0.2041, 0.1343, 0.0323, 0.0368, 0.0593, 0.2642, 0.1413, 0.0232, 0.0447)
MODEL2_LATE = (-0.0075, 0.0314, 0.0013, 0.0041, 0.0137, -0.0045, 0.2373, 0.0823, 0.0048, 0.0218)


class Fees(Part):
    """The starter's fees, as multiples of the request's typical fee.

    Normal: `open` at once, then `step` more every `every` minutes, `steps` fees in all (1.0, 1.1 … 1.5).
    Urgent, from the order's deadline warning: `urgent_open` at once, then `urgent_step` more every
    `urgent_every` minutes, `urgent_steps` fees in all (1.5, 1.75 … 2.5). Level 1 takes one fee only."""

    def __init__(self, open: float = 1.0, step: float = 0.1, every: int = HOUR, steps: int = 6,
                 urgent_open: float = 1.5, urgent_step: float = 0.25, urgent_every: int = 30, urgent_steps: int = 5):
        self.open, self.step, self.every, self.steps = open, step, every, steps
        self.urgent_open, self.urgent_step, self.urgent_every, self.urgent_steps = urgent_open, urgent_step, urgent_every, urgent_steps

    def estimate(self, request: dict[str, Any], desk: "Desk") -> int:
        """Experimental two-hour retained-booking fee, not a full delivery cost.

        Fork samples suggest a premium for private-address orders; trade-ins and later
        drops are not calibrated by this estimate.
        """
        private = any(leg[side].get("privateAddress") for leg in request["legs"] for side in ("pickup", "delivery"))
        multiple = 0.7 + (0.25 if private else 0)
        return max(1, int(request["referenceFeeCents"] * multiple + 0.5))

    def _cost_features(self, request: dict[str, Any], desk: "Desk") -> tuple[bool, bool, bool, bool]:
        leg = request["legs"][0]
        pickup, delivery = leg["pickup"]["placeId"], leg["delivery"]["placeId"]
        near = lambda place: sum(desk.ctx.straight_km(place, d["homePlaceId"]) <= 30 for d in desk.ctx.roster)
        private = any(leg[side].get("privateAddress") for leg in request["legs"] for side in ("pickup", "delivery"))
        return near(pickup) < 30, near(delivery) < 10, desk.ctx.km(pickup, delivery) >= 500, private

    def _model2_features(self, request: dict[str, Any], desk: "Desk") -> tuple[bool, ...]:
        """The nine yes/no facts of model 2, all known when the request arrives (no option facts:
        the quoter asks for the fee once per request, before it looks at the options)."""
        leg = request["legs"][0]
        pickup, delivery = leg["pickup"]["placeId"], leg["delivery"]["placeId"]
        near = lambda place: sum(desk.ctx.straight_km(place, d["homePlaceId"]) <= 30 for d in desk.ctx.roster)
        lead = max(0, leg["pickup"]["window"]["from"] - request["arrivedAt"]) / HOUR
        hour = request["arrivedAt"] % (24 * HOUR) / HOUR
        private = any(l[side].get("privateAddress") for l in request["legs"] for side in ("pickup", "delivery"))
        return (lead <= 3, 3 < lead <= 12, lead >= 24, hour >= 15, 12 <= hour < 15, private,
                desk.ctx.km(pickup, delivery) >= 500, near(pickup) < 30, near(delivery) < 10)

    def expected(self, request: dict[str, Any], desk: "Desk") -> int:
        """Expected total driver fees, as a share of the typical fee."""
        if getattr(self, "model", 1) == 2:
            multiple = MODEL2_EXPECTED[0] + sum(c for c, active in zip(MODEL2_EXPECTED[1:], self._model2_features(request, desk)) if active)
            return max(1, round(request["referenceFeeCents"] * multiple))
        features = self._cost_features(request, desk)
        multiple = 0.966 + sum(c for c, active in zip((0.076, 0.090, 0.213, 0.331), features) if active)
        return max(1, round(request["referenceFeeCents"] * multiple))

    def late_risk(self, request: dict[str, Any], desk: "Desk") -> float:
        """Empirical late share; clipped additive group model."""
        if getattr(self, "model", 1) == 2:
            risk = MODEL2_LATE[0] + sum(c for c, active in zip(MODEL2_LATE[1:], self._model2_features(request, desk)) if active)
            return min(1.0, max(0.0, risk))
        features = self._cost_features(request, desk)
        return min(1.0, max(0.0, -0.0017 + sum(c for c, active in zip((0.0269, -0.0130, 0.0855, 0.1676), features) if active)))

    def schedule(self, order: dict[str, Any], cars: int, urgent: bool, desk: "Desk") -> list[dict[str, int]]:
        """The schedule for `cars` of the order's cars, starting at `desk.now`."""
        fee = desk.requests[order["id"]]["referenceFeeCents"] * cars / len(order["legs"])
        first, step, every, steps = (self.urgent_open, self.urgent_step, self.urgent_every, self.urgent_steps) if urgent else (self.open, self.step, self.every, self.steps)
        # int(x + 0.5) rounds halves up, as the kit's starters do.
        return [{"at": desk.now + k * every, "feeCents": max(1, int(fee * (first + k * step) + 0.5))} for k in range(1 if desk.level == 1 else steps)]


class MeasuredFees(Fees):
    """Density-based opening with a configurable early rise."""

    def __init__(self, buffer: float = 0.15, rise: float = 0.1, interval: int = 20,
                 cap: float = 1.5, deadline_margin: int = 0, max_raises: int = 47, hold_until: int = 0, rescue_fraction: float = 0,
                 quiet_from: int = 0, quiet_to: int = 7 * HOUR, model: int = 1, far_open: float = 0, soon_open: float = 0, early: int = 0, backload: int = 0, rescue: int = 0, **kwargs: Any):
        super().__init__(**kwargs)
        # `early` > 0: an order without a driver goes to the urgent fees when this many minutes of the drivers' day are
        # left before its last pickup. The world's own warning comes 3 hours before, which is late for a driver to get there.
        self.early = int(early)
        # `backload` > 0: the gig waits at its opening fee while it has time, and the ladder starts as late as it can
        # while still reaching the cap `backload` minutes of the drivers' day before the last pickup. Off by default.
        self.backload = int(backload)
        # `rescue` > 0: a single car still without a driver when fewer than this many minutes of the drivers' day are left
        # before its last pickup goes at once to the top of its normal ladder (the cap), so it books while a driver can still
        # reach it. Off by default. Cars past their last pickup are left to the desk's `calm`.
        self.rescue = int(rescue)
        self.model = model  # 2: the refitted expected fee and late risk (MODEL2 above)
        # `quiet_from` > 0: the fee does not rise from this minute of the day until `quiet_to` the next morning.
        # Few drivers look at the app at night, so a raise then pays the morning's first driver more for nothing.
        self.quiet_from, self.quiet_to = int(quiet_from), int(quiet_to)
        self.buffer, self.rise, self.interval, self.cap = buffer, rise, interval, cap
        self.deadline_margin, self.max_raises, self.hold_until = deadline_margin, max_raises, hold_until
        self.rescue_fraction = rescue_fraction
        # Where the gig opens: the far lead group books cheap and is almost never late, the ready-soon group after
        # 15:00 is dear and late-prone (the stint's cost table), so the opening moves before the rise begins.
        self.far_open, self.soon_open = far_open, soon_open

    def after(self, start: int, minutes: int) -> int:
        """The minute that is `minutes` of the drivers' day after `start`: the quiet hours do not count."""
        if not self.quiet_from:
            return start + minutes
        at = start
        while minutes > 0:
            minute = at % (24 * HOUR)
            if minute >= self.quiet_from:
                at += 24 * HOUR - minute + self.quiet_to
            elif minute < self.quiet_to:
                at += self.quiet_to - minute
            else:
                step = min(minutes, self.quiet_from - minute)
                at, minutes = at + step, minutes - step
        return at

    def before(self, end: int, minutes: int) -> int:
        """About the minute that is `minutes` of the drivers' day before `end` (in steps of 15 minutes)."""
        at = end - minutes
        while self.after(at, minutes) > end:
            at -= 15
        return at

    def urgent_from(self, order: dict[str, Any]) -> int:
        """The minute from which the order is urgent on the desk's own account: `early` minutes of the drivers' day before its last pickup."""
        return self.before(order["lastPickupAt"], self.early)

    def rescue_from(self, order: dict[str, Any]) -> int:
        """The minute from which a single car without a driver goes at the top of its ladder: `rescue` minutes of the drivers' day before its last pickup."""
        return self.before(order["lastPickupAt"], self.rescue)

    def rescuing(self, order: dict[str, Any], cars: int, now: int) -> bool:
        """Whether a gig of `cars` of the order's cars, posted or repriced at `now`, goes straight to the top of its ladder."""
        return bool(self.rescue) and cars == 1 and self.rescue_from(order) <= now < order["lastPickupAt"]

    def schedule(self, order: dict[str, Any], cars: int, urgent: bool, desk: "Desk") -> list[dict[str, int]]:
        if urgent:
            schedule = super().schedule(order, cars, urgent, desk)
            if self.rescue_fraction:
                cap = max(1, int(order["priceCents"] * self.rescue_fraction * cars / len(order["legs"])))
                for item in schedule:
                    item["feeCents"] = min(item["feeCents"], cap)
            return schedule
        request = desk.requests[order["id"]]
        typical = request["referenceFeeCents"] * cars / len(order["legs"])
        # Keep the tested opening rule independent of the experimental refit.
        pickup = request["legs"][0]["pickup"]["placeId"]
        nearby = sum(desk.ctx.straight_km(pickup, d["homePlaceId"]) <= 30 for d in desk.ctx.roster)
        estimate = int(request["referenceFeeCents"] * (0.6 + (0.15 if nearby < 30 else 0)) + 0.5)
        first = max(1, estimate) / request["referenceFeeCents"] + self.buffer
        if self.far_open or self.soon_open:
            lead = request["legs"][0]["pickup"]["window"]["from"] - desk.now
            if self.far_open and lead >= 12 * HOUR:
                first -= self.far_open
            if self.soon_open and lead <= 3 * HOUR and desk.now % (24 * HOUR) >= 15 * HOUR:
                first += self.soon_open
        count = min(self.max_raises, max(0, int((self.cap - first) / self.rise + 0.999999)))
        interval = self.interval
        if self.deadline_margin and count:
            interval = max(1, min(interval, (order["lastPickupAt"] - desk.now - self.deadline_margin) // count))
        start = desk.now
        if self.backload and count:
            start = order["lastPickupAt"] - self.backload - count * interval
            while start > desk.now and self.after(start, count * interval) > order["lastPickupAt"] - self.backload:
                start -= 15
            start = max(desk.now, start)
        if self.rescuing(order, cars, desk.now):  # little of the drivers' day is left: the top of the ladder at once
            return [{"at": desk.now, "feeCents": max(1, int(typical * max(self.cap, first) + 0.5))}]
        return [{"at": self.after(start + (max(0, order["lastPickupAt"] - desk.now - self.hold_until) if k and self.hold_until else 0), k * interval), "feeCents": max(1, int(typical * min(self.cap, first + k * self.rise) + 0.5))} for k in range(1 if desk.level == 1 else count + 1)]
