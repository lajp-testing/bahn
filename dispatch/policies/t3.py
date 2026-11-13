"""Track 3: experimental measured fees inside the track 1 intake policy."""
from typing import Any
from ..context import Context
from ..fees import MeasuredFees
from ..intake import LimitedIntake
from ..notes import Notes
from ..parts import Parts
from ..quote import Quoter

def build(ctx: Context, **params: Any) -> Parts:
    return Parts(Quoter(markup=1.6, options="all"), LimitedIntake(15), MeasuredFees(**params), Notes())
