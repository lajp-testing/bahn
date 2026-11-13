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


class LimitedIntake(Intake):
    """Limit unbooked orders, including quotes awaiting a dealer decision."""

    def __init__(self, limit: int = 15, private: bool = False, slack: int = 0, queue_price: bool = False):
        self.limit, self.private, self.slack = limit, private, slack  # `private`: take requests with a private address
        self.queue_price = queue_price
        self.pending: dict[str, int] = {}

    def admit(self, request: dict[str, Any], prices: dict[str, int], desk: "Desk") -> dict[str, int]:
        from .quote import decline

        self.pending = {key: end for key, end in self.pending.items() if end > desk.now}
        unbooked = sum(
            1 for order in desk.orders.values()
            if any(at is None for at in order["deliveredAt"])
            and (not desk.gigs_of(order["id"]) or any(gig not in desk.booked for gig in desk.gigs_of(order["id"])))
        )
        later = {kind: price for kind, price in prices.items() if kind != "same_day"}
        notes = desk.parts.notes
        if self.slack and hasattr(notes, "earliest_pickup") and hasattr(notes, "latest_delivery"):
            leg = request["legs"][0]
            drive = desk.ctx.minutes(leg["pickup"]["placeId"], leg["delivery"]["placeId"])
            start = max(desk.now, notes.earliest_pickup(request))
            later = {o["kind"]: prices[o["kind"]] for o in request["options"]
                     if o["kind"] in prices and notes.latest_delivery(request, o["deadline"]) - start - drive >= self.slack}
        if not self.private and any(leg[side]["privateAddress"] for leg in request["legs"] for side in ("pickup", "delivery")):
            return decline(request)
        if not later or unbooked + len(self.pending) >= self.limit:
            return decline(request)
        if self.queue_price:
            factor = 0.9 + 0.2 * (unbooked + len(self.pending)) / self.limit
            later = {kind: round(price * factor) for kind, price in later.items()}
        self.pending[request["id"]] = request["respondBy"]
        return later
