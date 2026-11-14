"""The team's mainline: the parts that have earned their place, put together.

    intake  track 1: a limit on the orders without a booked driver, more room before noon, only options with 12 hours of slack; same-day options with 6 hours of slack and 80 drivers living near the pickup
    notes   the reader (dispatch/reader.py)
    fees    track 3: open near each car's estimated booking fee and rise a little every `rise` minutes, but not at night
    quoter  the price that earns the most at the level the week shows, over each car's expected fee and late risk, at each dealer's own level of trust (dispatch/pricing.py)

Each part can be switched back, to measure it: `notes=starter`, `fees=starter`, `private=false`, `price=fixed`, `slack=1440`, `same_day_slack=-1`, `car=0`, `late=0`, `trust=0`, `limit=15`, `fee_quiet_from=0`.
Other parameters go on to the t1 policy (limit, markup, options, and the starter fees' numbers).
"""
from __future__ import annotations

from typing import Any

from ..bundles import Bundles
from ..context import Context
from ..fees import MeasuredFees
from ..notes import ReadNotes
from ..offers import Offers
from ..parts import Parts
from ..pricing import ProfitQuoter
from . import t1


PROFIT = ("start", "spread", "step", "boost", "cost", "queue", "low", "high", "car", "late", "trust", "invest", "share", "lag", "dealer", "towns", "same", "kind_offset", "shape", "shape_scale", "lanes", "pair", "outage", "outage_z", "outage_n")
FEES = ("fee_model", "fee_buffer", "fee_rise", "fee_cap", "fee_max_raises", "fee_hold_until", "fee_deadline_margin", "fee_quiet_from", "fee_quiet_to", "fee_far_open", "fee_soon_open", "fee_early", "fee_backload")  # passed to the fees without the prefix


OFFERS = ("offer_n", "offer_up", "offer_near", "offer_fresh", "offer_rounds")  # passed to the offers without the prefix
BUNDLES = ("bundle_dead", "bundle_slack", "bundle_split", "bundle_discount", "bundle_drive", "bundle_private", "bundle_patience", "bundle_room")  # passed to the bundles without the prefix


def build(ctx: Context, notes: str = "read", fees: str = "measured", private: bool = True, markup: float = 1.6, price: str = "profit", rise: int = 60, slack: int = 720, limit: int = 35, morning_limit: int = 45, same_day_slack: int = 360, same_day_drivers: int = 80, car: float = 1.1, late: float = 1.0, trust: float = 1.0, bundle: int = 3, repairs: str = "windows+orphans+calm", pending: float = 1.0, queue_hours: float = 0, queue_far: float = 0.0, offers: str = "", day_limit: int = 0, **params: Any) -> Parts:
    together = {"patience": 120} | {key[7:]: params.pop(key) for key in BUNDLES if key in params}
    offer = {key[6:]: params.pop(key) for key in OFFERS if key in params}
    fee = {key[4:]: params.pop(key) for key in FEES if key in params}
    profit = {"car": car, "late": late, "trust": trust} | {key: params.pop(key) for key in PROFIT if key in params}
    parts = t1.build(ctx, markup=markup, slack=slack, limit=limit, morning_limit=morning_limit, same_day_slack=same_day_slack, same_day_drivers=same_day_drivers, **params)
    parts.intake.private = private
    parts.intake.pending_weight = pending  # how much of a place in the queue a quote awaiting its dealer holds
    # An unbooked order whose last pickup is more than `queue_hours` away holds only `queue_far` of a place: it is not yet a risk.
    parts.intake.queue_hours, parts.intake.queue_far = queue_hours, queue_far
    parts.intake.day_limit = day_limit  # the most undelivered orders due on one day; 0 for no such limit
    if price == "profit":
        parts.quoter = ProfitQuoter(limit=parts.intake.limit, **profit)
        parts.quoter.queue_hours, parts.quoter.queue_far = queue_hours, queue_far
    if notes == "read":
        parts.notes = ReadNotes()
    if fees == "measured":
        parts.fees = MeasuredFees(interval=rise, **({"quiet_from": 21 * 60, "model": 2} | fee))
    parts.repairs = frozenset(repairs.replace("+", ",").split(",")) - {""}  # e.g. --set repairs=windows+orphans+late+keep_urgent
    if bundle > 1:  # the most cars in one gig; below 2 every order goes alone
        parts.bundles = Bundles(cars=bundle, **together)
    if offers:  # e.g. --set offers=urgent+drops: direct offers for those gigs (dispatch/offers.py)
        parts.offers = Offers(on=offers, **offer)
    return parts
