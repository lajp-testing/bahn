"""What a note changed, from the reveal's truth against the request: the labels to score a reader against."""
from __future__ import annotations


def delta(request: dict, truth: list[dict], option_deadline: int | None = None) -> dict:
    """The facts that differ from what the request states, over all legs of the request."""
    out: dict = {}
    for i, (leg, t) in enumerate(zip(request["legs"], truth)):
        if t["readyAt"] != leg["pickup"]["window"]["from"]:
            out.setdefault("ready", {})[i] = t["readyAt"]
        if t["releasedAt"] is not None:
            out.setdefault("release", {})[i] = t["releasedAt"]
        if t["pickupHours"] != leg["pickup"]["hours"]:
            out.setdefault("pickup_hours", {})[i] = t["pickupHours"]
        if t["deliveryHours"] != leg["delivery"]["hours"]:
            out.setdefault("delivery_hours", {})[i] = t["deliveryHours"]
        if t["noteDeadline"] is not None:
            out.setdefault("deadline", {})[i] = t["noteDeadline"]
        for key, name in (("manualGearbox", "manual"), ("needsPlates", "plates"), ("summerTyres", "summer_tyres")):
            if t[key]:
                out.setdefault(name, {})[i] = True
    return out
