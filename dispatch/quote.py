"""The quoter: the price of each option of a request. Owned by track 2 (quotes)."""
from __future__ import annotations

import math
from typing import TYPE_CHECKING, Any, Callable, Optional

from .parts import Part
from .places import DELIVERY, PICKUP

if TYPE_CHECKING:
    from .desk import Desk

HOUR, DAY = 60, 24 * 60
# What an order costs more, in typical fees, and the mean over 30 practice weeks' orders: for a private address, for a
# car that is ready on a later day, for each unit of log(typical fee / list price), for a premium car, for each unit
# of log(1 + drivers who live within 60 km of the delivery place), the same of the pickup place, and for each unit of
# log(road minutes / 120). Fitted on the dev weeks it explains 10% of the study weeks' cost. tracks/t2/fit8.py.
DETAIL = ((0.26, 0.08), (-0.16, 0.52), (-0.42, -0.07), (0.14, 0.05), (-0.04, 3.6), (-0.03, 4.9), (-0.06, 0.06))
NEAR_KM = 60.0
STRAIN = 0.06  # the share of won orders with a deadline warning or a late delivery, over the control's 30 weeks
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

    A dealer takes a quote whose markup over list is under a limit that the dealer does not tell. The dev weeks
    put the limit of a request at about `level` (the dial), times an effect of the request: higher when the
    dealer does not offer `same_day`, for a higher list price, and by `by_trust` percent for each on-time order
    that the dealer counts. Around that the limits scatter with `scale` (a logistic in the log of the markup).

    An order costs about `cost_next` typical fees, or `cost_same` when the dealer also offers `same_day` (such
    a car is ready today, so its gig has longer to find a driver at the opening fee). Both are above the fees
    paid: every order also makes the drivers scarcer for the others. `detail` adds what the practice weeks' orders cost
    more or less than that (`DETAIL`): a private address and a premium car are dearer; a car that is ready on a later
    day is cheaper, and so are a request whose typical fee is high for its list price, a longer drive, and a pickup
    or a delivery place with many drivers living near. `brake` reads how scarce this week's drivers
    are from the orders themselves: the cost rises by `brake` typical fees for each unit that the share of won
    orders with a deadline warning or a late delivery lies above a usual week's (`STRAIN`), and falls below it.

    The quoter asks for the markup `m` that makes `(m x list - cost + ladder) x chance(m)` largest. The ladder
    is what one more on-time order is worth in the dealer's later prices (`ladder_value`). After each answer
    the dial moves by `gain x (won - chance)`: up after a win, down after a loss, so it follows a week, a day
    or a region that the dev weeks did not have. `dealer_gain` does the same for one dealer, and `place_gain` for
    one pickup place: the part of the competitor's lane factor that is new in each world, and a day's outage around the
    place. `lanes` adds the part that is the same in every world, from `dispatch.places`: a dealer accepts about 10%
    less for a car delivered to Vantaa, and 12% more for one to Kotka, than the week's level says. `admit` is the
    intake's decision: a request that the intake declines teaches nothing.

    The price war is one working day on which every limit is lower by `war` (the dev weeks: 0.25 to 0.34). A dial
    that follows it down sells the next morning's orders too cheaply while it climbs back. So `war` makes the war a
    switch of the day: each answer moves its probability `at_war` by how much better the war explains it, the
    chance of a quote is the mix of the two days, and the dial learns only what the mix did not expect. Each
    morning starts with one chance in the working days left, and none once a war has been.

    The competitor's prices have a factor that is new each day, so yesterday's dial is a worse guess each morning
    than at the evening before. With `day_sd`, the spread of that factor in the log, the dial keeps its own doubt
    (a variance): each morning it returns to the mean of the days so far and doubts by the day factor, and each
    answer moves it by `doubt / scale` times the surprise, at least `gain`, and takes away the doubt that the
    answer settled. So the first answers of a day move the dial far, and the later ones little.

    With `same_up`, a `same_day` option beside a later one costs that share more: a dealer who values the speed
    pays for it, and another takes the later option, which leaves the gig longer to find its driver."""

    def __init__(self, level: float = 1.33, scale: float = 0.09, gain: float = 0.03, dealer_gain: float = 0.0,
                 no_same_day: float = 0.094, by_list: float = 0.12, by_trust: float = 1.0,
                 cost_next: float = 1.13, cost_same: float = 1.01, ladder: float = 0.0, patience: int = 5 * HOUR,
                 floor: float = 1.1, ceiling: float = 2.4, war: float = 0.0, detail: float = 0.0, day_sd: float = 0.0,
                 same_up: float = 0.0, place_gain: float = 0.0, brake: float = 0.0, lanes: float = 0.0,
                 admit: Optional[Callable[[dict[str, Any], dict[str, int], "Desk"], dict[str, int]]] = None):
        super().__init__(options="all")
        self.dial, self.scale, self.gain, self.dealer_gain = math.log(level), scale, gain, dealer_gain
        self.no_same_day, self.by_list, self.by_trust = no_same_day, by_list, by_trust
        self.cost_next, self.cost_same, self.ladder, self.patience = cost_next, cost_same, ladder, patience
        self.floor, self.ceiling, self.war, self.admit = floor, ceiling, war, admit
        self.detail, self.day_sd, self.same_up, self.place_gain = detail, day_sd, same_up, place_gain
        self.lanes, self.near = lanes, {}  # place id -> drivers who live within NEAR_KM
        self.place_dial: dict[str, float] = {}  # pickup place id -> its own offset to the dial
        self.brake, self.won, self.strained = brake, 0, set()  # orders won, and those warned of their deadline or late
        self.day, self.at_war, self.war_over = -1, 0.0, False  # the day of the last quote, and the war's probability on it
        self.doubt, self.closes = 2 * day_sd ** 2, []  # the dial's variance, and the dial at the end of each usual day
        self.dealer_dial: dict[str, float] = {}  # dealer id -> its own offset to the dial
        self.asked: dict[str, int] = {}  # dealer id -> its requests so far
        self.trust: dict[str, int] = {}  # dealer id -> on-time orders, halved by a late one, at most 25
        self.coming: dict[str, int] = {}  # dealer id -> orders won and not yet delivered
        # request id -> (markup, effect without the dealer's and the place's offsets, dealer, prices, day, pickup place)
        self.quoted: dict[str, tuple[float, float, str, dict[str, int], int, str]] = {}
        self.dealer_of: dict[str, str] = {}  # order id -> dealer id
        self.on_time: set[str] = set()  # the delivered orders counted as on time
        self.late: set[str] = set()

    # --- the model ---

    def effect(self, request: dict[str, Any]) -> float:
        """The log of the request's limit against the dial."""
        kinds = [option["kind"] for option in request["options"]]
        dealer, leg = request["dealerId"], request["legs"][0]
        lane = PICKUP.get(leg["pickup"]["placeId"], 0.0) + DELIVERY.get(leg["delivery"]["placeId"], 0.0)
        return ((0.0 if "same_day" in kinds else self.no_same_day) + self.by_list * math.log(basis(request)["listPriceCents"] / 6000) + self.lanes * lane
                + self.by_trust * math.log(1 + self.trust.get(dealer, 0) / 100) + self.offsets(dealer, pickup(request)))

    def offsets(self, dealer: str, place: str) -> float:
        return self.dealer_dial.get(dealer, 0.0) + self.place_dial.get(place, 0.0)

    def chance(self, markup: float, effect: float) -> float:
        plain, low = self.chances(markup, effect)
        return (1 - self.at_war) * plain + self.at_war * low

    def chances(self, markup: float, effect: float) -> tuple[float, float]:
        """The chance that the dealer takes the quote on a usual day, and on the day of the price war."""
        gap = (self.dial + effect - math.log(markup)) / self.scale
        return 1 / (1 + math.exp(-gap)), 1 / (1 + math.exp(self.war / self.scale - gap))

    def morning(self, now: int) -> None:
        """The first quote of a day: the war, if it has not been, is as likely today as on each working day left."""
        if now // DAY > self.day:
            if self.day_sd and self.day >= 0:
                if self.at_war <= 0.5:
                    self.closes.append(self.dial)
                if self.closes:
                    self.dial = sum(self.closes) / len(self.closes)
                    self.doubt = self.day_sd ** 2 * (1 + 1 / len(self.closes))
            self.war_over = self.war_over or self.at_war > 0.5
            self.day = now // DAY
            self.at_war = min(0.5, 1 / (5 - self.day)) if self.war and not self.war_over and self.day < 5 else 0.0

    def drivers_near(self, place: str, desk: "Desk") -> int:
        if place not in self.near:
            self.near[place] = sum(1 for driver in desk.ctx.roster if desk.ctx.straight_km(place, driver["homePlaceId"]) <= NEAR_KM)
        return self.near[place]

    def cost(self, request: dict[str, Any], desk: "Desk") -> float:
        same_day = any(option["kind"] == "same_day" for option in request["options"])
        typical = request["referenceFeeCents"] * len(request["legs"])
        factor = (self.cost_same if same_day else self.cost_next) + self.brake * self.strain()
        if self.detail:
            first = request["legs"][0]
            start, end = first["pickup"]["placeId"], first["delivery"]["placeId"]
            private = any(leg[at]["privateAddress"] for leg in request["legs"] for at in ("pickup", "delivery"))
            later = first["pickup"]["window"]["from"] // DAY > request["arrivedAt"] // DAY
            shown = (private, later, math.log(typical / basis(request)["listPriceCents"]), first["car"]["premium"],
                     math.log(1 + self.drivers_near(end, desk)), math.log(1 + self.drivers_near(start, desk)),
                     math.log(max(desk.ctx.minutes(start, end), 1) / 120))
            factor += self.detail * sum(more * (value - mean) for (more, mean), value in zip(DETAIL, shown))
        return typical * factor

    def strain(self) -> float:
        """The share of the week's orders with a deadline warning or a late delivery, above a usual week's. The
        week starts as a usual one, with 40 orders' weight."""
        return (len(self.strained) + 40 * STRAIN) / (self.won + 40) - STRAIN

    def ladder_value(self, request: dict[str, Any], desk: "Desk", revenue: float) -> float:
        """What one more on-time order for this dealer is worth, in cents. A counted order lets each later request
        of the dealer take a price 1% higher at the same chance, so it is worth `ladder` (0.01) of the revenue
        that those requests should bring: `revenue` each, for as many as the dealer's rate so far promises from
        the day after, when the order counts. `patience` minutes stand in for the hours not yet seen, so a
        dealer's first requests promise little. Nothing once the dealer's counted and coming orders reach 25."""
        dealer = request["dealerId"]
        if not self.ladder or self.trust.get(dealer, 0) + self.coming.get(dealer, 0) >= 25:
            return 0.0
        later = self.asked.get(dealer, 0) * (worked(5 * DAY) - worked(desk.now + DAY)) / (worked(desk.now) + self.patience)
        return self.ladder * later * revenue

    def best_markup(self, request: dict[str, Any], desk: "Desk") -> float:
        effect, cost, list_price = self.effect(request), self.cost(request, desk), basis(request)["listPriceCents"]
        steps = range(round(self.floor * 100), round(self.ceiling * 100) + 1)

        def best(extra: float) -> float:
            return max(steps, key=lambda step: (step / 100 * list_price - cost + extra) * self.chance(step / 100, effect)) / 100

        plain = best(0.0)
        extra = self.ladder_value(request, desk, plain * list_price * self.chance(plain, effect))
        # A request that costs more than the ceiling pays: quote above the cost anyway, and lose it.
        return max(best(extra) if extra else plain, 1.05 * (cost - extra) / list_price)

    # --- quotes and what their answers teach ---

    def prices(self, request: dict[str, Any], desk: "Desk") -> dict[str, int]:
        if request["id"] not in self.quoted:  # a quote stays as it is: a desk that restarts quotes the same again
            self.morning(desk.now)
            dealer = request["dealerId"]
            self.asked[dealer] = self.asked.get(dealer, 0) + 1
            markup = self.best_markup(request, desk)
            dearer = 1 + self.same_up if len(request["options"]) > 1 else 1.0
            prices = {option["kind"]: round(option["listPriceCents"] * markup * (dearer if option["kind"] == "same_day" else 1.0))
                      for option in request["options"]}
            sent = self.admit(request, prices, desk) if self.admit else prices
            learns = any(sent.get(kind) == cents for kind, cents in prices.items())
            place = pickup(request)
            self.quoted[request["id"]] = (markup if learns else 0.0, self.effect(request) - self.offsets(dealer, place), dealer, prices, self.day, place)
        return self.quoted[request["id"]][3]

    def learn(self, request_id: str, won: bool) -> None:
        markup, effect, dealer, _, day, place = self.quoted.get(request_id, (0.0, 0.0, "", {}, 0, ""))
        if markup <= 0:
            return
        plain, low = self.chances(markup, effect + self.offsets(dealer, place))
        if self.at_war and day == self.day:  # Bayes: which of the two days explains this answer better?
            war, usual = self.at_war * (low if won else 1 - low), (1 - self.at_war) * (plain if won else 1 - plain)
            self.at_war = min(max(war / (war + usual), 0.001), 0.999)
        expected = (1 - self.at_war) * plain + self.at_war * low
        surprise = (1.0 if won else 0.0) - expected
        self.dial += max(self.gain, self.doubt / self.scale) * surprise
        self.doubt /= 1 + self.doubt * expected * (1 - expected) / self.scale ** 2
        if self.dealer_gain:
            self.dealer_dial[dealer] = self.dealer_dial.get(dealer, 0.0) + self.dealer_gain * surprise
        if self.place_gain:
            self.place_dial[place] = self.place_dial.get(place, 0.0) + self.place_gain * surprise

    def observe(self, event: dict[str, Any], desk: "Desk", replay: bool) -> None:
        kind = event["kind"]
        if kind == "price_request" and replay:
            self.prices(event["request"], desk)
        elif kind == "order_won":
            dealer = self.dealer_of[event["order"]["id"]] = event["order"]["dealerId"]
            self.coming[dealer] = self.coming.get(dealer, 0) + 1
            self.won += 1
            self.learn(event["order"]["id"], True)
        elif kind == "order_lost":
            self.learn(event["requestId"], False)
        elif kind == "order_cancelled":
            self.arrived(event["orderId"])
        elif kind == "deadline_close":
            self.strained.add(event["orderId"])
        elif kind == "ledger" and event["line"].get("orderId") in self.dealer_of:
            self.account(event["line"]["kind"], event["line"]["orderId"])

    def arrived(self, order_id: str) -> None:
        """The order is no longer coming: delivered, late, or cancelled."""
        if order_id in self.dealer_of and order_id not in self.on_time and order_id not in self.late:
            self.coming[self.dealer_of[order_id]] -= 1

    def account(self, line: str, order_id: str) -> None:
        """The dealer's trust: one up for an order delivered on time, halved by a late one."""
        dealer = self.dealer_of[order_id]
        count = self.trust.get(dealer, 0)
        if line == "revenue" and order_id not in self.late and order_id not in self.on_time:
            self.arrived(order_id)
            self.on_time.add(order_id)
            self.trust[dealer] = min(25, count + 1)
        elif line in ("late_refund", "undelivered_penalty") and order_id not in self.late:
            self.arrived(order_id)
            self.late.add(order_id)
            self.strained.add(order_id)
            self.trust[dealer] = (count - (1 if order_id in self.on_time else 0)) // 2


def worked(minute: int) -> int:
    """The working minutes of the week before `minute`: Monday to Friday, 08:00 to 18:00, when dealers ask."""
    day, of_day = divmod(minute, DAY)
    return 5 * 10 * HOUR if day >= 5 else day * 10 * HOUR + min(max(of_day - 8 * HOUR, 0), 10 * HOUR)


def pickup(request: dict[str, Any]) -> str:
    return request["legs"][0]["pickup"]["placeId"]


def basis(request: dict[str, Any]) -> dict[str, Any]:
    """The option whose list price the quoter reasons with: the first that is not `same_day`."""
    return next((option for option in request["options"] if option["kind"] != "same_day"), request["options"][0])
