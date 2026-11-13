"""A table of labels on one seed set: python3 -m harness.table <label prefix> [<label prefix> ...] [--seeds dev]"""
from __future__ import annotations

import collections
import sys

from . import config
from .play import read_index


def main() -> None:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    seeds = config.SEEDS[sys.argv[sys.argv.index("--seeds") + 1]] if "--seeds" in sys.argv else config.SEEDS["dev"]
    groups: dict[str, dict[str, dict]] = collections.defaultdict(dict)
    for row in read_index():
        if row["level"] == 8 and not row.get("board") and row["seed"] in seeds and any(row["label"].startswith(prefix) for prefix in args):
            groups[row["label"]][row["seed"]] = row
    print(f"{'label':46} {'weeks':>5} {'margin €':>9} {'orders':>6} {'on time':>7} {'worst':>6} {'ranked':>6} {'€/order':>7}")
    for label, weeks in sorted(groups.items(), key=lambda item: -sum(row["marginCents"] for row in item[1].values())):
        rows = list(weeks.values())
        orders = sum(row["wonOrders"] for row in rows)
        margin = sum(row["marginCents"] for row in rows) / 100
        on_time = sum(row["onTimeShare"] * row["wonOrders"] for row in rows) / max(1, orders)
        print(f"{label[:46]:46} {len(rows):>5} {margin:>9,.0f} {orders:>6} {on_time:>7.1%} {min(row['onTimeShare'] for row in rows):>6.1%} {sum(row['ranked'] for row in rows):>3}/{len(rows):<2} {margin / max(1, orders):>7.1f}")


if __name__ == "__main__":
    main()
