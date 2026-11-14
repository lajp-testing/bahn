"""Rides home: a car from where one of our drivers will finish to near that driver's home.

Such a car is the cheapest in the world for that driver: they drive home anyway. The app never tells
a driver about gigs near where our gigs take them (tracks/t2/FINDINGS.md, "Where our delivery capacity
goes"), so the quoter prices the car as a bundled one (`cut` off its expected fee), and once it is won
its gig goes as one direct offer to that driver, at the fee its schedule shows then. The gig stays in
the app too, so a no costs nothing.

Everything comes from events and from the action journal (`result`), so a restarted desk knows it too.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

from .bundles import fee_at, orders_in
from .parts import Part

if TYPE_CHECKING:
    from .desk import Desk

DAY = 24 * 60
SOON = 6 * 60  # a ride's pickup window must open within this many minutes of the driver's last finish


class Home(Part):
    def __init__(self, km: float = 30.0, cut: float = 0.2):
        self.km, self.cut = float(km), float(cut)
        self.stops: dict[str, list[dict[str, Any]]] = {}  # gig id -> its stops, from the posts the world accepted
        self.ends: dict[str, tuple[str, int, int]] = {}  # driver -> (place, earliest, latest finish) of their last gig for us
        self.homes: dict[str, str] = {}  # driver -> home place
        self.rides: dict[str, str] = {}  # order won as a ride home -> its driver
        self.offered: set[str] = set()  # orders whose gig went as an offer
        self.per_day: dict[tuple[str, int], int] = {}  # (driver, day) -> offers sent

    def driver(self, request: dict[str, Any], desk: "Desk") -> Optional[str]:
        """The driver for whom this request is a ride home, or None."""
        legs = request["legs"]
        if len(legs) != 1:
            return None
        if not self.homes:
            self.homes = {d["id"]: d["homePlaceId"] for d in desk.ctx.roster}
        pickup, delivery = legs[0]["pickup"], legs[0]["delivery"]["placeId"]
        span = pickup.get("window") or {}
        best = None
        for driver, (place, earliest, latest) in self.ends.items():
            home = self.homes.get(driver)
            if home is None or span.get("to", 1 << 30) < earliest or span.get("from", 0) > latest + SOON:
                continue
            near = 0.0 if place == pickup["placeId"] else desk.ctx.straight_km(place, pickup["placeId"])
            if near > self.km or (home != delivery and desk.ctx.straight_km(home, delivery) > self.km):
                continue
            if best is None or near < best[0]:
                best = (near, driver)
        return best[1] if best else None

    def observe(self, event: dict[str, Any], desk: "Desk", replay: bool) -> None:
        kind = event["kind"]
        if kind == "gig_booked" or (kind == "offer_answered" and event["answer"] == "accepted"):
            self.finish(event["gigId"], event["driverId"], desk)
        elif kind == "order_won":
            request = desk.requests.get(event["order"]["id"])
            driver = self.driver(request, desk) if request else None
            if driver:
                self.rides[event["order"]["id"]] = driver

    def finish(self, gig: str, driver: str, desk: "Desk") -> None:
        """Where and when the driver ends the gig: its last delivery, between the earliest drive and the deadline."""
        stops = self.stops.get(gig)
        if not stops or stops[-1]["kind"] != "delivery":
            return
        requests = [desk.requests.get(o) for o in orders_in(stops)]
        if None in requests:
            return
        last = requests[-1]["legs"][stops[-1]["leg"]]["delivery"]["placeId"]
        first = requests[0]["legs"][stops[0]["leg"]]["pickup"]
        drive = sum(desk.ctx.minutes(a, b) for a, b in zip(places(stops, desk), places(stops, desk)[1:]) if a != b)
        earliest = max(desk.now, first.get("window", {}).get("from", desk.now)) + drive
        latest = max(earliest, max(o["deadline"] for o in requests[-1]["options"]))
        self.ends[driver] = (last, earliest, latest)

    def result(self, action: dict[str, Any], result: dict[str, Any], desk: "Desk") -> None:
        if not result.get("ok"):
            return
        if action["type"] == "post":
            self.stops[result["id"]] = action["stops"]
            if any(o in self.rides and o not in self.offered for o in orders_in(action["stops"])):
                desk.wake(desk.now + 1)
        elif action["type"] == "offer":  # also from the journal after a restart
            key = (action["driverId"], desk.now // DAY)
            self.per_day[key] = self.per_day.get(key, 0) + 1
            for order_id in orders_in(self.stops.get(action["gigId"], [])):
                if self.rides.get(order_id) == action["driverId"]:
                    self.offered.add(order_id)

    def tick(self, desk: "Desk") -> None:
        waiting = [o for o in self.rides if o not in self.offered and o in desk.orders]
        if not waiting:
            return
        minute = desk.now % DAY
        if minute >= 23 * 60 - 10 or minute < 7 * 60:  # no driver reads an offer from 23:00 to 07:00
            desk.wake((desk.now // DAY + (1 if minute >= 7 * 60 else 0)) * DAY + 7 * 60)
            return
        for order_id in waiting:
            driver, gigs = self.rides[order_id], desk.gigs_of(order_id)
            if len(gigs) != 1 or gigs[0] not in desk.posts:
                continue  # its gig is not in the app yet
            if gigs[0] in desk.booked:
                self.offered.add(order_id)  # a driver took it first
                continue
            self.offered.add(order_id)
            if self.per_day.get((driver, desk.now // DAY), 0) >= 3:
                continue
            fee = fee_at(desk.posts[gigs[0]]["schedule"], desk.now)
            desk.outbox.append({"type": "offer", "gigId": gigs[0], "driverId": driver, "feeCents": fee})


def places(stops: list[dict[str, Any]], desk: "Desk") -> list[str]:
    return [desk.requests[s["orderId"]]["legs"][s["leg"]][s["kind"]]["placeId"] for s in stops]
