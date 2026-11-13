from types import SimpleNamespace

from dispatch.intake import LimitedIntake
from dispatch.notes import Notes


def desk(notes):
    return SimpleNamespace(now=0, orders={}, booked=set(), gigs_of=lambda _: [],
                           parts=SimpleNamespace(notes=notes),
                           ctx=SimpleNamespace(minutes=lambda a, b: 60))


def request():
    return {"id": "r", "respondBy": 30, "legs": [{
        "pickup": {"placeId": "a", "privateAddress": False},
        "delivery": {"placeId": "b", "privateAddress": False}}],
        "options": [{"kind": "same_day", "deadline": 300, "listPriceCents": 100},
                    {"kind": "next_day", "deadline": 1800, "listPriceCents": 100}]}


def test_slack_filters_each_option_and_uses_note_ready_time():
    notes = SimpleNamespace(earliest_pickup=lambda r: 200,
                            latest_delivery=lambda r, end: end)
    intake = LimitedIntake(slack=1440)
    assert intake.admit(request(), {"same_day": 170, "next_day": 170}, desk(notes)) == {"next_day": 170}


def test_slack_falls_back_to_later_options_without_reader():
    intake = LimitedIntake(slack=1440)
    assert intake.admit(request(), {"same_day": 170, "next_day": 170}, desk(Notes())) == {"next_day": 170}


def test_queue_price_rises_with_pending_quotes():
    intake = LimitedIntake(limit=2, queue_price=True)
    first = request()
    second = dict(first, id="s")
    assert intake.admit(first, {"next_day": 1000}, desk(Notes())) == {"next_day": 900}
    assert intake.admit(second, {"next_day": 1000}, desk(Notes())) == {"next_day": 1000}
