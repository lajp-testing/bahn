"""The quoter: the price of each option of a request. Owned by track 2 (quotes)."""
from __future__ import annotations

import math
from typing import TYPE_CHECKING, Any, Callable, Optional

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


class DialQuoter(Quoter):
    """Prices each request at the markup with the best expected margin, and learns the week's price level.

    A dealer takes a quote whose markup over list is under a limit that the dealer does not tell. The 1.4, 1.5
    and 1.6 dev weeks put the limit of a request at about `level` (the dial), times an effect of the request:
    higher when the dealer does not offer `same_day`, for a higher list price, and by up to 25% for a dealer
    with 25 on-time orders. Around that the limits scatter with `scale` (a logistic in the log of the markup).

    The cost of an order is about `cost_next` typical fees, or `cost_same` when the dealer also offers
    `same_day` (such a car is ready today, so its gig has longer to find a driver at the opening fee).

    The quoter asks for the markup `m` that makes `(m x list - cost + ladder) x chance(m)` largest. `ladder` is
    what one more on-time order is worth in the dealer's later prices; it falls to nothing by Friday night.
    After each answer the dial moves by `gain x (won - chance)`: up after a win, down after a loss, so that
    it follows a week, a day or a price war that the dev weeks did not have. `dealer_gain` does the same
    for one dealer. `admit` is the intake's decision: a request that the intake declines teaches nothing."""

    def __init__(self, level: float = 1.33, scale: float = 0.09, gain: float = 0.03, dealer_gain: float = 0.0,
                 no_same_day: float = 0.094, by_list: float = 0.12, by_trust: float = 0.233,
                 cost_next: float = 1.13, cost_same: float = 1.01, ladder: float = 0.0,
                 floor: float = 1.1, ceiling: float = 2.4,
                 admit: Optional[Callable[[dict[str, Any], dict[str, int], "Desk"], dict[str, int]]] = None):
        super().__init__(options="all")
        self.dial, self.scale, self.gain, self.dealer_gain = math.log(level), scale, gain, dealer_gain
        self.no_same_day, self.by_list, self.by_trust = no_same_day, by_list, by_trust
        self.cost_next, self.cost_same, self.ladder = cost_next, cost_same, ladder
        self.floor, self.ceiling, self.admit = floor, ceiling, admit
        self.dealer_dial: dict[str, float] = {}  # dealer id -> its own offset to the dial
        self.trust: dict[str, int] = {}  # dealer id -> on-time orders, halved by a late one, at most 25
        self.quoted: dict[str, tuple[float, float, str, dict[str, int]]] = {}  # request id -> (markup, effect, dealer, prices)
        self.dealer_of: dict[str, str] = {}  # order id -> dealer id
        self.on_time: set[str] = set()  # the delivered orders counted as on time
        self.late: set[str] = set()

    # --- the model ---

    def effect(self, request: dict[str, Any]) -> float:
        """The log of the request's limit against the dial."""
        kinds = [option["kind"] for option in request["options"]]
        dealer = request["dealerId"]
        return ((0.0 if "same_day" in kinds else self.no_same_day) + self.by_list * math.log(basis(request)["listPriceCents"] / 6000)
                + self.by_trust * self.trust.get(dealer, 0) / 25 + self.dealer_dial.get(dealer, 0.0))

    def chance(self, markup: float, effect: float) -> float:
        return 1 / (1 + math.exp(-(self.dial + effect - math.log(markup)) / self.scale))

    def cost(self, request: dict[str, Any]) -> float:
        same_day = any(option["kind"] == "same_day" for option in request["options"])
        return request["referenceFeeCents"] * len(request["legs"]) * (self.cost_same if same_day else self.cost_next)

    def ladder_value(self, request: dict[str, Any], desk: "Desk") -> float:
        """What one more on-time order for this dealer is worth, in cents: `ladder` on Monday morning, nothing
        from Friday night or once the dealer has 25."""
        if self.trust.get(request["dealerId"], 0) >= 25:
            return 0.0
        return self.ladder * max(0.0, 1 - desk.now / (5 * 1440))

    def best_markup(self, request: dict[str, Any], desk: "Desk") -> float:
        effect, cost, extra = self.effect(request), self.cost(request), self.ladder_value(request, desk)
        list_price = basis(request)["listPriceCents"]
        steps = range(round(self.floor * 100), round(self.ceiling * 100) + 1)
        best = max(steps, key=lambda step: (step / 100 * list_price - cost + extra) * self.chance(step / 100, effect))
        # A request that costs more than the ceiling pays: quote above the cost anyway, and lose it.
        return max(best / 100, 1.05 * (cost - extra) / list_price)

    # --- quotes and what their answers teach ---

    def prices(self, request: dict[str, Any], desk: "Desk") -> dict[str, int]:
        if request["id"] not in self.quoted:  # a quote stays as it is: a desk that restarts quotes the same again
            markup = self.best_markup(request, desk)
            prices = {option["kind"]: round(option["listPriceCents"] * markup) for option in request["options"]}
            sent = self.admit(request, prices, desk) if self.admit else prices
            learns = any(sent.get(kind) == cents for kind, cents in prices.items())
            self.quoted[request["id"]] = (markup if learns else 0.0, self.effect(request) - self.dealer_dial.get(request["dealerId"], 0.0), request["dealerId"], prices)
        return self.quoted[request["id"]][3]

    def learn(self, request_id: str, won: bool) -> None:
        markup, effect, dealer, _ = self.quoted.get(request_id, (0.0, 0.0, "", {}))
        if markup <= 0:
            return
        surprise = (1.0 if won else 0.0) - self.chance(markup, effect + self.dealer_dial.get(dealer, 0.0))
        self.dial += self.gain * surprise
        if self.dealer_gain:
            self.dealer_dial[dealer] = self.dealer_dial.get(dealer, 0.0) + self.dealer_gain * surprise

    def observe(self, event: dict[str, Any], desk: "Desk", replay: bool) -> None:
        kind = event["kind"]
        if kind == "price_request" and replay:
            self.prices(event["request"], desk)
        elif kind == "order_won":
            self.dealer_of[event["order"]["id"]] = event["order"]["dealerId"]
            self.learn(event["order"]["id"], True)
        elif kind == "order_lost":
            self.learn(event["requestId"], False)
        elif kind == "ledger" and event["line"].get("orderId") in self.dealer_of:
            self.account(event["line"]["kind"], event["line"]["orderId"])

    def account(self, line: str, order_id: str) -> None:
        """The dealer's trust: one up for an order delivered on time, halved by a late one."""
        dealer = self.dealer_of[order_id]
        count = self.trust.get(dealer, 0)
        if line == "revenue" and order_id not in self.late and order_id not in self.on_time:
            self.on_time.add(order_id)
            self.trust[dealer] = min(25, count + 1)
        elif line in ("late_refund", "undelivered_penalty") and order_id not in self.late:
            self.late.add(order_id)
            self.trust[dealer] = (count - (1 if order_id in self.on_time else 0)) // 2


def basis(request: dict[str, Any]) -> dict[str, Any]:
    """The option whose list price the quoter reasons with: the first that is not `same_day`."""
    return next((option for option in request["options"] if option["kind"] != "same_day"), request["options"][0])
