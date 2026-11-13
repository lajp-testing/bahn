"""The notes: what a dealer's note means for a gig's stops. Owned by track 4 (notes)."""
from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any, Optional

from .parts import Part, Retry

if TYPE_CHECKING:
    from .desk import Desk

HOUR, DAY = 60, 24 * 60


class Notes(Part):
    """The starter's reader: clock times near a few keywords narrow a stop's window. A manual licence
    and plates are asked for only after a visit has failed for them."""

    def risk(self, request: dict[str, Any], desk: "Desk") -> float:
        """How unsure the reader is about this request's note, from 0 (sure) to 1. The intake can decline on it."""
        return 0.0

    def plan(self, order: dict[str, Any], legs: list[int], request: dict[str, Any], retry: Retry, desk: "Desk") -> tuple[list[dict[str, Any]], dict[str, bool]]:
        """The stops for some of the order's legs, and the drivers who may take the gig."""
        # A premium car needs an experienced driver: the fine is €150 a car.
        audience = {"experienced": any(leg["car"]["premium"] for leg in order["legs"]), "manualLicence": retry.manual_licence}
        return stops_for(order, legs, request["note"], retry), audience


def stops_for(order: dict[str, Any], legs: list[int], note: Optional[dict[str, Any]], retry: Retry) -> list[dict[str, Any]]:
    """A pickup and a delivery for each leg. An electric car under 30% gets a charging stop.
    A stop has its own window only when the note or the retry makes it narrower. Without
    one, the world plans the pickup in the order's window and the delivery by the deadline."""
    stops: list[dict[str, Any]] = []
    for leg in legs:
        car, pickup, delivery = order["legs"][leg]["car"], order["legs"][leg]["pickup"], order["legs"][leg]["delivery"]
        noted = window_from_note(note, pickup["window"], "pickup")
        start = max(noted["from"], retry.pickup_from)
        pickup_window = {"from": start, "to": max(noted["to"], start)}
        delivery_base = {"from": delivery["window"]["from"], "to": max(delivery["window"]["from"], order["deadline"])}
        delivery_window = window_from_note(note, delivery_base, "delivery")
        low_battery = car["electric"] and car["chargePercent"] is not None and car["chargePercent"] < 30
        first = {"orderId": order["id"], "leg": leg, "kind": "pickup", "withPlates": retry.plates, "withCharging": low_battery}
        second = {"orderId": order["id"], "leg": leg, "kind": "delivery"}
        stops += [narrower(first, pickup_window, pickup["window"]), narrower(second, delivery_window, delivery_base)]
    return stops


def narrower(stop: dict[str, Any], window: dict[str, int], base: dict[str, int]) -> dict[str, Any]:
    return {**stop, "window": window} if window["from"] > base["from"] or window["to"] < base["to"] else stop


# "Not before", "at the earliest" and a ready time all mean from then on; read them before BEFORE.
AFTER = re.compile(r"jälkeen|alkaen|aikaisintaan|\bafter\b|\bfrom\b|earliest|not before|ei ennen|valmis|\bready\b|efter|tidigast|inte före|klar", re.ASCII)
BEFORE = re.compile(r"ennen|mennessä|viim|\bbefore\b|\bby\b|latest|före|senast", re.ASCII)
DELIVERY = re.compile(r"toimit|perillä|perille|vastaanot|kohde|deliver|arrive|destination|receiv|leverera|leverans|framme|mottag", re.ASCII)
CLOCK = re.compile(r"(?:klo|kl\.?)\s*(\d{1,2})(?:[.:](\d{2}))?|\b(\d{1,2})[.:](\d{2})\b", re.ASCII)
# Opening hours as a range: "9-16", "klo 9.00-14.30", "kl 10-14".
RANGE = re.compile(r"\b(\d{1,2})(?:[.:](\d{2}))?\s*[-–]\s*(\d{1,2})(?:[.:](\d{2}))?\b", re.ASCII)


def window_from_note(note: Optional[dict[str, Any]], window: dict[str, int], stop: str) -> dict[str, int]:
    """Narrows a stop's window by clock times in the note, found by keywords: "nouto ennen 15.30",
    "klo 12 jälkeen", "deliver by 19:00", "efter kl. 12", "aikaisintaan klo 13.30", "not before
    16:00", and opening hours as a range, "arkisin 9-16". The time is on the window's own day."""
    if not note:
        return window
    text = note["text"].lower()
    if bool(DELIVERY.search(text)) != (stop == "delivery"):
        return window

    def minutes(hour: int, minute: int) -> Optional[int]:
        return None if hour > 24 or minute > 59 else hour * HOUR + minute

    start, end = window["from"], window["to"]
    # Opening hours hold every day: they move the window's start to the first day's opening and its end to the last day's closing.
    for match in RANGE.finditer(text):
        opens, closes = minutes(int(match[1]), int(match[2] or 0)), minutes(int(match[3]), int(match[4] or 0))
        if opens is None or closes is None or opens >= closes:
            continue
        start = max(start, start // DAY * DAY + opens)
        end = min(end, end // DAY * DAY + closes)
    text = RANGE.sub(" ", text)
    for match in CLOCK.finditer(text):
        m = minutes(int(match[1] or match[3]), int(match[2] or match[4] or 0))
        if m is None:
            continue
        time = window["from"] // DAY * DAY + m
        around = text[max(0, match.start() - 16) : match.end() + 16]
        if AFTER.search(around):
            start = max(start, time)
        elif BEFORE.search(around):
            end = min(end, time)
    return {"from": start, "to": end} if start <= end else window

# Track 4's conservative reader. None means that a field has not been established;
# it must not be interpreted as a negative fact.
from dataclasses import dataclass


@dataclass
class NoteFacts:
    earliest_pickup: Optional[int] = None
    pickup_hours: Optional[tuple[int, int]] = None
    release: Optional[int] = None
    delivery_hours: Optional[tuple[int, int]] = None
    deadline: Optional[int] = None
    manual: Optional[bool] = None
    plates: Optional[bool] = None
    summer_tyres: Optional[bool] = None
    sure: bool = False


def read_note(request: dict[str, Any]) -> NoteFacts:
    """Extract only unambiguous positive requirements; unresolved text is unsure."""
    facts = NoteFacts()
    note = request.get('note')
    if not note or not note.get('text', '').strip():
        facts.sure = True
        return facts
    text = note['text'].lower()
    if re.search(r'manuaal|manual gearbox|manual transmission|stick shift|manuell växel', text):
        facts.manual = True
    if re.search(r'no plates|without plates|ei rekkareita|kilvet (?:puuttuu|poistetu)|rekisterikilvet irrotettu|ilman kilpi|siirtokilvet|koekilvet|transfer plates|trade plates', text):
        facts.plates = True
    if re.search(r'summer ty(?:re|r)es on|no winters|sommardäck på|kesärenkaat alla|kesärenkailla', text):
        facts.summer_tyres = True
    return facts


class TrackNotes(Notes):
    """Keep the starter's windows while applying certain equipment requirements."""

    def risk(self, request: dict[str, Any], desk: "Desk") -> float:
        return 0.0 if read_note(request).sure else 1.0

    def plan(self, order: dict[str, Any], legs: list[int], request: dict[str, Any], retry: Retry, desk: "Desk") -> tuple[list[dict[str, Any]], dict[str, bool]]:
        facts = read_note(request)
        retry = Retry(retry.pickup_from, retry.manual_licence or bool(facts.manual), retry.plates or bool(facts.plates))
        return super().plan(order, legs, request, retry, desk)
