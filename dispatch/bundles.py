"""The bundles: which cars share a gig.

One driver who moves two cars in a row needs one trip to the first car and one trip home, where two
drivers need two of each. In copies of the same world a gig with two cars found a driver for about
14% less than the two cars posted alone, and it found one for cars that no driver took alone
(tracks/t5/FINDINGS.md). A bundle also uses one of the week's few drivers for two cars.

A newly won car joins an open gig when one driver can do all stops in a row: the next pickup is near
the last delivery, and a start exists that reaches every stop inside its window and opening hours.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

from .parts import Part

if TYPE_CHECKING:
    from .desk import Desk

HOUR, DAY = 60, 24 * 60


class Bundles(Part):
    def __init__(self, cars: int = 2, dead: int = 30, slack: int = 6 * HOUR, split: int = 4 * HOUR, discount: float = 0.85, drive: int = 11 * HOUR, private: bool = False, patience: int = 0, room: int = 0):
        self.cars = cars  # the most cars in one gig
        self.dead = dead  # the longest drive without a car between two cars, in minutes
        self.slack = slack  # a bundle is made only when its last possible start is at least this far away
        self.split = split  # a bundle without a driver this long before its last start goes back to one gig per car
        self.discount = discount  # a bundle's fee: this share of the sum of its cars' fees
        self.drive = drive  # the longest drive from first pickup to last delivery; the world's limit is 12 hours
        self.private = private  # whether a car at a private address may join a bundle
        self.patience = patience  # a bundle without a driver after this many minutes of the drivers' day goes back to one gig per car; 0: no limit
        self.room = room  # a bundle is made only when a driver can start it over at least this many minutes

    def plain(self, order: dict[str, Any], desk: "Desk") -> bool:
        """A car that may share a gig: one car, no deadline warning yet, and no private address."""
        legs = order["legs"]
        return len(legs) == 1 and order["id"] not in desk.urgent and (self.private or not (legs[0]["pickup"]["privateAddress"] or legs[0]["delivery"]["privateAddress"]))

    def join(self, order: dict[str, Any], stops: list[dict[str, Any]], audience: dict[str, bool], desk: "Desk") -> Optional[tuple[Any, list[dict[str, Any]], dict[str, bool]]]:
        """The gig that the order's car joins, with the joined stops and audience; None when it goes alone."""
        if not self.plain(order, desk):
            return None
        return self.search(order, stops, audience, desk, desk.orders)

    def fits(self, request: dict[str, Any], desk: "Desk") -> bool:
        """Whether the request's car, once won, could join a gig that is open now."""
        legs = request["legs"]
        if len(legs) != 1 or not (self.private or not (legs[0]["pickup"]["privateAddress"] or legs[0]["delivery"]["privateAddress"])):
            return False
        order = {"id": request["id"], "legs": legs, "deadline": max(option["deadline"] for option in request["options"])}
        stops = [{"orderId": order["id"], "leg": 0, "kind": kind} for kind in ("pickup", "delivery")]
        return self.search(order, stops, {}, desk, desk.orders | {order["id"]: order}) is not None

    def search(self, order: dict[str, Any], stops: list[dict[str, Any]], audience: dict[str, bool], desk: "Desk", orders: dict[str, Any]) -> Optional[tuple[Any, list[dict[str, Any]], dict[str, bool]]]:
        """The best gig to join: one that is open in the app (its id), or one that the desk has decided to post
        and not sent yet (the post itself), as when a dealer's cars are won in the same minute."""
        best: Optional[tuple[tuple[int, int], Any, list[dict[str, Any]], dict[str, bool]]] = None
        open_gigs = [(gig_id, action, [gig_id]) for gig_id, action in desk.posts.items() if gig_id not in desk.booked]
        unsent = [(action, action, []) for action in desk.outbox if action["type"] == "post"]
        for gig_id, action, carried_by in open_gigs + unsent:
            members = orders_in(action["stops"])
            if len(members) >= self.cars or order["id"] in members:
                continue
            if not all(member in desk.orders and desk.gigs_of(member) == carried_by and self.plain(desk.orders[member], desk) for member in members):
                continue
            for joined in (action["stops"] + stops, stops + action["stops"]):
                found = self.route(joined, desk, orders)
                if found is None or found[1] - desk.now < self.slack or found[2] < self.room:
                    continue
                score = (found[0], drive(joined[-1], joined[0], desk, orders))
                if best is None or score < best[0]:
                    best = (score, gig_id, joined, {key: audience[key] or action["audience"][key] for key in audience})
        return best[1:] if best else None

    def route(self, stops: list[dict[str, Any]], desk: "Desk", orders: Optional[dict[str, Any]] = None) -> Optional[tuple[int, int, int]]:
        """The minutes driven without a car, the last minute a driver can start the first stop and reach every
        stop inside its window while its site is open, and for how many minutes such a start exists. None
        when the stops do not fit in one gig."""
        orders = desk.orders if orders is None else orders
        dead = total = 0
        for a, b in zip(stops, stops[1:]):
            minutes = drive(a, b, desk, orders)
            total += minutes
            if a["kind"] == "delivery":
                if minutes > self.dead:
                    return None
                dead += minutes
        if total > self.drive:
            return None
        first = max(desk.now, window(stops[0], orders)["from"])
        last = min(window(stop, orders)["to"] for stop in stops)
        starts = [start for start in range(last - last % 15, first - 1, -15) if self.reaches(stops, start, desk, orders)]
        return (dead, starts[0], 15 * len(starts)) if starts else None

    def reaches(self, stops: list[dict[str, Any]], start: int, desk: "Desk", orders: dict[str, Any]) -> bool:
        at = start
        for i, stop in enumerate(stops):
            if i:
                at += drive(stops[i - 1], stop, desk, orders)
            span = window(stop, orders)
            if not (span["from"] <= at <= span["to"] and is_open(side(stop, orders)["hours"], at)):
                return False
            at += 30 * bool(stop.get("withPlates")) + 40 * bool(stop.get("withCharging"))
        return True

    def split_at(self, stops: list[dict[str, Any]], desk: "Desk") -> int:
        """When a bundle that still has no driver gives up: `split` before its last possible start, or
        after `patience` minutes of the drivers' day in the app. Now, when it no longer fits."""
        found = self.route(stops, desk)
        last = found[1] - self.split if found else desk.now
        fees = desk.parts.fees
        waited = (fees.after(desk.now, self.patience) if hasattr(fees, "after") else desk.now + self.patience) if self.patience else last
        return min(last, waited)

    def fees(self, schedules: list[list[dict[str, int]]], now: int) -> list[dict[str, int]]:
        """A bundle's fee schedule: at each minute, the sum of what its cars' own schedules pay then, less the discount."""
        times = sorted({max(now, step["at"]) for schedule in schedules for step in schedule})[:48]
        return [{"at": at, "feeCents": max(1, round(self.discount * sum(fee_at(schedule, at) for schedule in schedules)))} for at in times]


def orders_in(stops: list[Any]) -> list[str]:
    """The orders whose cars a list of stops carries, in the order of the stops."""
    return list(dict.fromkeys(stop["orderId"] for stop in stops))


def fee_at(schedule: list[dict[str, int]], at: int) -> int:
    """The fee that a schedule shows at a minute: its latest step that has started, or its first step."""
    started = [step["feeCents"] for step in schedule if step["at"] <= at]
    return started[-1] if started else schedule[0]["feeCents"]


def resume(schedule: list[dict[str, int]], now: int) -> list[dict[str, int]]:
    """A schedule taken up again at `now`: the fee it shows now, then its later steps."""
    return [{"at": now, "feeCents": fee_at(schedule, now)}] + [step for step in schedule if step["at"] > now]


def side(stop: dict[str, Any], orders: dict[str, Any]) -> dict[str, Any]:
    return orders[stop["orderId"]]["legs"][stop["leg"]][stop["kind"]]


def drive(a: dict[str, Any], b: dict[str, Any], desk: "Desk", orders: dict[str, Any]) -> int:
    """The road minutes from one stop to the next."""
    start, end = side(a, orders)["placeId"], side(b, orders)["placeId"]
    return desk.ctx.minutes(start, end) if start != end else 0


def window(stop: dict[str, Any], orders: dict[str, Any]) -> dict[str, int]:
    """The stop's own window, or the order's: the pickup window, and for a delivery up to the deadline."""
    if "window" in stop:
        return stop["window"]
    order = orders[stop["orderId"]]
    span = side(stop, orders)["window"]
    return span if stop["kind"] == "pickup" else {"from": span["from"], "to": max(span["from"], order["deadline"])}


def is_open(hours: Optional[dict[str, Any]], minute: int) -> bool:
    """Whether a site's stated hours show it open at a minute. A private address has no hours."""
    if not hours:
        return True
    day, clock = minute // DAY % 7, minute % DAY
    if day == 5 and hours.get("saturday"):
        return hours["saturday"]["opens"] <= clock <= hours["saturday"]["closes"]
    return day in hours["weekdays"] and hours["opens"] <= clock <= hours["closes"]
