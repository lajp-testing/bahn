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

    def __init__(self, limit: int = 15, private: bool = False, slack: int = 0, queue_price: bool = False, win_price: bool = False, same_day_slack: int = -1, same_day_drivers: int = 0, morning_limit: int = 0, shortage_warnings: int = 0, shortage_drops: int = 0, late_floor: float = 0, afternoon_ready: int = 0, shortage_limit: int = 0):
        self.limit, self.private, self.slack = limit, private, slack  # `private`: take requests with a private address
        self.morning_limit = morning_limit
        self.shortage_warnings = shortage_warnings
        self.shortage_drops = shortage_drops
        self.late_floor = late_floor
        self.afternoon_ready = afternoon_ready
        self.shortage_limit = shortage_limit
        self.drops: list[int] = []
        self.warnings: list[int] = []
        self.same_day_slack = same_day_slack
        self.same_day_drivers = same_day_drivers
        self.queue_price = queue_price
        self.win_price = win_price
        self.quoted: set[str] = set()
        self.win_rate = 0.4
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
            nearby = sum(desk.ctx.straight_km(driver["homePlaceId"], leg["pickup"]["placeId"]) <= 30
                         for driver in desk.ctx.roster) if self.same_day_slack >= 0 else 0
            later = {o["kind"]: prices[o["kind"]] for o in request["options"]
                     if o["kind"] in prices and (
                         ((o["kind"] != "same_day" or self.same_day_slack < 0) and notes.latest_delivery(request, o["deadline"]) - start - drive >= self.slack)
                         or (o["kind"] == "same_day" and self.same_day_slack >= 0
                             and nearby >= self.same_day_drivers
                             and notes.latest_delivery(request, o["deadline"]) - start - drive >= self.same_day_slack))}
        if (self.afternoon_ready and desk.now % 1440 >= 900
                and hasattr(notes, "earliest_pickup")
                and notes.earliest_pickup(request) <= desk.now + self.afternoon_ready):
            return decline(request)
        late = sum(any(at is not None and at > order["deadline"] for at in order["deliveredAt"])
                   or (desk.now > order["deadline"] and any(at is None for at in order["deliveredAt"]))
                   for order in desk.orders.values())
        shortage = ((self.late_floor and len(desk.orders) >= 30 and late / len(desk.orders) >= self.late_floor)
                or (self.shortage_warnings and sum(at > desk.now - 360 for at in self.warnings) >= self.shortage_warnings)
                or (self.shortage_drops and sum(at > desk.now - 360 for at in self.drops) >= self.shortage_drops))
        if shortage:
            later = {kind: price for kind, price in later.items() if kind != "same_day"}
            if any(leg[side]["privateAddress"] for leg in request["legs"] for side in ("pickup", "delivery")):
                return decline(request)
        if not self.private and any(leg[side]["privateAddress"] for leg in request["legs"] for side in ("pickup", "delivery")):
            return decline(request)
        limit = self.morning_limit if self.morning_limit and desk.now % 1440 < 12 * 60 else self.limit
        if shortage and self.shortage_limit:
            limit = min(limit, self.shortage_limit)
        # A quote awaiting its dealer holds `pending_weight` of a place: about a third of them win.
        waiting = unbooked + getattr(self, "pending_weight", 1.0) * len(self.pending)
        if not later or waiting >= limit:
            return decline(request)
        if self.queue_price:
            load = waiting / self.limit
            factor = 0.9 + 0.2 * load
            if self.win_price:
                factor *= max(0.9, min(1.1, 1 + (self.win_rate - 0.4) * 0.25))
            later = {kind: round(price * factor) for kind, price in later.items()}
        self.pending[request["id"]] = request["respondBy"]
        return later

    def result(self, action: dict[str, Any], result: dict[str, Any], desk: "Desk") -> None:
        if self.win_price and action["type"] == "quote" and result.get("ok") and action["requestId"] in self.pending:
            self.quoted.add(action["requestId"])

    def observe(self, event: dict[str, Any], desk: "Desk", replay: bool) -> None:
        if event["kind"] == "gig_dropped":
            self.drops.append(event["at"])
        if event["kind"] == "deadline_close":
            self.warnings.append(event["at"])
        if event["kind"] not in ("order_won", "order_lost"):
            return
        rid = event["order"]["id"] if event["kind"] == "order_won" else event["requestId"]
        if rid in self.quoted:
            self.quoted.remove(rid)
            self.win_rate = 0.95 * self.win_rate + 0.05 * (event["kind"] == "order_won")
