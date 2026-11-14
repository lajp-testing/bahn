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
    def __init__(self, cars: int = 2, dead: int = 30, slack: int = 6 * HOUR, split: int = 4 * HOUR, discount: float = 0.85, drive: int = 11 * HOUR, private: bool = False):
        self.cars = cars  # the most cars in one gig
        self.dead = dead  # the longest drive without a car between two cars, in minutes
        self.slack = slack  # a bundle is made only when its last possible start is at least this far away
        self.split = split  # a bundle without a driver this long before its last start goes back to one gig per car
        self.discount = discount  # a bundle's fee: this share of the sum of its cars' fees
        self.drive = drive  # the longest drive from first pickup to last delivery; the world's limit is 12 hours
        self.private = private  # whether a car at a private address may join a bundle

    def plain(self, order: dict[str, Any], desk: "Desk") -> bool:
        """A car that may share a gig: one car, no deadline warning yet, and no private address."""
        legs = order["legs"]
        return len(legs) == 1 and order["id"] not in desk.urgent and (self.private or not (legs[0]["pickup"]["privateAddress"] or legs[0]["delivery"]["privateAddress"]))

    def join(self, order: dict[str, Any], stops: list[dict[str, Any]], audience: dict[str, bool], desk: "Desk") -> Optional[tuple[str, list[dict[str, Any]], dict[str, bool]]]:
        """The open gig that the order's car joins, with the joined stops and audience; None when it goes alone."""
        if not self.plain(order, desk):
            return None
        best: Optional[tuple[tuple[int, int], str, list[dict[str, Any]], dict[str, bool]]] = None
        for gig_id, action in desk.posts.items():
            members = orders_in(action["stops"])
            if gig_id in desk.booked or len(members) >= self.cars or order["id"] in members:
                continue
            if not all(member in desk.orders and desk.gigs_of(member) == [gig_id] and self.plain(desk.orders[member], desk) for member in members):
                continue
            for joined in (action["stops"] + stops, stops + action["stops"]):
                found = self.route(joined, desk)
                if found is None or found[1] - desk.now < self.slack:
                    continue
                score = (found[0], desk.ctx.minutes(place(joined[-1], desk), place(joined[0], desk)) if place(joined[-1], desk) != place(joined[0], desk) else 0)
                if best is None or score < best[0]:
                    best = (score, gig_id, joined, {key: audience[key] or action["audience"][key] for key in audience})
        return best[1:] if best else None

    def route(self, stops: list[dict[str, Any]], desk: "Desk") -> Optional[tuple[int, int]]:
        """The minutes driven without a car, and the last minute a driver can start the first stop and reach
        every stop inside its window while its site is open. None when the stops do not fit in one gig."""
        dead = total = 0
        for a, b in zip(stops, stops[1:]):
            minutes = desk.ctx.minutes(place(a, desk), place(b, desk)) if place(a, desk) != place(b, desk) else 0
            total += minutes
            if a["kind"] == "delivery":
                if minutes > self.dead:
                    return None
                dead += minutes
        if total > self.drive:
            return None
        first = max(desk.now, window(stops[0], desk)["from"])
        last = min(window(stop, desk)["to"] for stop in stops)
        for start in range(last - last % 15, first - 1, -15):
            if self.reaches(stops, start, desk):
                return dead, start
        return None

    def reaches(self, stops: list[dict[str, Any]], start: int, desk: "Desk") -> bool:
        at = start
        for i, stop in enumerate(stops):
            if i:
                at += desk.ctx.minutes(place(stops[i - 1], desk), place(stop, desk)) if place(stops[i - 1], desk) != place(stop, desk) else 0
            span = window(stop, desk)
            if not (span["from"] <= at <= span["to"] and is_open(side(stop, desk)["hours"], at)):
                return False
            at += 30 * bool(stop.get("withPlates")) + 40 * bool(stop.get("withCharging"))
        return True

    def last_start(self, stops: list[dict[str, Any]], desk: "Desk") -> int:
        """The last minute a driver can start the bundle; now when it no longer fits."""
        found = self.route(stops, desk)
        return found[1] if found else desk.now

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


def side(stop: dict[str, Any], desk: "Desk") -> dict[str, Any]:
    return desk.orders[stop["orderId"]]["legs"][stop["leg"]][stop["kind"]]


def place(stop: dict[str, Any], desk: "Desk") -> str:
    return side(stop, desk)["placeId"]


def window(stop: dict[str, Any], desk: "Desk") -> dict[str, int]:
    """The stop's own window, or the order's: the pickup window, and for a delivery up to the deadline."""
    if "window" in stop:
        return stop["window"]
    order = desk.orders[stop["orderId"]]
    span = side(stop, desk)["window"]
    return span if stop["kind"] == "pickup" else {"from": span["from"], "to": max(span["from"], order["deadline"])}


def is_open(hours: Optional[dict[str, Any]], minute: int) -> bool:
    """Whether a site's stated hours show it open at a minute. A private address has no hours."""
    if not hours:
        return True
    day, clock = minute // DAY % 7, minute % DAY
    if day == 5 and hours.get("saturday"):
        return hours["saturday"]["opens"] <= clock <= hours["saturday"]["closes"]
    return day in hours["weekdays"] and hours["opens"] <= clock <= hours["closes"]
