"""The quoter: the price that earns the most, for the level this week's dealers accept.

A dealer buys from us when our price is under a switching price that we cannot see. Scans of whole
weeks (tracks/t2) show two things about it, as a multiple of the list price: its level moves from
day to day and from week to week (day means from 1.1 to 1.7), and around that level requests are
spread widely (a standard deviation of 0.2 to 0.35).

So the quoter keeps one number, the level, and a fixed spread. An option's kind moves its level too:
dealers pay more for a faster option (`same`). Together they give the chance to win
at any price; the curve is the logistic, or the shape measured from the scans (dispatch/shape.py).
For each option it quotes the price that maximises (price - cost) x chance. After each
dealer's decision the level moves a step: up after a win, down after a loss, by more when the result
was a surprise. The steps are larger for the first decisions of a day, because the level is new then.

The cost is what the car costs us to move: the fee we expect to pay for this car (the fees part
estimates it from where drivers live, the lane's length and a private address), what its risk of
being late costs, and a charge that rises as the queue of orders without a driver fills. A full
queue makes every car dearer for us, so prices rise before the intake has to decline.

At level 8 a dealer accepts prices 1% higher from us for each order we delivered to it on time, up
to 25 orders; a late order halves its count. The quoter keeps the same count from its own ledger
(`trust`), so it knows each dealer's level instead of one level for all. And because an order on
time raises every later price to that dealer, it is worth more than its own margin: `invest` takes
1% of the revenue we still expect from the dealer this week off the cost of the order.
"""
import math
from typing import TYPE_CHECKING, Any

from .lanes import leftover
from .parts import Part
from .shape import survival
from .towns import DELIVERY

if TYPE_CHECKING:
    from .desk import Desk

DAY = 24 * 60
OPEN, CLOSE, DAYS = 8 * 60, 18 * 60, 5  # requests arrive on five days, from 08:00 to 18:00


class ProfitQuoter(Part):
    wake_on = ["order_lost"]  # a loss moves the level too: hear of it at once

    def __init__(self, start: float = 1.4, spread: float = 0.2, step: float = 0.06, boost: float = 3.0, cost: float = 1.2,
                 queue: float = 0.3, limit: int = 15, low: float = 0.9, high: float = 2.6, car: float = 0.0, late: float = 0.0,
                 trust: float = 0.0, invest: float = 0.0, share: float = 0.25, lag: float = 0.15, dealer: float = 0.0,
                 towns: float = 0.0, same: float = 0.0, kind_offset: float = 0.0, shape: str = "logistic", shape_scale: float = 1.0,
                 lanes: float = 0.0, pair: float = 0.0, outage: float = 0.0, outage_z: float = 3.5, outage_n: int = 8,
                 target: float = 0.0, margin: float = 1.15, barrier: float = 0.0, allowance: float = 0.06, crowd: float = 0.5, floor_orders: int = 100,
                 end_car: float = 0.0):
        self.level, self.spread, self.step, self.boost = start, spread, step, boost
        self.pair = pair  # the share of its expected fee that a car saves when it can join a gig that is open now
        self.cost, self.queue, self.limit, self.low, self.high = cost, queue, limit, low, high
        # `car` > 0: the cost is `car` times the fee the fees part expects for this car, instead of `cost` times the typical fee.
        # `late`: what a late order costs, as a share of its price (the refund and the dealer's trust), times this car's risk of being late.
        self.car, self.late = car, late
        self.sent: dict[str, dict[str, float]] = {}  # request -> option -> the price we sent, as a multiple of the list price
        self.day, self.seen_today = -1, 0
        # `trust`: how much of the rule to use (1 = each counted order raises the dealer's level by 1%).
        # `invest`: how much of the later revenue that an order's trust buys to take off its cost.
        # `share`: the revenue we expect per euro of list price that a dealer asks about; `lag`: the part of the week before an order counts.
        self.trust, self.invest, self.share, self.lag = trust, invest, share, lag
        self.counts: dict[str, int] = {}     # dealer -> orders delivered on time, as the dealer counts them
        self.before: dict[str, tuple[str, int]] = {}  # delivered order -> its dealer and the dealer's count before it
        self.open: dict[str, str] = {}       # order won and not yet delivered -> dealer
        self.asked: dict[str, int] = {}      # dealer -> list price of its requests so far, in cents
        self.factors: dict[str, float] = {}  # request -> the dealer's factor when we quoted
        # `dealer` > 0: each dealer gets its own offset to the level, learned from its wins and losses.
        # `towns` > 0: the level also moves by the delivery town's lane part (dispatch/towns.py), scaled by this.
        self.dealer, self.dealers = dealer, {}   # step size, dealer -> offset, kept for the whole week
        self.towns = towns
        # `same` > 0: a same_day option's level sits this much higher, because dealers pay for speed.
        # `kind_offset`: the same for a within_3_days option. `shape`: "logistic", or "table" for the
        # measured curve (dispatch/shape.py), which `shape_scale` > 1 widens along its z axis.
        self.same, self.kind_offset = same, kind_offset
        # `lanes` > 0: the level also moves by the lane model's leftover for this option
        # (dispatch/lanes.py), scaled by this: the part of the spread the request's own features predict.
        self.lanes = lanes
        self.shape, self.shape_scale = shape, shape_scale
        self.offsets: dict[str, dict[str, float]] = {}  # request -> option kind -> the level offset used when we quoted
        self.owners: dict[str, str] = {}         # request -> the dealer, needed for a loss
        # `outage` > 0: on one working day the competitor is down around one town, and dealers there pay about 30% more.
        # While the day's requests picked up within 80 km of a request have won far more often for their prices than the
        # rest of the country's (`outage_z` standard errors, at least `outage_n` decided requests on each side), its level is this much higher.
        self.outage, self.outage_z, self.outage_n = outage, outage_z, outage_n
        self.heard_day, self.heard = -1, {}      # today, and pickup place -> [wins minus expected, variance, requests decided] today
        self.near: dict[str, list[str]] = {}     # place -> the places within 80 km
        self.trusts: dict[str, float] = {}       # request -> the dealer's factor without the outage, when we quoted
        self.places: dict[str, str] = {}         # request -> its pickup place
        # `target` > 0 (volume first): quote each option at the price whose learned chance to win is `target`, never below
        # `margin` times its expected cost, because the margin-per-quote price wins too few orders when the cost estimate is high.
        self.target, self.margin = target, margin
        # `barrier` > 0 (euros): the queue charge gives way to two prices. Room under the 90% on-time minimum costs
        # `barrier` x (late share / `allowance`)^4 per car, where the late share counts the orders late so far plus the
        # expected late among those still open, over at least `floor_orders`; and each car without a driver costs a new
        # car `crowd` euros, because it competes with it for the same drivers. Stateless: read from the desk's orders.
        self.barrier, self.allowance, self.crowd, self.floor_orders = barrier, allowance, crowd, floor_orders
        self.end_car = end_car  # the fee multiplier for an option due on Friday; 0 for the same as `car`
        self.risks: dict[str, float] = {}  # order -> its late risk when won (a cache; recomputed after a restart)

    def offset(self, request: dict[str, Any]) -> float:
        """How much this request's level moves: its dealer's learned offset and its delivery town's lane part."""
        dealer = self.dealers.get(request["dealerId"], 0.0)
        return dealer + (self.towns * DELIVERY.get(request["legs"][0]["delivery"]["placeId"], 0.0) if self.towns else 0.0)

    def kind_off(self, kind: str) -> float:
        """How much an option kind's level moves: dealers pay more for a faster option."""
        if kind == "same_day":
            return self.same
        if kind == "within_3_days":
            return self.kind_offset
        return 0.0

    def lane_off(self, request: dict[str, Any], kind: str, desk: "Desk") -> float:
        """How much this option's level moves by the lane model (dispatch/lanes.py), scaled by `lanes`."""
        if not self.lanes:
            return 0.0
        option = next((o for o in request["options"] if o["kind"] == kind), None)
        return self.lanes * leftover(request, option, desk.ctx) if option is not None else 0.0

    def chance(self, ratio: float, offset: float = 0.0) -> float:
        """The chance that a dealer takes a price of `ratio` times the list price."""
        z = ratio - self.level - offset
        if self.shape == "table":
            return survival(z / self.shape_scale)
        return 1 / (1 + math.exp(max(-40.0, min(40.0, z / self.spread))))

    def region(self, request: dict[str, Any], desk: "Desk") -> float:
        """How much higher the level is because the competitor looks down around the request's pickup today."""
        if not self.outage or desk.now // DAY != self.heard_day or not OPEN <= desk.now % DAY < CLOSE:
            return 1.0
        place = request["legs"][0]["pickup"]["placeId"]
        if place not in self.near:
            self.near[place] = [other for other in desk.ctx.places if desk.ctx.straight_km(place, other) <= 80]
        # The level itself follows the day's wins, so the test is the region against the rest of the country today.
        inside = [sum(self.heard[p][i] for p in self.near[place] if p in self.heard) for i in range(3)]
        outside = [sum(heard[i] for heard in self.heard.values()) - inside[i] for i in range(3)]
        if min(inside[2], outside[2]) < self.outage_n:
            return 1.0
        more = inside[0] / inside[2] - outside[0] / outside[2]
        error = math.sqrt(inside[1] / inside[2] ** 2 + outside[1] / outside[2] ** 2)
        return 1 + self.outage if more >= self.outage_z * error else 1.0

    def factor(self, dealer: str) -> float:
        """How much higher than a new dealer's this dealer's level is."""
        return 1 + 0.01 * self.trust * self.counts.get(dealer, 0)

    def future(self, dealer: str, now: int) -> float:
        """The revenue we still expect from the dealer this week after an order won now is delivered, in cents."""
        day, minute = divmod(now, DAY)
        done = (min(day, DAYS) * (CLOSE - OPEN) + (min(max(minute, OPEN), CLOSE) - OPEN if day < DAYS else 0)) / (DAYS * (CLOSE - OPEN))
        done = max(done, 0.03)
        return self.share * self.asked.get(dealer, 0) / done * max(0.0, 1 - done - self.lag)

    def waiting(self, desk: "Desk") -> float:
        """How full the queue of orders without a booked driver is, from 0 to 1."""
        from .intake import unbooked
        count = unbooked(desk, getattr(self, "queue_hours", 0), getattr(self, "queue_far", 0.0))
        return min(1.0, count / self.limit)

    def room(self, desk: "Desk") -> float:
        """The price in cents of one more car: what it uses of the late allowance plus what it costs the cars still without a driver."""
        from .intake import unbooked
        late = 0.0
        for order in desk.orders.values():
            open_ = any(at is None for at in order["deliveredAt"])
            if any(at is not None and at > order["deadline"] for at in order["deliveredAt"]) or (open_ and desk.now > order["deadline"]):
                late += 1
            elif open_ and order["id"] in desk.requests:
                if order["id"] not in self.risks:
                    self.risks[order["id"]] = desk.parts.fees.late_risk(desk.requests[order["id"]], desk)
                late += self.risks[order["id"]]
        share = late / max(len(desk.orders), self.floor_orders)
        return 100 * (self.barrier * (share / self.allowance) ** 4 + self.crowd * unbooked(desk))

    def prices(self, request: dict[str, Any], desk: "Desk") -> dict[str, int]:
        charge = self.queue * self.waiting(desk) ** 2
        room = 0.0
        if self.barrier:
            charge, room = 0.0, self.room(desk)
        intake = desk.parts.intake
        if getattr(intake, "safe_limit", 0) and intake.safe(request, desk):  # a safe car's queue is the larger one
            charge = self.queue * min(1.0, self.waiting(desk) * self.limit / intake.safe_limit) ** 2
        fees = desk.parts.fees
        fee = self.car * fees.expected(request, desk) if self.car and hasattr(fees, "expected") else self.cost * request["referenceFeeCents"]
        risk = self.late * fees.late_risk(request, desk) if self.late and hasattr(fees, "late_risk") else 0.0
        if self.pair and desk.parts.bundles and desk.parts.bundles.fits(request, desk):
            fee *= 1 - self.pair  # a car that can share a gig with one we hold costs less to move
        home = getattr(desk.parts, "home", None)
        if home and home.driver(request, desk):
            fee *= 1 - home.cut  # a ride home for one of our drivers costs them little: price it as a bundled car
        dealer = request["dealerId"]
        factor, gain = self.factor(dealer) * self.region(request, desk), 0.0
        if self.invest:
            count, future = self.counts.get(dealer, 0), self.future(dealer, desk.now)
            waiting = sum(1 for other in self.open.values() if other == dealer)
            # On time, the order adds 1% (while the dealer still counts); late, it takes half the count away.
            gain = self.invest * 0.01 * future * ((1 - risk) * (count + waiting < 25) - risk * count / 2)
        prices = {}
        offset = self.offset(request)
        for option in request["options"]:
            due_fee = fee
            if self.end_car and self.car and min(option["deadline"] // 1440, 7) == 4:
                due_fee = fee * self.end_car / self.car  # a car due Friday has no working day after it to recover a drop
            cost = (due_fee - gain + room) / option["listPriceCents"] + charge  # in list prices
            # A late order gives back part of its price: the expected loss grows with the price itself.
            floor = max(cost, 0.5 * fee / option["listPriceCents"])
            off = offset + self.kind_off(option["kind"]) + self.lane_off(request, option["kind"], desk)
            if self.target:
                grid = [0.5 + 0.01 * i for i in range(260)]
                hit = [ratio for ratio in grid if self.chance(ratio / factor, off) >= self.target]
                best = max(hit[-1] if hit else grid[0], self.margin * cost / max(0.05, 1 - risk), floor + 0.02)
                prices[option["kind"]] = round(option["listPriceCents"] * best)
                continue
            best = max((floor + 0.02 + 0.01 * i for i in range(260)), key=lambda ratio: (ratio * (1 - risk) - cost) * self.chance(ratio / factor, off))
            prices[option["kind"]] = round(option["listPriceCents"] * best)
        return prices

    def result(self, action: dict[str, Any], result: dict[str, Any], desk: "Desk") -> None:
        """Remembers the prices that went out: the intake may have changed or declined them."""
        request = desk.requests.get(action.get("requestId", ""))
        if action["type"] == "quote" and result.get("ok") and request is not None:
            lists = {option["kind"]: option["listPriceCents"] for option in request["options"]}
            self.sent[request["id"]] = {kind: cents / lists[kind] for kind, cents in action["prices"].items() if kind in lists}
            self.trusts[request["id"]] = self.factor(request["dealerId"])
            self.factors[request["id"]] = self.trusts[request["id"]] * self.region(request, desk)
            self.places[request["id"]] = request["legs"][0]["pickup"]["placeId"]
            self.offsets[request["id"]] = {kind: self.offset(request) + self.kind_off(kind) + self.lane_off(request, kind, desk)
                                           for kind in self.sent[request["id"]]}
            self.owners[request["id"]] = request["dealerId"]

    def observe(self, event: dict[str, Any], desk: "Desk", replay: bool) -> None:
        kind = event["kind"]
        if kind == "price_request":
            request = event["request"]
            self.asked[request["dealerId"]] = self.asked.get(request["dealerId"], 0) + min(option["listPriceCents"] for option in request["options"])
        elif kind == "ledger":
            self.count(event["line"])
        elif kind == "order_cancelled":
            self.open.pop(event.get("orderId", ""), None)
        if kind not in ("order_won", "order_lost"):
            return
        won = kind == "order_won"
        name = event["order"]["id"] if won else event["requestId"]
        sent, factor = self.sent.pop(name, None), self.factors.pop(name, 1.0)
        offsets, dealer = self.offsets.pop(name, {}), self.owners.pop(name, "")
        trust, place = self.trusts.pop(name, factor), self.places.pop(name, "")
        if won:
            self.open[event["order"]["id"]] = event["order"]["dealerId"]
        if not sent:
            return
        # A win shows the taken option's price was low enough; a loss shows even the closest option was too high.
        if won and event["order"]["option"] in sent:
            taken = event["order"]["option"]
        else:
            taken = min(sent, key=lambda k: sent[k] - offsets.get(k, 0.0))
        ratio, offset = sent[taken], offsets.get(taken, 0.0)
        if ratio > 4:
            return  # the intake declined this request: its loss says nothing about the level
        if event["at"] // DAY != self.day:
            self.day, self.seen_today = event["at"] // DAY, 0
        step = self.step * max(1.0, self.boost / math.sqrt(1 + self.seen_today / 3))
        self.seen_today += 1
        chance = self.chance(ratio / factor, offset)
        if self.outage and place and OPEN <= event["at"] % DAY < CLOSE + 30:
            if event["at"] // DAY != self.heard_day:
                self.heard_day, self.heard = event["at"] // DAY, {}
            usual = self.chance(ratio / trust, offset)  # what the price would win on a usual day
            heard = self.heard.setdefault(place, [0.0, 0.0, 0])
            heard[0], heard[1], heard[2] = heard[0] + (1.0 if won else 0.0) - usual, heard[1] + usual * (1 - usual), heard[2] + 1
        self.level = min(self.high, max(self.low, self.level + step * ((1.0 if won else 0.0) - chance)))
        if self.dealer:
            who = event["order"]["dealerId"] if won else dealer
            self.dealers[who] = min(0.4, max(-0.4, self.dealers.get(who, 0.0) + self.dealer * ((1.0 if won else 0.0) - chance)))

    def count(self, line: dict[str, Any]) -> None:
        """Keeps each dealer's count as the dealer does: one more for an order on time, half after a late one."""
        order = line.get("orderId")
        if line["kind"] == "revenue" and order in self.open:
            dealer = self.open.pop(order)
            self.before[order] = (dealer, self.counts.get(dealer, 0))
            self.counts[dealer] = min(25, self.counts.get(dealer, 0) + 1)
        elif line["kind"] == "late_refund" and order in self.before:
            dealer, before = self.before.pop(order)
            self.counts[dealer] = before // 2
        elif line["kind"] == "undelivered_penalty":
            self.open.pop(order, None)
