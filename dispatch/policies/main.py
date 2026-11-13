"""The team's mainline: the parts that have earned their place, put together.

    intake  track 1: a limit on the orders without a booked driver, no same-day options
    notes   the reader (dispatch/reader.py); `notes=starter` puts the starter's notes back, to measure the reader
    quoter, fees: the starter's, with track 1's numbers

Parameters go on to the t1 policy (limit, markup, options, and the fee parameters).
"""
from __future__ import annotations

from typing import Any

from ..context import Context
from ..notes import ReadNotes
from ..parts import Parts
from . import t1


def build(ctx: Context, notes: str = "read", **params: Any) -> Parts:
    parts = t1.build(ctx, **params)
    if notes == "read":
        parts.notes = ReadNotes()
    return parts
