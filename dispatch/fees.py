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

    def schedule(self, order: dict[str, Any], cars: int, urgent: bool, desk: "Desk") -> list[dict[str, int]]:
        """The schedule for `cars` of the order's cars, starting at `desk.now`."""
        fee = desk.requests[order["id"]]["referenceFeeCents"] * cars / len(order["legs"])
        first, step, every, steps = (self.urgent_open, self.urgent_step, self.urgent_every, self.urgent_steps) if urgent else (self.open, self.step, self.every, self.steps)
        # int(x + 0.5) rounds halves up, as the kit's starters do.
        return [{"at": desk.now + k * every, "feeCents": max(1, int(fee * (first + k * step) + 0.5))} for k in range(1 if desk.level == 1 else steps)]


class MeasuredFees(Fees):
    """Density-based opening with a configurable early rise."""

    def __init__(self, buffer: float = 0.15, rise: float = 0.1, interval: int = 20,
                 cap: float = 1.5, deadline_margin: int = 0, max_raises: int = 47, **kwargs: Any):
        super().__init__(**kwargs)
        self.buffer, self.rise, self.interval, self.cap = buffer, rise, interval, cap
        self.deadline_margin, self.max_raises = deadline_margin, max_raises

    def schedule(self, order: dict[str, Any], cars: int, urgent: bool, desk: "Desk") -> list[dict[str, int]]:
        if urgent:
            return super().schedule(order, cars, urgent, desk)
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
        return [{"at": desk.now + k * interval, "feeCents": max(1, int(typical * min(self.cap, first + k * self.rise) + 0.5))} for k in range(1 if desk.level == 1 else count + 1)]
