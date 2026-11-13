"""Track 3 fee experiments on the team's mainline."""
from typing import Any
from ..context import Context
from ..fees import MeasuredFees
from ..parts import Parts
from . import main


def build(ctx: Context, **params: Any) -> Parts:
    parts = main.build(ctx)
    parts.fees = MeasuredFees(**params)
    return parts
