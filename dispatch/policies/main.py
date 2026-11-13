"""The team's mainline: the parts that have earned their place, put together.

    intake  track 1: a limit on the orders without a booked driver, no same-day options, no private addresses
    notes   the reader (dispatch/reader.py)
    fees    track 3: open near each car's estimated booking fee, two early raises
    quoter  the starter's, at a multiple of the list price; `price=profit` quotes the price that earns the most at the level the week shows (dispatch/pricing.py)

Each part can be switched back, to measure it: `notes=starter`, `fees=starter`, `private=true`.
Other parameters go on to the t1 policy (limit, markup, options, and the starter fees' numbers).
"""
from __future__ import annotations

from typing import Any

from ..context import Context
from ..fees import MeasuredFees
from ..notes import ReadNotes
from ..parts import Parts
from ..pricing import ProfitQuoter
from . import t1


PROFIT = ("start", "spread", "step", "boost", "cost", "queue", "low", "high")


def build(ctx: Context, notes: str = "read", fees: str = "measured", private: bool = False, markup: float = 1.6, price: str = "fixed", **params: Any) -> Parts:
    profit = {key: params.pop(key) for key in PROFIT if key in params}
    parts = t1.build(ctx, markup=markup, **params)
    parts.intake.private = private
    if price == "profit":
        parts.quoter = ProfitQuoter(limit=parts.intake.limit, **profit)
    if notes == "read":
        parts.notes = ReadNotes()
    if fees == "measured":
        parts.fees = MeasuredFees()
    return parts
