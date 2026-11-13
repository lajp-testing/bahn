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

    def __init__(self, limit: int = 15):
        self.limit = limit
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
        if not later or unbooked + len(self.pending) >= self.limit:
            return decline(request)
        self.pending[request["id"]] = request["respondBy"]
        return later
