"""The clearing price: one price level for the week, which the week itself sets.

Drivers are scarce, so the desk can move only so many cars at once. The right price is the highest
one that still fills that capacity. The level is a multiple of the list price. After each dealer's
decision it moves a small step: up after a win, down after a loss. The steps are sized so that the
level settles where the share of quotes won equals a target, and the target follows the queue of
orders that wait for a driver: high when the queue is empty, low when it is full.

So a week with a dear competitor ends at a high level, a week with a cheap one at a low level, and
a full queue pushes the level up before the intake has to decline.
"""
from __future__ import annotations

import math
from typing import TYPE_CHECKING, Any

from .parts import Part

if TYPE_CHECKING:
    from .desk import Desk


class ClearingQuoter(Part):
    wake_on = ["order_lost"]  # a loss moves the level too: do not wait for the next request to hear of it

    def __init__(self, start: float = 1.45, step: float = 0.04, empty: float = 0.7, full: float = 0.15, limit: int = 15,
                 low: float = 1.0, high: float = 2.6, trust: float = 0.0):
        self.level, self.step, self.empty, self.full, self.limit = start, step, empty, full, limit
        self.low, self.high, self.trust = low, high, trust
        self.on_time: dict[str, int] = {}  # dealer -> orders delivered on time, as the dealer counts its trust
        self.late: set[str] = set()

    def prices(self, request: dict[str, Any], desk: "Desk") -> dict[str, int]:
        # A dealer accepts 1% more for each order we delivered to it on time, up to 25.
        bonus = 1 + self.trust * 0.01 * min(25, self.on_time.get(request["dealerId"], 0))
        return {option["kind"]: round(option["listPriceCents"] * self.level * bonus) for option in request["options"]}

    def target(self, desk: "Desk") -> float:
        """The share of quotes we want to win now: from `empty` with no order waiting to `full` at the limit."""
        waiting = sum(1 for order in desk.orders.values() if any(at is None for at in order["deliveredAt"])
                      and (not desk.gigs_of(order["id"]) or any(gig not in desk.booked for gig in desk.gigs_of(order["id"]))))
        fill = min(1.0, waiting / self.limit)
        return self.empty + (self.full - self.empty) * fill

    def observe(self, event: dict[str, Any], desk: "Desk", replay: bool) -> None:
        kind = event["kind"]
        if kind in ("order_won", "order_lost"):
            request_id = event["order"]["id"] if kind == "order_won" else event["requestId"]
            request = desk.requests.get(request_id)
            if request is None or self._declined(request, event):
                return
            target = self.target(desk)
            # Up by step x (1 - target) after a win, down by step x target after a loss: no drift when the win share is the target.
            move = self.step * ((1 - target) if kind == "order_won" else -target)
            self.level = min(self.high, max(self.low, self.level * math.exp(move)))
        elif kind == "ledger":
            line = event["line"]
            if line["kind"] == "late_refund" and line["orderId"]:
                self.late.add(line["orderId"])
            elif line["kind"] == "revenue" and line["orderId"] and line["orderId"] not in self.late:
                dealer = desk.requests.get(line["orderId"], {}).get("dealerId")
                if dealer:
                    self.on_time[dealer] = self.on_time.get(dealer, 0) + 1

    def _declined(self, request: dict[str, Any], event: dict[str, Any]) -> bool:
        """A loss on a request that the intake declined says nothing about the price."""
        return event["kind"] == "order_lost" and request["id"] in self.declined

    declined: set[str] = set()

    def result(self, action: dict[str, Any], result: dict[str, Any], desk: "Desk") -> None:
        if action["type"] != "quote":
            return
        request = desk.requests.get(action["requestId"])
        if request is None:
            return
        if self.declined is ClearingQuoter.declined:
            self.declined = set()
        # The intake declines with a price far above the list price.
        if min(action["prices"][option["kind"]] / option["listPriceCents"] for option in request["options"] if option["kind"] in action["prices"]) > 4:
            self.declined.add(request["id"])
