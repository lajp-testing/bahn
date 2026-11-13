"""Checks the desk, the practice loop and the slot broker without the server."""
from __future__ import annotations

import math
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


def test_a_ranking_run_needs_a_fresh_approval_for_each_run():
    with tempfile.TemporaryDirectory() as folder:
        old, config.DATA = config.DATA, folder
        saved = os.environ.pop(slots.APPROVAL, None)
        try:
            for value in (None, "L7:luukas-1"):  # none, or one for another level
                if value:
                    os.environ[slots.APPROVAL] = value
                try:
                    slots.approve_ranked(8)
                except SystemExit:
                    continue
                raise AssertionError(f"a ranking run started with approval {value!r}")
            os.environ[slots.APPROVAL] = "L8:luukas-1"
            assert slots.approve_ranked(8) == "luukas-1"
            try:
                slots.approve_ranked(8)  # the same approval again
            except SystemExit:
                pass
            else:
                raise AssertionError("one approval started two ranking runs")
        finally:
            config.DATA = old
            os.environ.pop(slots.APPROVAL, None)
            if saved is not None:
                os.environ[slots.APPROVAL] = saved


def test_a_ranking_run_is_never_deleted_on_an_error_or_by_the_next_process():
    deleted = []

    class Run:
        id = "wrank"

        def delete(self):
            deleted.append(self.id)

    class Client:
        def __init__(self, ended):
            self.ended = ended

        def worlds(self):
            return [{"worldId": "wrank", "boardRun": 1, "ended": self.ended, "kind": "practice", "level": 8, "parent": None, "season": 1}]

        def world(self, world_id):
            return Run()

    with tempfile.TemporaryDirectory() as folder:
        old, config.SLOTS = config.SLOTS, folder
        try:
            try:
                with slots._held("orch", Client(False), Run, delete_on_error=False):
                    raise RuntimeError("the system stopped mid-week")
            except RuntimeError:
                pass
            assert deleted == []
            try:  # the slot still names the unfinished ranking run: the next process stops instead of deleting it
                slots.acquire("orch", Client(False))
            except SystemExit:
                pass
            else:
                raise AssertionError("a process took the slot of an unfinished ranking run")
            assert deleted == []
            slot = slots.acquire("orch", Client(False), keep="wrank")  # resuming it keeps it
            assert slot is not None and slot.left_behind() == "wrank" and deleted == []
            slot.release()
            # A track's slot that a killed process left naming the run: resuming in orch's slot clears it there.
            with open(os.path.join(folder, "slot-0"), "w", encoding="utf-8") as file:
                file.write("wrank")
            with slots.adopt(Client(False), "wrank", board=True, track="orch"):
                assert open(os.path.join(folder, "slot-0"), encoding="utf-8").read() == ""
                assert open(os.path.join(folder, "slot-7"), encoding="utf-8").read() == "wrank"
            # An ended ranking run left in a slot is not deleted either: the slot is only freed.
            with open(os.path.join(folder, "slot-0"), "w", encoding="utf-8") as file:
                file.write("wrank")
            slot = slots.acquire("t1", Client(True))
            assert slot is not None and slot.left_behind() == "" and deleted == []
            slot.release()
        finally:
            config.SLOTS = old


def test_practice_runs_have_no_way_to_make_a_ranking_run():
    import inspect

    from harness import ranked, run

    assert "--board" not in inspect.getsource(run)
    source = inspect.getsource(ranked)
    assert 'os.environ.get("SPREAD_TEST_KEY"' in source and 'CountingClient(key=test_key)' in source
    assert 'environ.get("SPREAD_KEY"' not in source and 'environ["SPREAD_KEY"' not in source


def reach_desk(**params):
    from dispatch.desk import Desk

    context = Context.build(8, two_towns(), [{"id": f"d{i}", "homePlaceId": "helsinki", "rating": 4.9, "licence": "manual",
                                              "completedGigs": 80, "drops": 0} for i in range(25)])
    return Desk(None, context, load("reach")(context, **params), 600)


def test_future_same_day_quotes_a_car_ready_tomorrow_but_not_today():
    request = {**REQUEST, "note": None, "options": [{"kind": "same_day", "deadline": 1200 + 1440, "listPriceCents": 20000}]}
    for future, expected in ((False, {"same_day": 100000}), (True, {"same_day": 30000})):
        desk = reach_desk(future_same_day=future)
        desk.quote(request)
        assert desk.outbox[-1]["prices"] == expected
    desk = reach_desk(future_same_day=True)
    desk.quote({**REQUEST, "options": REQUEST["options"][:1]})  # ready today: still declined
    assert desk.outbox[-1]["prices"] == {"same_day": 100000}


def test_the_late_budget_brakes_intake_once_late_and_at_risk_orders_reach_it():
    desk = reach_desk(late_budget=0.1, budget_after=10, brake_drivers=30)
    intake = desk.parts.intake
    request = {**REQUEST, "note": None}
    for i in range(10):
        intake.observe({"kind": "order_won", "order": {"id": f"O{i}"}}, desk, False)
    assert not intake.braking(desk)
    desk.quote(request)
    assert desk.outbox[-1]["prices"] == {"next_day": 22500}
    intake.observe({"kind": "ledger", "line": {"kind": "late_refund", "orderId": "O1", "cents": -100}}, desk, False)
    assert intake.braking(desk)  # 1 late of 10 won is the 10% budget
    desk.quote(request)  # Helsinki has 25 drivers near, under the brake's 30: declined
    assert desk.outbox[-1]["prices"] == {"same_day": 100000}


def test_density_fees_stay_flat_near_drivers_and_climb_slowly_elsewhere():
    order = {**ORDER, "legs": [{**LEG, "delivery": {**PLACE, "placeId": "helsinki"}}]}  # 25 drivers live in Helsinki
    far = {**ORDER}  # delivery in Tampere, where nobody lives
    desk = reach_desk(density=True, open=0.85)
    desk.requests["R1"] = REQUEST
    assert desk.fees_for(order, 1) == [{"at": 600, "feeCents": 8500}]
    assert desk.fees_for(far, 1) == [{"at": 600, "feeCents": 8500}, {"at": 900, "feeCents": 11500}, {"at": 1080, "feeCents": 13000}]
    desk.urgent.add("R1")
    assert desk.fees_for(order, 1)[0] == {"at": 600, "feeCents": 15000}  # the warning brings the urgent schedule
    plain = reach_desk(open=0.85)
    plain.requests["R1"] = REQUEST
    assert len(plain.fees_for(order, 1)) == 6  # without density=true: the starter's hourly climb


def volume_request():
    return {**REQUEST, "arrivedAt": 600, "respondBy": 615, "note": None, "options": REQUEST["options"][:1]}


def test_long_lanes_need_open_hours_qualified_supply_and_risk_room():
    request = {**volume_request(), "options": REQUEST["options"][1:]}
    for enabled, expected in ((False, {"next_day": 75000}), (True, {"next_day": 22500})):
        desk = reach_desk(long_lanes=enabled)
        desk.ctx.road_minutes[("helsinki", "tampere")] = 360
        desk.quote(request)
        assert desk.outbox[-1]["prices"] == expected
    for long_max, markup, expected in ((359, 1.0, {"next_day": 75000}), (360, 1.2, {"next_day": 27000})):
        desk = reach_desk(long_lanes=True, long_max=long_max, long_markup=markup)
        desk.ctx.road_minutes[("helsinki", "tampere")] = 360
        desk.quote(request)
        assert desk.outbox[-1]["prices"] == expected
    both = {**request, "options": [{"kind": "same_day", "deadline": 2640, "listPriceCents": 20000}] + request["options"]}
    for same_day, expected in ((True, {"same_day": 30000, "next_day": 22500}), (False, {"next_day": 22500})):
        desk = reach_desk(long_lanes=True, long_same_day=same_day)
        desk.ctx.road_minutes[("helsinki", "tampere")] = 360
        desk.quote(both)
        assert desk.outbox[-1]["prices"] == expected
    # Residents with the wrong premium qualification are not six usable drivers.
    desk.ctx.roster = [{**d, "rating": 4.0} for d in desk.ctx.roster]
    desk.quote(request)
    assert desk.outbox[-1]["prices"] == {"next_day": 75000}
    desk = reach_desk(long_lanes=True)
    desk.ctx.road_minutes[("helsinki", "tampere")] = 360
    closed = {"opens": 480, "closes": 540, "weekdays": [2], "saturday": None}
    desk.quote({**request, "legs": [{**LEG, "delivery": {**LEG["delivery"], "hours": closed}}]})
    assert desk.outbox[-1]["prices"] == {"next_day": 75000}  # first opens Wednesday, due Tuesday
    for i in range(3):
        desk.parts.intake.observe({"kind": "ledger", "line": {"kind": "late_refund", "orderId": f"late-{i}"}}, desk, False)
    desk.quote(request)
    assert desk.outbox[-1]["prices"] == {"next_day": 75000}


def test_batch_slots_reserve_capacity_before_any_quote_is_won():
    request = {**volume_request(), "batchId": "bulk-1"}
    desk = reach_desk()
    desk.quote(request)
    assert desk.outbox[-1]["prices"] == {"same_day": 100000}
    desk = reach_desk(batch_slots=True)
    for i in range(9):
        desk.quote({**request, "id": f"bulk-{i}"})
    assert [q["prices"]["same_day"] for q in desk.outbox] == [30000] * 8 + [100000]
    desk.now = 616  # lost quotes no longer reserve capacity
    desk.quote({**request, "id": "next-batch", "respondBy": 631})
    assert desk.outbox[-1]["prices"] == {"same_day": 30000}


def test_noted_slots_read_equipment_before_posting_and_keep_unknown_times_out():
    request = {**volume_request(), "note": {"text": "Manual, no plates.", "language": "en"}}
    desk = reach_desk(noted_slots=True)
    desk.quote(request)
    assert desk.outbox[-1]["prices"] == {"same_day": 30000}
    desk.win(ORDER)
    post = desk.outbox[-1]
    assert post["audience"]["manualLicence"] and post["stops"][0]["withPlates"]
    desk.quote({**request, "note": {"text": "Thanks. Ready tomorrow 11:30.", "language": "en"}})
    assert desk.outbox[-1]["prices"] == {"same_day": 100000}
    desk = reach_desk(noted_slots=True)
    request = {**request, "note": {"text": "Automatic, not a manual. Thanks.", "language": "en"}}
    desk.quote(request)
    desk.win(ORDER)
    assert not desk.outbox[-1]["audience"]["manualLicence"]
    plain = reach_desk()
    plain.quote(request)
    assert plain.outbox[-1]["prices"] == {"same_day": 100000}


def test_private_slots_need_booking_time_and_room_inside_the_actual_slot():
    request = volume_request()
    delivery = {**LEG["delivery"], "privateAddress": True, "window": {"from": 1050, "to": 1110}}
    request = {**request, "legs": [{**LEG, "delivery": delivery}],
               "options": [{**request["options"][0], "deadline": 1140}]}
    for enabled, expected in ((False, 100000), (True, 30000)):
        desk = reach_desk(private_slots=enabled)
        desk.quote(request)
        assert desk.outbox[-1]["prices"]["same_day"] == expected
        desk = reach_desk(private_slots=enabled, no_private=True)  # no_private leaves private requests to the gate
        desk.quote(request)
        assert desk.outbox[-1]["prices"]["same_day"] == expected
    desk.quote({**request, "legs": [{**LEG, "delivery": {**delivery, "window": {"from": 900, "to": 960}}}]})
    assert desk.outbox[-1]["prices"] == {"same_day": 100000}  # earliest arrival 961, outside the slot


def test_trade_ins_keep_the_same_visit_and_reject_routes_over_twelve_hours():
    private = {**LEG["delivery"], "privateAddress": True, "window": {"from": 1030, "to": 1090}}
    outbound = {**LEG, "delivery": private}
    back = {**LEG, "pickup": {**private, "window": {"from": 1000, "to": 1020}}, "delivery": PLACE}
    request = {**volume_request(), "legs": [outbound, back],
               "options": [{**REQUEST["options"][0], "deadline": 1300}]}
    for enabled, expected in ((False, 100000), (True, 30000)):
        desk = reach_desk(trade_ins=enabled, long_lanes=True)
        desk.quote(request)
        assert desk.outbox[-1]["prices"]["same_day"] == expected
    desk.ctx.road_minutes[("helsinki", "tampere")] = 361
    desk.ctx.road_minutes[("tampere", "helsinki")] = 361
    desk.quote(request)
    assert desk.outbox[-1]["prices"] == {"same_day": 100000}


def test_no_private_and_no_trade_ins_decline_those_classes_even_when_reachable():
    private = {**REQUEST, "legs": [{**LEG, "delivery": {**LEG["delivery"], "privateAddress": True}}]}
    trade = {**REQUEST, "legs": [LEG, {**LEG, "pickup": LEG["delivery"], "delivery": PLACE}]}
    for request, switch in ((private, "no_private"), (trade, "no_trade_ins")):
        desk = reach_desk(min_drivers=0)
        desk.quote(request)
        assert desk.outbox[-1]["prices"] == {"next_day": 22500}
        desk = reach_desk(min_drivers=0, **{switch: True})
        desk.quote(request)
        assert desk.outbox[-1]["prices"] == {"same_day": 100000}
    desk = reach_desk(min_drivers=0, no_private=True, no_trade_ins=True)
    desk.quote(REQUEST)  # a plain request is unchanged
    assert desk.outbox[-1]["prices"] == {"next_day": 22500}


def test_thin_drivers_offers_a_long_leg_from_a_thin_pickup_with_three_days_only():
    request = {**REQUEST, "options": REQUEST["options"] + [{"kind": "within_3_days", "deadline": 5520, "listPriceCents": 12000}]}
    for thin, expected in ((0, {"next_day": 22500, "within_3_days": 18000}), (25, {"next_day": 22500, "within_3_days": 18000}),
                           (26, {"next_day": 22500, "within_3_days": 18000})):
        desk = reach_desk(thin_drivers=thin)  # 25 drivers live in Helsinki; the leg drives 106 minutes
        desk.quote(request)
        assert desk.outbox[-1]["prices"] == expected
    for thin, expected in ((25, {"next_day": 22500, "within_3_days": 18000}), (26, {"within_3_days": 18000})):
        desk = reach_desk(thin_drivers=thin)
        desk.ctx.road_minutes[("helsinki", "tampere")] = 120
        desk.quote(request)
        assert desk.outbox[-1]["prices"] == expected
    desk.quote(REQUEST)  # no three-day option: declined
    assert desk.outbox[-1]["prices"] == {"same_day": 100000}
    for thin, expected in ((25, {"next_day": 22500, "within_3_days": 18000}), (26, {"within_3_days": 18000})):
        desk = reach_desk(thin_drivers=thin, thin_both=True)  # no driver lives near Tampere: short legs count too
        desk.quote(request)
        assert desk.outbox[-1]["prices"] == expected
    for thin, expected in ((0, {"next_day": 22500, "within_3_days": 18000}), (26, {"within_3_days": 18000})):
        desk = reach_desk(thin_drivers=thin, thin_both=True, long_lanes=True)  # a long lane, through the gate
        desk.ctx.road_minutes[("helsinki", "tampere")] = 360
        desk.quote({**request, "note": None})
        assert desk.outbox[-1]["prices"] == expected


NEXT_DAY = {**REQUEST, "note": None, "options": REQUEST["options"][1:]}  # list €150, typical fee €100, D1


def quoted(desk, request):
    desk.quote(request)
    return desk.outbox[-1]["prices"]


def test_the_dial_prices_by_cost_and_chance_and_moves_with_the_answers():
    from dispatch.quote import DialQuoter, Quoter

    assert type(reach_desk().parts.quoter) is Quoter  # the dial is a switch: reach without it quotes 1.5 x list
    desk = reach_desk(quoter="dial")
    quoter = desk.parts.quoter
    assert type(quoter) is DialQuoter
    first = quoted(desk, NEXT_DAY)["next_day"]
    assert 1.13 * 10000 < first < 2.4 * 15000  # above the order's cost, inside the price range
    assert quoted(desk, NEXT_DAY)["next_day"] == first  # the same request again: the same quote
    assert quoted(reach_desk(quoter="dial", cost_next=1.6), NEXT_DAY)["next_day"] > first  # a dearer order, a higher price
    both = quoted(desk, {**REQUEST, "id": "R0", "note": None})  # the dealer also offers same_day: a lower limit
    assert both == {"next_day": both["next_day"]} and both["next_day"] < first
    quoter.observe({"kind": "order_lost", "requestId": "R1"}, desk, False)
    after_loss = quoted(desk, {**NEXT_DAY, "id": "R2"})["next_day"]
    assert after_loss < first
    quoter.observe({"kind": "order_won", "order": {**ORDER, "id": "R2"}}, desk, False)
    assert quoted(desk, {**NEXT_DAY, "id": "R3"})["next_day"] > after_loss


def test_a_request_that_the_intake_declines_teaches_the_dial_nothing():
    desk = reach_desk(quoter="dial")
    quoter = desk.parts.quoter
    same_day_only = {**REQUEST, "note": None, "options": REQUEST["options"][:1]}
    assert quoted(desk, same_day_only) == {"same_day": 100000}  # ready today: reach declines same_day
    dial = quoter.dial
    quoter.observe({"kind": "order_lost", "requestId": "R1"}, desk, False)
    assert quoter.dial == dial
    assert quoter.asked == {"D1": 1}


def test_the_dial_counts_a_dealers_trust_from_the_ledger():
    desk = reach_desk(quoter="dial")
    quoter = desk.parts.quoter
    first = quoted(desk, NEXT_DAY)["next_day"]

    def ledger(kind, order_id):
        quoter.observe({"kind": "ledger", "line": {"kind": kind, "orderId": order_id, "cents": 0}}, desk, False)

    for i in range(5):
        quoter.observe({"kind": "order_won", "order": {**ORDER, "id": f"O{i}"}}, desk, False)  # unknown requests: no lesson
    assert quoter.coming == {"D1": 5} and quoter.dial == math.log(1.33)
    for i in range(4):
        ledger("revenue", f"O{i}")
    ledger("revenue", "O0")  # a second revenue line of the same order does not count twice
    assert quoter.trust == {"D1": 4} and quoter.coming == {"D1": 1}
    assert quoted(desk, {**NEXT_DAY, "id": "R2"})["next_day"] > first  # the dealer accepts more now
    assert quoted(desk, {**NEXT_DAY, "id": "R3", "dealerId": "D2"})["next_day"] == first  # another dealer does not
    ledger("revenue", "O4")
    ledger("late_refund", "O4")  # counted on time at its revenue, then late: the count without it, halved
    assert quoter.trust == {"D1": 2} and quoter.coming == {"D1": 0}
    quoter.observe({"kind": "order_won", "order": {**ORDER, "id": "O5"}}, desk, False)
    quoter.observe({"kind": "order_cancelled", "orderId": "O5"}, desk, False)
    assert quoter.coming == {"D1": 0}


def test_a_price_war_is_a_day_that_the_dial_does_not_follow():
    plain, war = reach_desk(quoter="dial"), reach_desk(quoter="dial", war=0.3)
    first = quoted(war, NEXT_DAY)["next_day"]
    for desk in (plain, war):
        for i in range(30):  # thirty quotes in a row lose
            quoted(desk, {**NEXT_DAY, "id": f"L{i}"})
            desk.parts.quoter.observe({"kind": "order_lost", "requestId": f"L{i}"}, desk, False)
    assert war.parts.quoter.at_war > 0.9
    assert quoted(war, {**NEXT_DAY, "id": "W"})["next_day"] < first  # on the war's day it quotes lower, to win
    assert war.parts.quoter.dial > plain.parts.quoter.dial  # but its dial has not gone all the way down
    for desk in (plain, war):
        desk.parts.quoter.morning(1440 + 600)
    assert war.parts.quoter.at_war == 0 and war.parts.quoter.war_over  # one war a week
    assert war.parts.quoter.best_markup(NEXT_DAY, war) > plain.parts.quoter.best_markup(NEXT_DAY, plain)


def test_the_dial_moves_far_on_a_mornings_first_answers_and_little_later():
    plain, doubting = reach_desk(quoter="dial"), reach_desk(quoter="dial", day_sd=0.12)
    steps = []
    for desk in (plain, doubting):
        quoter = desk.parts.quoter
        for i in range(40):
            before = quoter.dial
            quoted(desk, {**NEXT_DAY, "id": f"L{i}"})
            quoter.observe({"kind": "order_won" if i % 2 else "order_lost", "requestId": f"L{i}", "order": {**ORDER, "id": f"L{i}"}}, desk, False)
            steps.append(abs(quoter.dial - before))
    assert steps[40] > 2 * steps[0]  # the first answer of the week moves a dial in doubt further
    assert steps[79] < steps[40] / 2  # and the fortieth much less
    quoter.morning(1440 + 600)
    assert quoter.doubt == 0.12 ** 2 * 2 and quoter.closes  # a new day: back to the mean of the days, and in doubt again


def test_detail_prices_a_private_address_up_and_a_car_ready_tomorrow_down():
    private = {**NEXT_DAY, "legs": [{**LEG, "delivery": {**PLACE, "placeId": "tampere", "privateAddress": True}}]}
    later = {**NEXT_DAY, "legs": [{**LEG, "pickup": {**PLACE, "window": {"from": 1440 + 600, "to": 1440 + 1200}}}]}
    quoter = reach_desk(quoter="dial", detail=1.0).parts.quoter
    assert quoter.cost(private) - quoter.cost(NEXT_DAY) == 0.23 * 10000
    assert round(quoter.cost(later) - quoter.cost(NEXT_DAY)) == -0.15 * 10000
    assert reach_desk(quoter="dial").parts.quoter.cost(private) == 1.13 * 10000  # off by default


def test_same_up_prices_same_day_above_the_later_option():
    tomorrow = {**PLACE, "window": {"from": 1440 + 600, "to": 1440 + 1200}}
    request = {**REQUEST, "note": None, "legs": [{**LEG, "pickup": tomorrow, "delivery": {**tomorrow, "placeId": "tampere"}}],
               "options": [{"kind": "same_day", "deadline": 1440 + 1200, "listPriceCents": 20000}, {"kind": "next_day", "deadline": 2 * 1440 + 1200, "listPriceCents": 15000}]}
    alike = quoted(reach_desk(quoter="dial", same_day=True), request)  # reach quotes same_day beside another option only when told
    dearer = quoted(reach_desk(quoter="dial", same_day=True, same_up=0.1), request)
    assert set(alike) == {"same_day", "next_day"} and alike["same_day"] * 3 == alike["next_day"] * 4  # one markup for both
    assert dearer["next_day"] == alike["next_day"] and dearer["same_day"] == round(alike["same_day"] * 1.1)
