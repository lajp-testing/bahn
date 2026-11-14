"""The fees: the fee schedule of a gig. Owned by track 3 (fees and drivers)."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .parts import Part

if TYPE_CHECKING:
    from .desk import Desk

HOUR = 60


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

    def expected(self, request: dict[str, Any], desk: "Desk") -> int:
        """Expected total driver fees, calibrated to saved low20 orders."""
        features = self._cost_features(request, desk)
        multiple = 0.966 + sum(c for c, active in zip((0.076, 0.090, 0.213, 0.331), features) if active)
        return max(1, round(request["referenceFeeCents"] * multiple))

    def late_risk(self, request: dict[str, Any], desk: "Desk") -> float:
        """Empirical late share under low20; clipped additive group model."""
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
                 quiet_from: int = 0, quiet_to: int = 7 * HOUR, **kwargs: Any):
        super().__init__(**kwargs)
        # `quiet_from` > 0: the fee does not rise from this minute of the day until `quiet_to` the next morning.
        # Few drivers look at the app at night, so a raise then pays the morning's first driver more for nothing.
        self.quiet_from, self.quiet_to = int(quiet_from), int(quiet_to)
        self.buffer, self.rise, self.interval, self.cap = buffer, rise, interval, cap
        self.deadline_margin, self.max_raises, self.hold_until = deadline_margin, max_raises, hold_until
        self.rescue_fraction = rescue_fraction

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
        count = min(self.max_raises, max(0, int((self.cap - first) / self.rise + 0.999999)))
        interval = self.interval
        if self.deadline_margin and count:
            interval = max(1, min(interval, (order["lastPickupAt"] - desk.now - self.deadline_margin) // count))
        return [{"at": self.after(desk.now + (max(0, order["lastPickupAt"] - desk.now - self.hold_until) if k and self.hold_until else 0), k * interval), "feeCents": max(1, int(typical * min(self.cap, first + k * self.rise) + 0.5))} for k in range(1 if desk.level == 1 else count + 1)]
