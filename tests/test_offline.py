"""Checks the desk, the practice loop and the slot broker without the server."""
from __future__ import annotations

import os
import tempfile

from dispatch.context import Context
from dispatch.policies import load, parse_params
from harness import config, slots
from harness.play import Log, play

PLACE = {"placeId": "helsinki", "privateAddress": False, "window": {"from": 600, "to": 1200}, "hours": None}
LEG = {"car": {"premium": True, "electric": True, "chargePercent": 20}, "pickup": PLACE, "delivery": {**PLACE, "placeId": "tampere"}}
REQUEST = {"id": "R1", "dealerId": "D1", "batchId": None, "arrivedAt": 540, "respondBy": 555, "legs": [LEG],
           "options": [{"kind": "same_day", "deadline": 1200, "listPriceCents": 20000}, {"kind": "next_day", "deadline": 2640, "listPriceCents": 15000}],
           "referenceFeeCents": 10000, "note": {"text": "Nouto klo 12 jälkeen", "language": "fi"}}
ORDER = {"id": "R1", "dealerId": "D1", "option": "same_day", "priceCents": 20000, "deadline": 1200, "legs": [LEG],
         "status": "waiting", "deliveredAt": [None], "lastPickupAt": 1000}


class FakeWorld:
    """A week of three steps: a request, the win, a deadline warning."""

    id = "wfake"

    def __init__(self):
        self.now, self.sent, self.gigs = 0, [], 0
        self.script = [
            (540, [{"seq": 0, "at": 540, "kind": "price_request", "request": REQUEST}]),
            (555, [{"seq": 1, "at": 555, "kind": "order_won", "order": ORDER}]),
            (820, [{"seq": 2, "at": 600, "kind": "gig_viewed", "gigId": "g1", "driverId": "d1"},
                   {"seq": 3, "at": 820, "kind": "deadline_close", "orderId": "R1", "lastPickupAt": 1000}]),
        ]

    def snapshot(self):
        return {"now": self.now, "endsAt": 1440}

    def _apply(self, actions):
        results = []
        for action in actions:
            self.sent.append((self.now, action))
            if action["type"] == "post":
                self.gigs += 1
                results.append({"ok": True, "id": f"g{self.gigs}"})
            else:
                results.append({"ok": True, "id": action.get("requestId") or action.get("gigId")})
        return results

    def act(self, actions):
        return self._apply(actions)

    def advance(self, until=None, max=None, actions=()):
        results = self._apply(list(actions))
        if self.script and self.script[0][0] <= max:
            self.now, events = self.script.pop(0)
        else:
            self.now, events = max, []
        return {"now": self.now, "events": events, "results": results}


def two_towns(km: float = 172.4) -> dict:
    return {"places": [{"id": "helsinki", "name": "Helsinki", "lat": 60.17, "lon": 24.94}, {"id": "tampere", "name": "Tampere", "lat": 61.5, "lon": 23.76}],
            "roads": [{"from": a, "to": b, "km": 0 if a == b else km, "minutes": 0 if a == b else 106} for a in ("helsinki", "tampere") for b in ("helsinki", "tampere")]}


def ctx(km: float = 172.4) -> Context:
    return Context.build(8, two_towns(km), [{"id": "d1", "homePlaceId": "tampere", "rating": 4.9, "licence": "manual", "completedGigs": 80, "drops": 0}])


def test_base_policy_plays_the_starter():
    world, context = FakeWorld(), ctx()
    with tempfile.TemporaryDirectory() as folder:
        log = Log(folder)
        desk = play(world, context, load("base")(context), log)
        log.close()
        assert sorted(os.listdir(folder)) == ["actions.jsonl.gz", "events.jsonl.gz"]
    quote, post, reprice = (action for _, action in world.sent)
    assert quote == {"type": "quote", "requestId": "R1", "prices": {"same_day": 20000}}
    assert world.sent[0][0] == 540 and world.sent[1][0] == 555 and world.sent[2][0] == 820
    # A premium car goes to experienced drivers; a low battery on 172 km needs no charging stop; the note moves the pickup to 12:00.
    assert post["audience"] == {"experienced": True, "manualLicence": False}
    assert post["stops"][0] == {"orderId": "R1", "leg": 0, "kind": "pickup", "withPlates": False, "withCharging": False, "window": {"from": 720, "to": 1200}}
    assert post["schedule"][0] == {"at": 555, "feeCents": 10000} and post["schedule"][-1] == {"at": 855, "feeCents": 15000}
    assert reprice["gigId"] == "g1" and reprice["schedule"][0] == {"at": 820, "feeCents": 15000} and reprice["schedule"][-1] == {"at": 940, "feeCents": 25000}
    assert desk.now == 1440 and not desk.refused and desk.gigs_of("R1") == ["g1"]


def test_parameters_reach_the_parts():
    context = ctx()
    parts = load("base")(context, **parse_params(["markup=1.3", "options=all", "open=0.8", "steps=2"]))
    world = FakeWorld()
    play(world, context, parts)
    assert world.sent[0][1]["prices"] == {"same_day": 26000, "next_day": 19500}
    assert [step["feeCents"] for step in world.sent[1][1]["schedule"]] == [8000, 9000]


def test_a_part_can_ask_for_a_wake_up():
    context, world = ctx(), FakeWorld()
    parts = load("base")(context)
    ticks = []
    parts.intake.tick = lambda desk: (ticks.append(desk.now), desk.wake(700) if desk.now < 700 else None)
    play(world, context, parts)
    assert 700 in ticks


def test_slots_are_exclusive_and_bounded(monkeypatch=None):
    with tempfile.TemporaryDirectory() as folder:
        old, config.SLOTS = config.SLOTS, folder
        try:
            first = slots.acquire("t4", client=None)
            assert first is not None and first.index == 6
            assert slots.acquire("t4", client=None, wait=False) is None  # track 4 has one slot
            other = slots.acquire("t1", client=None, wait=False)
            assert other is not None and other.index in (0, 1)
            first.release()
            again = slots.acquire("t4", client=None, wait=False)
            assert again is not None
            again.release()
            other.release()
        finally:
            config.SLOTS = old


def test_only_the_orchestrator_plays_ranking_runs_and_holdout():
    for seed, board in (("hold-01", False), (None, True)):
        try:
            slots._check("t1", seed, board)
        except SystemExit:
            continue
        raise AssertionError("a track played what only the orchestrator may play")
    slots._check("orch", "hold-01", False)
    slots._check("t1", "dev-01", False)


class FakeLiveWorld(FakeWorld):
    """The same week from a stream: the win has already happened when the desk starts, and no gig is posted yet."""

    def snapshot(self):
        return {"now": 600, "endsAt": 1440, "orders": [ORDER], "gigs": [], "openRequests": []}

    def events(self, after=-1):
        return [event for _, events in FakeWorld().script[:2] for event in events]

    def roster(self):
        return []

    def stream(self, after=None, idle=None):
        assert after == 1  # from the last event of the history
        yield {"seq": 3, "at": 820, "kind": "deadline_close", "orderId": "R1", "lastPickupAt": 1000}
        yield {"seq": 4, "at": 1440, "kind": "ledger", "line": {}}

    def score(self):
        return {"marginCents": 0, "revenueCents": 0, "wonOrders": 1, "onTimeShare": 1.0, "undeliveredShare": 0.0, "ranked": True}


def test_the_live_desk_rejoins_and_answers_the_stream():
    from dispatch.live import play_live

    world = FakeLiveWorld()
    seen = []

    def build(context):
        parts = load("base")(context)
        parts.quoter.observe = lambda event, desk, replay: seen.append((event["kind"], replay))
        return parts

    play_live(world, 8, two_towns(), build, clock=lambda: 1440)
    kinds = [action["type"] for _, action in world.sent]
    assert kinds == ["post", "reprice"]  # the order without a gig is posted on rejoin; the warning makes it urgent
    assert seen[:2] == [("price_request", True), ("order_won", True)] and ("deadline_close", False) in seen


def test_reach_quotes_reachable_cars_above_list_and_declines_the_rest():
    context = ctx()  # one driver, living in Tampere; Helsinki to Tampere is 106 road minutes
    world = FakeWorld()
    play(world, context, load("reach")(context, min_drivers=1))
    # The pickup in Helsinki has no driver within 60 km: a losing quote at 5 x list, not no quote.
    assert world.sent[0][1]["prices"] == {"same_day": 100000}
    world = FakeWorld()
    play(world, context, load("reach")(context, min_drivers=0, markup=1.5))
    # Reachable: every option but same_day, at 1.5 x list.
    assert world.sent[0][1]["prices"] == {"next_day": 22500}


def test_a_low_battery_gets_a_charging_stop_only_over_200_km():
    # The car of LEG is electric at 20%. RULES.md: a charging stop is needed on a route over 200 km.
    charging = {}
    for km in (200, 200.1):
        world, context = FakeWorld(), ctx(km=km)
        play(world, context, load("base")(context))
        post = next(action for _, action in world.sent if action["type"] == "post")
        charging[km] = post["stops"][0]["withCharging"]
    assert charging == {200: False, 200.1: True}


class FakeRestartWorld(FakeLiveWorld):
    """The desk stopped after the deadline warning at 820 and before it sent the reprice: the gig still has the
    fees it was posted with."""

    def __init__(self, schedule):
        super().__init__()
        self.gig = {"id": "g1", "stops": [{"orderId": "R1", "leg": 0, "kind": "pickup"}, {"orderId": "R1", "leg": 0, "kind": "delivery"}],
                    "audience": {"experienced": True, "manualLicence": False}, "schedule": schedule, "status": "open",
                    "postedAt": 555, "feeCents": schedule[0]["feeCents"], "driverId": None}

    def snapshot(self):
        return {"now": 830, "endsAt": 1440, "orders": [ORDER], "gigs": [self.gig], "openRequests": []}

    def events(self, after=-1):
        events = [event for _, events in FakeWorld().script for event in events]
        return [event for event in events if event["kind"] != "gig_viewed"]

    def stream(self, after=None, idle=None):
        yield {"seq": 4, "at": 1440, "kind": "ledger", "line": {}}


def test_a_restart_resends_a_lost_urgent_reprice_but_does_not_restart_one_that_was_sent():
    from dispatch.live import play_live

    normal = [{"at": 555 + 60 * k, "feeCents": 10000 + 1000 * k} for k in range(6)]  # 1.0 to 1.5 x the typical fee
    world = FakeRestartWorld(normal)
    play_live(world, 8, two_towns(), lambda context: load("base")(context), clock=lambda: 1440)
    reprices = [action for _, action in world.sent if action["type"] == "reprice"]
    assert [r["gigId"] for r in reprices] == ["g1"]
    assert reprices[0]["schedule"][0] == {"at": 830, "feeCents": 15000} and reprices[0]["schedule"][-1]["feeCents"] == 25000

    sent = [{"at": 820 + 30 * k, "feeCents": 15000 + 2500 * k} for k in range(5)]  # the urgent reprice went out at 820
    world = FakeRestartWorld(sent)
    play_live(world, 8, two_towns(), lambda context: load("base")(context), clock=lambda: 1440)
    assert not [action for _, action in world.sent if action["type"] == "reprice"]
