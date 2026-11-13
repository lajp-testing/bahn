"""The reach policy: quote every option at a markup over list, but only for cars that drivers can reach.

Parameters: `markup` (default 1.5) to the quoter; `max_drive`, `min_drivers`, `near_km`, `same_day` to the
intake (`dispatch.intake.ReachIntake`); the rest to the fees, as in `base`.
"""
from __future__ import annotations

from typing import Any

from ..context import Context
from ..fees import Fees
from ..intake import ReachIntake
from ..notes import Notes
from ..parts import Parts
from ..quote import Quoter

INTAKE = ("max_drive", "min_drivers", "near_km", "same_day")


def build(ctx: Context, **params: Any) -> Parts:
    quoter = Quoter(markup=params.pop("markup", 1.5), options="all")
    intake = ReachIntake(**{key: params.pop(key) for key in INTAKE if key in params})
    return Parts(quoter=quoter, intake=intake, fees=Fees(**params), notes=Notes())
