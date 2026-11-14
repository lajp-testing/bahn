"""The four parts of a policy, and what every part can do.

A part decides one thing. It also sees every event (`observe`), so it can learn during the week,
and it can ask the desk for a wake-up (`desk.wake(minute)`, then `tick`).

    Quoter  dispatch/quote.py   the price of each option of a request
    Intake  dispatch/intake.py  how much work to take: it may raise the quoter's prices or decline
    Fees    dispatch/fees.py    the fee schedule of a gig
    Notes   dispatch/notes.py   what a dealer's note means for a gig's stops

The classes in those files are the kit starter's behaviour. A policy (`dispatch/policies/`) chooses
one class for each part.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, NamedTuple

if TYPE_CHECKING:
    from .desk import Desk


class Retry(NamedTuple):
    """How to post a leg again after a failed visit."""
    pickup_from: int = 0
    manual_licence: bool = False
    plates: bool = False


class Part:
    """What every part can do besides its own decision. All of it is optional."""

    wake_on: list[str] = []  # event kinds, besides the desk's own, at which a practice world should stop

    def observe(self, event: dict[str, Any], desk: "Desk", replay: bool) -> None:
        """Every event, before the desk answers it. `replay` is true while a restarted desk reads the
        week's history: learn from the event then, but do not act."""

    def result(self, action: dict[str, Any], result: dict[str, Any], desk: "Desk") -> None:
        """The world's answer to one action that the desk sent: `{ok: True, id}` or `{ok: False, reason}`."""

    def tick(self, desk: "Desk") -> None:
        """After each step of the clock. Check `desk.now` against the minutes you asked `desk.wake` for."""


@dataclass
class Parts:
    quoter: Any
    intake: Any
    fees: Any
    notes: Any
    bundles: Any = None  # dispatch/bundles.py: which cars share a gig; None posts every order alone
    offers: Any = None  # dispatch/offers.py: direct offers for urgent or dropped gigs; None sends none
    home: Any = None  # dispatch/home.py: rides home for our drivers; None prices and posts them like any other car
    # The desk's own repairs, each a switch (docs/reviews/2026-11-14-whole-repo-review.md): "windows", "orphans", "late", "keep_urgent".
    repairs: frozenset = frozenset()
    requote: int = 0  # the desk quotes each undecided request again this many minutes before its respondBy; 0 for off

    def all(self) -> list[Part]:
        return [self.quoter, self.intake, self.fees, self.notes] + ([self.bundles] if self.bundles else []) + ([self.offers] if self.offers else []) + ([self.home] if self.home else [])
