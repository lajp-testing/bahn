"""The reach policy: quote every option at a markup over list, but only for cars that drivers can reach.

Parameters: `markup` (default 1.5) to the quoter; `max_drive`, `min_drivers`, `near_km`, `same_day` to the
intake (`dispatch.intake.ReachIntake`), with `future_same_day` and `late_budget`; `density=true` and its
parameters choose `dispatch.fees.DensityFees`; the rest to the fees, as in `base`.
"""
from __future__ import annotations

from typing import Any

from ..context import Context
from ..fees import DensityFees, Fees
from ..intake import ReachIntake
from ..notes import Notes
from ..parts import Parts
from ..quote import Quoter

INTAKE = ("max_drive", "min_drivers", "near_km", "same_day", "future_same_day", "late_budget", "budget_after",
          "brake_drivers", "brake_drive")
DENSITY = ("dense", "dense_km", "far_1", "far_1_at", "far_2", "far_2_at")


def build(ctx: Context, **params: Any) -> Parts:
    quoter = Quoter(markup=params.pop("markup", 1.5), options="all")
    intake = ReachIntake(**{key: params.pop(key) for key in INTAKE if key in params})
    # density=true: the fee schedule by drivers near the delivery (DensityFees); otherwise the starter's climb.
    fees = DensityFees(**params) if params.pop("density", False) else Fees(**{k: v for k, v in params.items() if k not in DENSITY})
    return Parts(quoter=quoter, intake=intake, fees=fees, notes=Notes())
