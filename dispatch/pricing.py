"""The quoter: the price that earns the most, for the level this week's dealers accept.

A dealer buys from us when our price is under a switching price that we cannot see. Scans of whole
weeks (tracks/t2) show two things about it, as a multiple of the list price: its level moves from
day to day and from week to week (day means from 1.1 to 1.7), and around that level requests are
spread widely (a standard deviation of 0.2 to 0.35).

So the quoter keeps one number, the level, and a fixed spread. Together they give the chance to win
at any price. For each option it quotes the price that maximises (price - cost) x chance. After each
dealer's decision the level moves a step: up after a win, down after a loss, by more when the result
was a surprise. The steps are larger for the first decisions of a day, because the level is new then.

The cost is what the car costs us to move: a multiple of the typical fee, plus a charge that rises
as the queue of orders without a driver fills. A full queue makes every car dearer for us, so prices
rise before the intake has to decline.
"""
from __future__ import annotations

import math
from typing import TYPE_CHECKING, Any

from .parts import Part

if TYPE_CHECKING:
    from .desk import Desk

DAY = 24 * 60


class ProfitQuoter(Part):
    wake_on = ["order_lost"]  # a loss moves the level too: hear of it at once

    def __init__(self, start: float = 1.4, spread: float = 0.2, step: float = 0.06, boost: float = 3.0, cost: float = 1.2,
                 queue: float = 0.0, limit: int = 15, low: float = 0.9, high: float = 2.6):
        self.level, self.spread, self.step, self.boost = start, spread, step, boost
        self.cost, self.queue, self.limit, self.low, self.high = cost, queue, limit, low, high
        self.sent: dict[str, dict[str, float]] = {}  # request -> option -> the price we sent, as a multiple of the list price
        self.day, self.seen_today = -1, 0

    def chance(self, ratio: float) -> float:
        """The chance that a dealer takes a price of `ratio` times the list price."""
        return 1 / (1 + math.exp(max(-40.0, min(40.0, (ratio - self.level) / self.spread))))

    def waiting(self, desk: "Desk") -> float:
        """How full the queue of orders without a booked driver is, from 0 to 1."""
        count = sum(1 for order in desk.orders.values() if any(at is None for at in order["deliveredAt"])
                    and (not desk.gigs_of(order["id"]) or any(gig not in desk.booked for gig in desk.gigs_of(order["id"]))))
        return min(1.0, count / self.limit)

    def prices(self, request: dict[str, Any], desk: "Desk") -> dict[str, int]:
        charge = self.queue * self.waiting(desk) ** 2
        prices = {}
        for option in request["options"]:
            cost = self.cost * request["referenceFeeCents"] / option["listPriceCents"] + charge  # in list prices
            best = max((cost + 0.02 + 0.01 * i for i in range(220)), key=lambda ratio: (ratio - cost) * self.chance(ratio))
            prices[option["kind"]] = round(option["listPriceCents"] * best)
        return prices

    def result(self, action: dict[str, Any], result: dict[str, Any], desk: "Desk") -> None:
        """Remembers the prices that went out: the intake may have changed or declined them."""
        request = desk.requests.get(action.get("requestId", ""))
        if action["type"] == "quote" and result.get("ok") and request is not None:
            lists = {option["kind"]: option["listPriceCents"] for option in request["options"]}
            self.sent[request["id"]] = {kind: cents / lists[kind] for kind, cents in action["prices"].items() if kind in lists}

    def observe(self, event: dict[str, Any], desk: "Desk", replay: bool) -> None:
        if event["kind"] not in ("order_won", "order_lost"):
            return
        won = event["kind"] == "order_won"
        sent = self.sent.pop(event["order"]["id"] if won else event["requestId"], None)
        if not sent:
            return
        # A win shows the taken option's price was low enough; a loss shows even the lowest one was too high.
        ratio = sent.get(event["order"]["option"], min(sent.values())) if won else min(sent.values())
        if ratio > 4:
            return  # the intake declined this request: its loss says nothing about the level
        if event["at"] // DAY != self.day:
            self.day, self.seen_today = event["at"] // DAY, 0
        step = self.step * max(1.0, self.boost / math.sqrt(1 + self.seen_today / 3))
        self.seen_today += 1
        self.level = min(self.high, max(self.low, self.level + step * ((1.0 if won else 0.0) - self.chance(ratio))))
