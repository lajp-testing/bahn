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
                 brake_drivers: int = 10, brake_drive: int = 180):
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

    def observe(self, event: dict[str, Any], desk: "Desk", replay: bool) -> None:
        kind = event["kind"]
        if kind == "order_won":
            self.won.add(event["order"]["id"])
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

    def admit(self, request: dict[str, Any], prices: dict[str, int], desk: "Desk") -> dict[str, int]:
        from .quote import decline

        brake = self.braking(desk)
        max_drive, min_drivers = (min(self.max_drive, self.brake_drive), max(self.min_drivers, self.brake_drivers)) if brake else (self.max_drive, self.min_drivers)
        reachable = all(
            desk.ctx.minutes(leg["pickup"]["placeId"], leg["delivery"]["placeId"]) <= max_drive
            and self.drivers_near(leg["pickup"]["placeId"], desk) >= min_drivers
            for leg in request["legs"])
        same_day = not brake and (self.same_day or (self.future_same_day and self.future_ready(request)))
        kept = {kind: cents for kind, cents in prices.items() if same_day or kind != "same_day"} if reachable else {}
        return kept or decline(request)
