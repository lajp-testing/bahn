"""Track 1: limit the queue of work awaiting drivers."""
from typing import Any

from ..context import Context
from ..fees import Fees
from ..intake import LimitedIntake
from ..notes import Notes
from ..parts import Parts
from ..quote import Quoter


def build(ctx: Context, **params: Any) -> Parts:
    markup = params.pop("markup", 1.8)
    options = params.pop("options", "all")
    limit = params.pop("limit", 15)
    defaults = dict(open=1.3, step=0.1, every=60, steps=6)
    defaults.update(params)
    return Parts(Quoter(markup=markup, options=options), LimitedIntake(limit), Fees(**defaults), Notes())
