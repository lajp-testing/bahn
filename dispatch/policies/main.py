"""The team's mainline: the parts that have earned their place, put together.

    intake  track 1: a limit on the orders without a booked driver, no same-day options, no private addresses
    notes   the reader (dispatch/reader.py)
    fees    track 3: open near each car's estimated booking fee, two early raises
    quoter  the starter's, at a multiple of the list price; `price=clearing` lets the week set the level (dispatch/pricing.py)

Each part can be switched back, to measure it: `notes=starter`, `fees=starter`, `private=true`.
Other parameters go on to the t1 policy (limit, markup, options, and the starter fees' numbers).
"""
from __future__ import annotations

from typing import Any

from ..context import Context
from ..fees import MeasuredFees
from ..notes import ReadNotes
from ..parts import Parts
from ..pricing import ClearingQuoter
from . import t1


CLEARING = ("start", "step", "empty", "full", "low", "high", "trust")


def build(ctx: Context, notes: str = "read", fees: str = "measured", private: bool = False, markup: float = 1.6, price: str = "fixed", **params: Any) -> Parts:
    clearing = {key: params.pop(key) for key in CLEARING if key in params}
    parts = t1.build(ctx, markup=markup, **params)
    parts.intake.private = private
    if price == "clearing":
        parts.quoter = ClearingQuoter(limit=parts.intake.limit, **clearing)
    if notes == "read":
        parts.notes = ReadNotes()
    if fees == "measured":
        parts.fees = MeasuredFees()
    return parts
