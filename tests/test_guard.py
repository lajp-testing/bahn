"""The on-time governor: the week's own record makes the quoter careful (dispatch/guard.py)."""
from __future__ import annotations

from dispatch.guard import Governor


class Desk:
    def __init__(self, orders, now):
        self.orders, self.now = orders, now


def order(ats, deadline):
    return {"deliveredAt": ats, "deadline": deadline}


def desk(on_time, late_delivered=0, late_open=0, deadline=900, now=2000):
    orders = {f"a{i}": order([100], deadline) for i in range(on_time)}
    orders.update({f"d{i}": order([1000], deadline) for i in range(late_delivered)})
    orders.update({f"o{i}": order([None], deadline) for i in range(late_open)})
    return Desk(orders, now)


def test_ignored_until_forty_decided():
    guard = Governor(0.94)
    assert guard.careful(desk(0, late_delivered=39)) is False  # 39 decided, all late: not enough yet
    assert guard.careful(desk(30, late_delivered=10)) is True  # 40 decided, 75% on time


def test_hysteresis():
    guard = Governor(0.94)
    assert guard.careful(desk(30, late_delivered=10)) is True   # 0.75: careful
    assert guard.careful(desk(38, late_delivered=2)) is True    # 0.95 <= guard + 0.01: stays careful
    assert guard.careful(desk(39, late_delivered=1)) is False   # 0.975 > guard + 0.01: back to normal


def test_undelivered_past_deadline_is_late():
    assert Governor(0.94).careful(desk(37, late_open=3)) is True  # past the deadline and not delivered
    assert Governor(0.94).careful(desk(39, late_open=1, deadline=5000)) is False  # still before it: undecided


def test_a_late_leg_counts_even_while_another_is_open():
    orders = {f"a{i}": order([100], 900) for i in range(37)}
    orders["p"] = order([100, 950], 900)  # one leg delivered after the deadline, one still open
    orders["q"] = order([1000], 900)
    orders["r"] = order([None], 901)      # past its deadline, not delivered
    assert Governor(0.94).careful(Desk(orders, 940)) is True  # 37 on time, 3 late
