"""The learned cost model (fee model 3): its inputs, its export, and the switch."""
import json
import os
from pathlib import Path

import pytest

from dispatch import features as F
from dispatch.context import Context
from dispatch.desk import Desk
from dispatch.policies.main import build

ROOT = Path(__file__).resolve().parent.parent


def world():
    for path in (ROOT / "data" / "map.json", ROOT / "tracks" / "t2" / "map.json"):
        if path.exists():
            return json.loads(path.read_text())
    pytest.skip("no map")


def request(rid="R1", pickup="helsinki", delivery="tampere", arrived=600):
    window = {"from": arrived, "to": arrived + 2000}
    hours = {"opens": 480, "closes": 1080, "weekdays": [0, 1, 2, 3, 4], "saturday": None}
    side = lambda place: {"placeId": place, "privateAddress": False, "window": window, "hours": hours}
    return {"id": rid, "dealerId": "D1", "batchId": None, "arrivedAt": arrived, "respondBy": arrived + 15,
            "legs": [{"car": {"premium": False, "electric": False, "chargePercent": None}, "pickup": side(pickup), "delivery": side(delivery)}],
            "options": [{"kind": "next_day", "deadline": arrived + 2000, "listPriceCents": 9000}],
            "referenceFeeCents": 5000, "note": None}


def desk(**params):
    m = world()
    roster = [{"id": f"d{i}", "homePlaceId": m["places"][i % len(m["places"])]["id"]} for i in range(60)]
    ctx = Context.build(8, m, roster)
    return Desk(None, ctx, build(ctx, **params), 600)


def test_features_match_names():
    d = desk()
    x = F.features(request(), d)
    assert len(x) == len(F.NAMES)
    assert all(isinstance(v, (int, float)) for v in x)
    assert "R1" not in d.requests  # the schedule features leave the desk's books as they were


def test_learned_model_and_switch():
    learned = pytest.importorskip("dispatch.learned")
    assert tuple(learned.NAMES) == F.NAMES
    d = desk(fee_model=3)
    r = request()
    fee, risk = d.parts.fees.expected(r, d), d.parts.fees.late_risk(r, d)
    assert 0.2 * r["referenceFeeCents"] < fee < 5 * r["referenceFeeCents"]
    assert 0.0 <= risk <= 1.0
    assert desk().parts.fees.model == 5  # the mainline uses model 5, retrained on the floor-0.75 weeks (b84: 40 weeks +EUR 14,444)
    assert desk(fee_model=2).parts.fees.model == 2  # the hand-fit model stays one switch away


def test_learned2_model_and_switch():
    learned2 = pytest.importorskip("dispatch.learned2")
    assert tuple(learned2.NAMES) == F.NAMES
    d = desk(fee_model=4)
    r = request()
    fee, risk = d.parts.fees.expected(r, d), d.parts.fees.late_risk(r, d)
    assert 0.2 * r["referenceFeeCents"] < fee < 5 * r["referenceFeeCents"]
    assert 0.0 <= risk <= 1.0
    assert desk(fee_model=3).parts.fees.model == 3  # model 3 stays unchanged, one switch away


def test_learned3_model_and_switch():
    learned3 = pytest.importorskip("dispatch.learned3")
    assert tuple(learned3.NAMES) == F.NAMES
    d = desk(fee_model=5)
    r = request()
    fee, risk = d.parts.fees.expected(r, d), d.parts.fees.late_risk(r, d)
    assert 0.2 * r["referenceFeeCents"] < fee < 5 * r["referenceFeeCents"]
    assert 0.0 <= risk <= 1.0
    assert desk(fee_model=4).parts.fees.model == 4  # model 4 stays unchanged, one switch away
