"""The quoter: the price of each option of a request. Owned by track 2 (quotes)."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .parts import Part

if TYPE_CHECKING:
    from .desk import Desk

DECLINE_FACTOR = 5  # a quote this many times the list price loses, and a lost quote costs nothing


def decline(request: dict[str, Any]) -> dict[str, int]:
    """A quote that loses: the way to decline a request without losing the dealer's goodwill."""
    first = request["options"][0]
    return {first["kind"]: first["listPriceCents"] * DECLINE_FACTOR}


class Quoter(Part):
    """The starter's quoter: a multiple of the list price. With `options="first"` it quotes the dealer's
    first option only, as the starter does; with `"all"`, every option."""

    def __init__(self, markup: float = 1.0, options: str = "first"):
        self.markup, self.options = markup, options

    def prices(self, request: dict[str, Any], desk: "Desk") -> dict[str, int]:
        offered = request["options"][:1] if self.options == "first" else request["options"]
        return {option["kind"]: round(option["listPriceCents"] * self.markup) for option in offered}


class LearningQuoter(Part):
    """Experimental shared logistic demand curve; learn approximately from accepted quotes."""

    wake_on = ["order_lost"]

    def __init__(self, cost_factor: float = 1.0):
        self.cost_factor = cost_factor
        self.midpoint = 1.45
        self.pending: dict[str, tuple[float, int]] = {}

    def prices(self, request: dict[str, Any], desk: "Desk") -> dict[str, int]:
        import math
        prices = {}
        for option in request["options"]:
            base = option["listPriceCents"]
            cost = self.cost_factor * request["referenceFeeCents"]
            candidates = range(80, 251)
            def value(n: int) -> float:
                m = n / 100
                probability = 1 / (1 + math.exp(max(-40, min(40, (m - self.midpoint) / .10))))
                return (base * m - cost) * probability
            best = max(candidates, key=value)
            prices[option["kind"]] = round(base * best / 100)
        return prices

    def result(self, action: dict[str, Any], result: dict[str, Any], desk: "Desk") -> None:
        if action["type"] != "quote" or not result.get("ok") :
            return
        request = desk.requests.get(action["requestId"])
        if not request:
            return
        ratios = [action["prices"][o["kind"]] / o["listPriceCents"]
                  for o in request["options"] if o["kind"] in action["prices"]]
        if ratios:
            self.pending[action["requestId"]] = (min(ratios), desk.now)

    def observe(self, event: dict[str, Any], desk: "Desk", replay: bool) -> None:
        import math
        if event["kind"] not in ("order_won", "order_lost"):
            return
        rid = event["order"]["id"] if event["kind"] == "order_won" else event["requestId"]
        observation = self.pending.pop(rid, None)
        if observation is None:
            return
        ratio, _ = observation
        probability = 1 / (1 + math.exp(max(-40, min(40, (ratio - self.midpoint) / .10))))
        self.midpoint = max(.8, min(2.2, self.midpoint + .02 * ((event["kind"] == "order_won") - probability)))
