"""Track 3 fee experiments on the team's mainline."""
from typing import Any
from ..context import Context
from ..fees import MeasuredFees
from ..parts import Parts
from . import main


def build(ctx: Context, **params: Any) -> Parts:
    fee_keys = {"buffer", "rise", "interval", "cap", "deadline_margin", "max_raises", "hold_until", "rescue_fraction", "urgent_open", "urgent_step", "urgent_every", "urgent_steps"}
    fees = {key: params.pop(key) for key in list(params) if key in fee_keys}
    parts = main.build(ctx, **params)
    fees.setdefault("interval", 60)  # ten-week matched improvement over low20
    parts.fees = MeasuredFees(**fees)
    return parts
