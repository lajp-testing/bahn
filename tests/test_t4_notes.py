from dispatch.notes import TrackNotes, read_note
from dispatch.parts import Retry


def test_real_equipment_notes():
    assert read_note({'note': {'text': 'Manuaali, ei automaatti.'}}).manual is True
    assert read_note({'note': {'text': 'car has no plates, bring trade plates.'}}).plates is True
    assert read_note({'note': {'text': 'Summer tyres on, no winters.'}}).summer_tyres is True
    assert read_note({'note': {'text': 'Kesärenkaat vanteineen takakontissa'}}).summer_tyres is None


def test_unknown_note_is_not_confident():
    assert not read_note({'note': {'text': 'valmis huomenna klo 13'}}).sure
    assert read_note({'note': None}).sure


def test_first_post_uses_requirements():
    request = {'note': {'text': 'Manuaali, ei automaatti. car has no plates, bring trade plates.'}}
    order = {'id': 'R1', 'deadline': 1500, 'legs': [{'car': {'premium': False, 'electric': False, 'chargePercent': None}, 'pickup': {'window': {'from': 500, 'to': 1000}}, 'delivery': {'window': {'from': 500, 'to': 1500}}}]}
    stops, audience = TrackNotes().plan(order, [0], request, Retry(), None)
    assert audience['manualLicence']
    assert stops[0]['withPlates']
