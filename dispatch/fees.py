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
                 urgent_open: float = 1.5, urgent_step: float = 0.25, urgent_every: int = 30, urgent_steps: int = 5,
                 night: bool = False, sleep: int = 23, wake: int = 7):
        self.open, self.step, self.every, self.steps = open, step, every, steps
        self.urgent_open, self.urgent_step, self.urgent_every, self.urgent_steps = urgent_open, urgent_step, urgent_every, urgent_steps
        # night=true: a normal schedule climbs only while drivers read, from `wake` to `sleep` o'clock. Without it a
        # gig posted in the afternoon reaches its top fee overnight and the first drivers up book it there.
        self.night, self.sleep, self.wake = night, sleep * HOUR, wake * HOUR

    def awake(self, start: int, minutes: int) -> int:
        """The minute `minutes` of reading time after `start`, skipping the nights."""
        t = start
        while True:
            day, clock = divmod(t, 24 * HOUR)
            if clock < self.wake:
                t = day * 24 * HOUR + self.wake
            elif clock >= self.sleep:
                t = (day + 1) * 24 * HOUR + self.wake
            elif minutes < self.sleep - clock:
                return t + minutes
            else:
                minutes -= self.sleep - clock
                t = (day + 1) * 24 * HOUR + self.wake

    def schedule(self, order: dict[str, Any], cars: int, urgent: bool, desk: "Desk") -> list[dict[str, int]]:
        """The schedule for `cars` of the order's cars, starting at `desk.now`."""
        fee = desk.requests[order["id"]]["referenceFeeCents"] * cars / len(order["legs"])
        first, step, every, steps = (self.urgent_open, self.urgent_step, self.urgent_every, self.urgent_steps) if urgent else (self.open, self.step, self.every, self.steps)
        at = (lambda k: desk.now if k == 0 else self.awake(desk.now, k * every)) if self.night and not urgent else (lambda k: desk.now + k * every)
        # int(x + 0.5) rounds halves up, as the kit's starters do.
        return [{"at": at(k), "feeCents": max(1, int(fee * (first + k * step) + 0.5))} for k in range(1 if desk.level == 1 else steps)]


class DensityFees(Fees):
    """The fee schedule by where drivers live near the delivery (the alternative-strategies thread's finding).

    Where at least `dense` drivers live within `dense_km` of every delivery, a gig that nobody books today books
    tomorrow morning at the opening fee, so the fee stays flat at `open` until the deadline warning. Elsewhere it
    climbs slowly: `open`, then `far_1` after `far_1_at` minutes and `far_2` after `far_2_at`. The deadline warning
    brings the urgent schedule everywhere."""

    def __init__(self, dense: int = 20, dense_km: float = 30.0, far_1: float = 1.15, far_1_at: int = 5 * HOUR,
                 far_2: float = 1.3, far_2_at: int = 8 * HOUR, **base):
        super().__init__(**base)
        self.dense, self.dense_km = dense, dense_km
        self.far = [(0, self.open), (far_1_at, far_1), (far_2_at, far_2)]
        self._near: dict[str, int] = {}

    def drivers_near(self, place_id: str, desk: "Desk") -> int:
        if place_id not in self._near:
            homes = [driver["homePlaceId"] for driver in desk.ctx.roster]
            self._near[place_id] = sum(1 for home in homes if desk.ctx.straight_km(place_id, home) <= self.dense_km)
        return self._near[place_id]

    def schedule(self, order: dict[str, Any], cars: int, urgent: bool, desk: "Desk") -> list[dict[str, int]]:
        if urgent or desk.level == 1:
            return super().schedule(order, cars, urgent, desk)
        fee = desk.requests[order["id"]]["referenceFeeCents"] * cars / len(order["legs"])
        dense = all(self.drivers_near(leg["delivery"]["placeId"], desk) >= self.dense for leg in order["legs"])
        plan = self.far[:1] if dense else self.far
        return [{"at": desk.now + after, "feeCents": max(1, int(fee * factor + 0.5))} for after, factor in plan]
