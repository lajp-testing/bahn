"""Track 3: fee experiments with the starter as the control.

Parameters go to the part that names them: `markup`, `options` to the quoter; `open`, `step`, `every`,
`steps`, `urgent_open`, `urgent_step`, `urgent_every`, `urgent_steps` to the fees.
"""
from __future__ import annotations

from typing import Any

from ..context import Context
from ..fees import Fees
from ..intake import Intake
from ..notes import Notes
from ..parts import Parts
from ..quote import Quoter

QUOTER = ("markup", "options")


def build(ctx: Context, **params: Any) -> Parts:
    quoter = Quoter(**{key: params.pop(key) for key in QUOTER if key in params})
    return Parts(quoter=quoter, intake=Intake(), fees=Fees(**params), notes=Notes())
