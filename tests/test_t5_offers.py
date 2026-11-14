"""The `new` trigger of the offers (dispatch/offers.py): a direct offer to our drivers who finish near a
freshly posted gig's pickup, at the app's fee times `offer_new_fee`, only when they reach the pickup inside
its window from where we leave them."""
from __future__ import annotations

from dispatch.context import Context
from dispatch.offers import Offers

PLACES = {p: {"id": p, "name": p, "lat": 60.0 + 0.1 * i, "lon": 24.0} for i, p in enumerate(["helsinki", "vantaa", "tampere"])}
ROADS = [("helsinki", "vantaa", 30, 25.0), ("vantaa", "helsinki", 30, 25.0), ("helsinki", "tampere", 120, 160.0),
         ("tampere", "helsinki", 120, 160.0), ("vantaa", "tampere", 100, 140.0), ("tampere", "vantaa", 100, 140.0)]
ROSTER = [{"id": "d1", "homePlaceId": "tampere", "licence": "manual", "rating": 5, "completedGigs": 10, "drops": 0},
          {"id": "d2", "homePlaceId": "helsinki", "licence": "auto", "rating": 5, "completedGigs": 10, "drops": 0},
          {"id": "d3", "homePlaceId": "vantaa", "licence": "auto", "rating": 5, "completedGigs": 10, "drops": 0}]
ORDER = {"id": "R1", "dealerId": "D1", "legs": [{"pickup": {"placeId": "vantaa", "window": {"from": 600, "to": 700}},
                                                "delivery": {"placeId": "tampere", "window": {"from": 600, "to": 1200}}}],
         "lastPickupAt": 1000, "deliveredAt": [None]}


class FakeDesk:
    """What the offers part reads of the desk: the clock, the context, the order and its one-car gig."""

    def __init__(self, now=600, window=True):
        self.now, self.ctx, self.orders, self.requests = now, context(), {"R1": ORDER}, {"R1": {"referenceFeeCents": 10000}}
        self.urgent, self.booked, self.outbox, self.wakes = set(), set(), [], []
        pickup = {"kind": "pickup", "orderId": "R1", "leg": 0, "placeId": "vantaa"}
        if window:
            pickup["window"] = {"from": 600, "to": 700}
        self.action = {"type": "post", "stops": [pickup, {"kind": "delivery", "orderId": "R1", "leg": 0, "placeId": "tampere"}],
                       "audience": {}, "schedule": [{"at": now, "feeCents": 10000}]}
        self.posts = {"g1": self.action}
        self.leg_gigs = {"R1": {0: "g1"}}

    def wake(self, minute):
        self.wakes.append(minute)

    def gigs_of(self, order_id):
        return list(dict.fromkeys(self.leg_gigs.get(order_id, {}).values()))


def context():
    ctx = Context(level=8, places=PLACES, roster=ROSTER)
    ctx.road_minutes = {(a, b): m for a, b, m, _ in ROADS}
    ctx.road_km = {(a, b): k for a, b, _, k in ROADS}
    return ctx


def run(on="new", new_fee=1.0, window=True, at=None, urgent=False, per_day=None):
    desk = FakeDesk(window=window)
    desk.urgent.add("R1") if urgent else None
    offers = Offers(on=on, new_fee=new_fee)
    offers.at.update(at or {"d1": ("helsinki", 650)})
    offers.per_day.update(per_day or {})
    offers.result(desk.action, {"ok": True, "id": "g1"}, desk)
    offers.tick(desk)
    return offers, [action for action in desk.outbox if action["type"] == "offer"]


def test_new_trigger_offers_the_app_fee_to_a_driver_who_can_reach_the_pickup():
    offers, sent = run()
    assert [(action["driverId"], action["feeCents"]) for action in sent] == [("d1", 10000)]
    assert offers.wanted == {"R1": 0}  # one round only: the gig stays in the app at the same fee
    offers, sent = run(new_fee=0.9)
    assert sent[0]["feeCents"] == 9000


def test_new_trigger_skips_drivers_who_cannot_reach_the_pickup_in_time():
    _, sent = run(at={"d1": ("helsinki", 680)})  # the pickup's window ends at 700, 30 minutes away
    assert sent == []
    _, sent = run(at={"d1": ("tampere", 620)})  # the road from there takes 100 minutes
    assert sent == []
    _, sent = run(window=False, at={"d1": ("helsinki", 650)})  # a bare post: the leg's window still says when
    assert [(action["driverId"]) for action in sent] == ["d1"]
    ORDER["legs"][0]["pickup"]["window"] = None  # no window at all: unsure, so nobody
    _, sent = run(window=False)
    ORDER["legs"][0]["pickup"]["window"] = {"from": 600, "to": 700}
    assert sent == []


def test_new_trigger_stays_off_for_urgent_orders_and_other_modes():
    offers, sent = run(urgent=True)
    assert offers.wanted == {} and sent == []
    offers, sent = run(on="urgent")  # the default mode does not trigger on a post
    assert offers.wanted == {} and sent == []


def test_new_trigger_respects_the_limits_and_takes_the_closest_driver():
    _, sent = run(at={"d1": ("helsinki", 650), "d2": ("helsinki", 650), "d3": ("vantaa", 640)}, per_day={("d2", 0): 3})
    assert [action["driverId"] for action in sent] == ["d3", "d1"]  # closest first; d2 has its three offers today


def test_urgent_overrides_a_chain_want():
    desk = FakeDesk()
    offers = Offers(on="new+urgent", new_fee=0.5)
    offers.at["d1"] = ("helsinki", 650)
    offers.result(desk.action, {"ok": True, "id": "g1"}, desk)
    offers.observe({"kind": "deadline_close", "orderId": "R1"}, desk, replay=False)
    assert offers.wanted == {"R1": 2} and offers.chain == set()
    offers.tick(desk)
    assert desk.outbox[0]["feeCents"] == 11000  # the app's fee plus `up`, not the chain's fee


def test_new_waits_for_the_morning_when_posted_at_night():
    desk = FakeDesk(now=23 * 60 + 5)
    offers = Offers(on="new")
    offers.at["d1"] = ("helsinki", 23 * 60 + 30)
    offers.result(desk.action, {"ok": True, "id": "g1"}, desk)
    offers.tick(desk)
    assert not [a for a in desk.outbox if a["type"] == "offer"] and offers.wanted == {"R1": 1}
    assert desk.wakes[-1] == 24 * 60 + 7 * 60
