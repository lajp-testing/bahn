"""The shape of the chance curve, measured from whole-week scans.

SURVIVAL[z] is the share of scanned `same_day` options whose switching ratio lay more than z
above the mean ratio of their own world and day: the true chance to win at a price z list
prices above the level. Made by tracks/t2/shape.py from the six level-8 scans in tracks/t2
(scan-t2-scan-*-l8.jsonl, 3,918 same_day rows over 30 world-days; rows with no winning price
skipped). Steeper in the middle than the logistic 1/(1+exp(z/0.2)) the quoter assumed
(S: 0.84 -> 0.16 over z -0.2..+0.2 vs 0.73 -> 0.27) and with thinner tails on both sides.
"""
from __future__ import annotations

SURVIVAL: list[tuple[float, float]] = [
    (-1.00, 1.0000),
    (-0.95, 1.0000),
    (-0.90, 1.0000),
    (-0.85, 1.0000),
    (-0.80, 1.0000),
    (-0.75, 1.0000),
    (-0.70, 0.9997),
    (-0.65, 0.9997),
    (-0.60, 0.9987),
    (-0.55, 0.9977),
    (-0.50, 0.9949),
    (-0.45, 0.9903),
    (-0.40, 0.9791),
    (-0.35, 0.9640),
    (-0.30, 0.9380),
    (-0.25, 0.8989),
    (-0.20, 0.8356),
    (-0.15, 0.7568),
    (-0.10, 0.6715),
    (-0.05, 0.5766),
    (0.00, 0.4745),
    (0.05, 0.3777),
    (0.10, 0.2930),
    (0.15, 0.2195),
    (0.20, 0.1577),
    (0.25, 0.1136),
    (0.30, 0.0804),
    (0.35, 0.0531),
    (0.40, 0.0368),
    (0.45, 0.0260),
    (0.50, 0.0174),
    (0.55, 0.0135),
    (0.60, 0.0089),
    (0.65, 0.0054),
    (0.70, 0.0043),
    (0.75, 0.0026),
    (0.80, 0.0018),
    (0.85, 0.0013),
    (0.90, 0.0003),
    (0.95, 0.0003),
    (1.00, 0.0003),
]


def survival(z: float) -> float:
    """The table's share at `z`: linear between points, 1.0 below the first, 0.0 above the last."""
    if z <= SURVIVAL[0][0]:
        return 1.0
    for (z0, s0), (z1, s1) in zip(SURVIVAL, SURVIVAL[1:]):
        if z <= z1:
            return s0 + (s1 - s0) * (z - z0) / (z1 - z0)
    return 0.0
