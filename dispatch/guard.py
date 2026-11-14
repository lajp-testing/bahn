"""The on-time governor: the week's own record decides how carefully we quote.

A team is ranked only when 90% of its orders arrive on time, so a week that is going badly must
stop buying risk: while the share of on-time orders among those already decided sits under `guard`,
every car costs more to move (`guard_car` times the cost tilt) and same-day speed goes unsold.
The share is read from the desk's own books, which are built from the events it already sees.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .desk import Desk


class Governor:
    """Watches the week's on-time share and reports whether the quoter should be careful."""

    MIN_ORDERS = 40  # the share means nothing before this many orders are decided

    def __init__(self, guard: float, guard_car: float = 1.1):
        self.guard, self.guard_car = guard, guard_car
        self.on = False  # hysteresis: once careful, only a share above `guard` + 0.01 turns it off

    def careful(self, desk: "Desk") -> bool:
        on_time = late = 0
        for order in desk.orders.values():
            times, deadline = order["deliveredAt"], order["deadline"]
            if any(at is not None and at > deadline for at in times) or (
                    any(at is None for at in times) and desk.now > deadline):
                late += 1  # a leg delivered after the deadline, or past it and still not delivered
            elif all(at is not None for at in times):
                on_time += 1
        decided = on_time + late
        if decided < self.MIN_ORDERS:
            self.on = False
            return False
        share = on_time / decided
        self.on = share <= self.guard + 0.01 if self.on else share < self.guard
        return self.on
