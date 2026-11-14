"""Track 1: limit the queue of work awaiting drivers."""
from typing import Any

from ..context import Context
from ..fees import Fees
from ..intake import LimitedIntake
from ..notes import Notes
from ..parts import Parts
from ..quote import Quoter


def build(ctx: Context, **params: Any) -> Parts:
    markup = params.pop("markup", 1.7)
    options = params.pop("options", "all")
    limit = params.pop("limit", 15)
    slack = params.pop("slack", 0)
    queue_price = params.pop("queue_price", False)
    win_price = params.pop("win_price", False)
    same_day_slack = params.pop("same_day_slack", -1)
    same_day_drivers = params.pop("same_day_drivers", 0)
    morning_limit = params.pop("morning_limit", 0)
    shortage_warnings = params.pop("shortage_warnings", 0)
    shortage_drops = params.pop("shortage_drops", 0)
    late_floor = params.pop("late_floor", 0)
    afternoon_ready = params.pop("afternoon_ready", 0)
    shortage_limit = params.pop("shortage_limit", 0)
    defaults = dict(open=1.3, step=0.1, every=60, steps=6)
    defaults.update(params)
    return Parts(Quoter(markup=markup, options=options), LimitedIntake(limit, slack=slack, queue_price=queue_price, win_price=win_price, same_day_slack=same_day_slack, same_day_drivers=same_day_drivers, morning_limit=morning_limit, shortage_warnings=shortage_warnings, shortage_drops=shortage_drops, late_floor=late_floor, afternoon_ready=afternoon_ready, shortage_limit=shortage_limit), Fees(**defaults), Notes())
