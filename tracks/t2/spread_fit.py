"""Fits the quoter's spread from saved weeks: level per day and spread by grid.

For every really-quoted request (tracks/t2/dealers.py `scan`) the effective ratio is
(lowest quoted price / list) / (the dealer's trust factor then).  The chance model is the
quoter's logistic curve: p = 1 / (1 + exp((ratio - level) / spread)).  For each spread on
a grid, each week-day gets its own best level (grid), and the fit that explains the
observed wins and losses with the highest log-likelihood wins.

Usage: python3 tracks/t2/spread_fit.py [label]   (default t2s5-base)
"""
from __future__ import annotations

import math
import sys

from dealers import scan, weeks


def loglik(rows, day, level, spread):
    total = 0.0
    for dealer, d, ratio, won in rows:
        if d != day:
            continue
        p = 1 / (1 + math.exp(max(-40.0, min(40.0, (ratio - level) / spread))))
        total += math.log(max(p if won else 1 - p, 1e-12))
    return total


def main(label: str = "t2s5-base") -> None:
    rows = []
    for folder in weeks(label):
        rows += scan(folder)
    print(f"{label}: {len(rows)} quoted requests")
    for spread in (0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40):
        total, levels = 0.0, []
        for day in range(5):
            best = max(((loglik(rows, day, level, spread), level)
                        for level in [0.8 + 0.01 * i for i in range(141)]))
            total += best[0]
            levels.append(best[1])
        print(f"spread {spread:.2f}: log-likelihood {total:12.1f}  day levels "
              + " ".join(f"{level:.2f}" for level in levels))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "t2s5-base")
