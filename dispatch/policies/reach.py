"""The reach policy: quote every option at a markup over list, but only for cars that drivers can reach.

Parameters: `markup` (default 1.5) to the quoter, or `quoter=dial` and its parameters for
`dispatch.quote.DialQuoter`, which prices each request by its cost and its chance; `max_drive`, `min_drivers`, `near_km`, `same_day` to the
intake (`dispatch.intake.ReachIntake`), with `future_same_day` and `late_budget`; `density=true` and its
parameters choose `dispatch.fees.DensityFees`; `notes=read` chooses `dispatch.notes.ReadNotes`; the rest to the fees, as in `base`.
"""
from __future__ import annotations

from typing import Any

from ..context import Context
from ..fees import DensityFees, Fees
from ..intake import ReachIntake
from ..notes import Notes, ReadNotes
from ..parts import Parts
from ..quote import DialQuoter, Quoter

INTAKE = ("max_drive", "min_drivers", "near_km", "same_day", "future_same_day", "late_budget", "budget_after",
          "brake_drivers", "brake_drive", "long_lanes", "batch_slots", "noted_slots", "private_slots", "trade_ins",
          "no_private", "no_trade_ins", "thin_drivers", "thin_both",
          "long_max", "long_markup", "expand_brake", "long_same_day")
DIAL = ("level", "scale", "gain", "dealer_gain", "no_same_day", "by_list", "by_trust", "cost_next", "cost_same", "ladder", "patience", "war", "detail", "day_sd", "same_up", "place_gain", "brake", "lanes", "only_same",
        "floor", "ceiling")
DENSITY = ("dense", "dense_km", "far_1", "far_1_at", "far_2", "far_2_at")


def build(ctx: Context, **params: Any) -> Parts:
    # notes=read: the note reader from langsjo's mainline (dispatch/reader.py); otherwise the starter's notes.
    notes = ReadNotes() if params.pop("notes", "starter") == "read" else Notes(equipment=params.get("noted_slots", False))
    intake = ReachIntake(**{key: params.pop(key) for key in INTAKE if key in params})
    dial = {key: params.pop(key) for key in DIAL if key in params}
    if params.pop("quoter", "markup") == "dial":
        quoter: Quoter = DialQuoter(admit=intake.admit, **dial)
    else:
        quoter = Quoter(markup=params.pop("markup", 1.5), options="all")
    # density=true: the fee schedule by drivers near the delivery (DensityFees); otherwise the starter's climb.
    fees = DensityFees(**params) if params.pop("density", False) else Fees(**{k: v for k, v in params.items() if k not in DENSITY})
    return Parts(quoter=quoter, intake=intake, fees=fees, notes=notes)
