"""The team's mainline: the parts that have earned their place, put together.

    intake  track 1: a limit on the orders without a booked driver, no same-day options, only options with a day of slack
    notes   the reader (dispatch/reader.py)
    fees    track 3: open near each car's estimated booking fee and rise a little every `rise` minutes
    quoter  the price that earns the most at the level the week shows, over each car's expected fee and late risk, at each dealer's own level of trust (dispatch/pricing.py)

Each part can be switched back, to measure it: `notes=starter`, `fees=starter`, `private=false`, `price=fixed`, `slack=0`, `car=0`, `late=0`, `trust=0`, `limit=15`.
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


PROFIT = ("start", "spread", "step", "boost", "cost", "queue", "low", "high", "car", "late", "trust", "invest", "share", "lag")


def build(ctx: Context, notes: str = "read", fees: str = "measured", private: bool = True, markup: float = 1.6, price: str = "profit", rise: int = 60, slack: int = 1440, limit: int = 25, car: float = 1.1, late: float = 1.0, trust: float = 1.0, **params: Any) -> Parts:
    profit = {"car": car, "late": late, "trust": trust} | {key: params.pop(key) for key in PROFIT if key in params}
    parts = t1.build(ctx, markup=markup, slack=slack, limit=limit, **params)
    parts.intake.private = private
    if price == "profit":
        parts.quoter = ProfitQuoter(limit=parts.intake.limit, **profit)
    if notes == "read":
        parts.notes = ReadNotes()
    if fees == "measured":
        parts.fees = MeasuredFees(interval=rise)
    return parts
