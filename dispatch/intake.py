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

    def __init__(self, max_drive: int = 300, min_drivers: int = 3, near_km: float = 60.0, same_day: bool = False):
        self.max_drive, self.min_drivers, self.near_km, self.same_day = max_drive, min_drivers, near_km, same_day
        self._near: dict[str, int] = {}

    def drivers_near(self, place_id: str, desk: "Desk") -> int:
        if place_id not in self._near:
            homes = [driver["homePlaceId"] for driver in desk.ctx.roster]
            self._near[place_id] = sum(1 for home in homes if desk.ctx.straight_km(place_id, home) <= self.near_km)
        return self._near[place_id]

    def admit(self, request: dict[str, Any], prices: dict[str, int], desk: "Desk") -> dict[str, int]:
        from .quote import decline

        reachable = all(
            desk.ctx.minutes(leg["pickup"]["placeId"], leg["delivery"]["placeId"]) <= self.max_drive
            and self.drivers_near(leg["pickup"]["placeId"], desk) >= self.min_drivers
            for leg in request["legs"])
        kept = {kind: cents for kind, cents in prices.items() if self.same_day or kind != "same_day"} if reachable else {}
        return kept or decline(request)
