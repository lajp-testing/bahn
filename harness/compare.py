"""Compares two versions on the weeks that both have played, or lists what the index holds.

    python -m harness.compare <label A> <label B>            A is the baseline, B the change
    python -m harness.compare <label A> <label B> --seeds dev
    python -m harness.compare --list                         every label in the index, newest last
    python -m harness.compare --list --track t2

A week is the pair (level, seed). When a label has played a week twice, the newest run counts.
"""
from __future__ import annotations

import argparse
from typing import Any

from . import config
from .play import read_index


def weeks_of(label: str, level: int, rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {row["seed"]: row for row in rows if row["label"] == label and row["level"] == level and not row.get("board")}


def totals(rows: list[dict[str, Any]]) -> tuple[float, int, float, int]:
    orders = sum(row["wonOrders"] for row in rows)
    on_time = sum(row["onTimeShare"] * row["wonOrders"] for row in rows) / orders if orders else 0.0
    return sum(row["marginCents"] for row in rows) / 100, orders, on_time, sum(1 for row in rows if row["ranked"])


def listing(rows: list[dict[str, Any]], track: str | None) -> None:
    groups: dict[tuple[str, int], list[dict[str, Any]]] = {}
    for row in rows:
        if not row.get("board") and (track is None or row["track"] == track):
            groups.setdefault((row["label"], row["level"]), []).append(row)
    print(f"{'first run':<16} {'track':<5} {'L':<2} {'weeks':>5} {'margin €':>12} {'orders':>7} {'on time':>8} {'ranked':>7}  label")
    for (label, level), group in sorted(groups.items(), key=lambda item: item[1][0]["at"]):
        latest = list({row["seed"]: row for row in group}.values())
        margin, orders, on_time, ranked = totals(latest)
        print(f"{group[0]['at']:<16} {group[0]['track']:<5} {level:<2} {len(latest):>5} {margin:>12,.0f} {orders:>7} {on_time:>8.1%} {ranked:>4}/{len(latest):<2}  {label}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Compares two labels on the weeks that both have played.")
    parser.add_argument("labels", nargs="*", help="the baseline's label, then the change's label")
    parser.add_argument("--level", type=int, default=8)
    parser.add_argument("--seeds", choices=sorted(config.SEEDS), help="count only the weeks of this seed set")
    parser.add_argument("--list", action="store_true", help="list the labels in the index")
    parser.add_argument("--track", help="with --list: only this track's runs")
    args = parser.parse_args()
    rows = read_index()
    if args.list or not args.labels:
        return listing(rows, args.track)
    if len(args.labels) != 2:
        parser.error("give two labels: the baseline, then the change")
    a, b = (weeks_of(label, args.level, rows) for label in args.labels)
    seeds = [seed for seed in a if seed in b and (args.seeds is None or seed in config.SEEDS[args.seeds])]
    if not seeds:
        raise SystemExit(f"No week at level {args.level} that both labels have played. A has {sorted(a)}, B has {sorted(b)}.")
    print(f"A = {args.labels[0]}\nB = {args.labels[1]}\nlevel {args.level}, {len(seeds)} weeks\n")
    print(f"{'seed':<12} {'margin A €':>11} {'margin B €':>11} {'B - A €':>10}   {'on time A':>9} {'on time B':>9}   {'orders A':>8} {'orders B':>8}   ranked A/B")
    better = 0
    for seed in sorted(seeds):
        x, y = a[seed], b[seed]
        diff = (y["marginCents"] - x["marginCents"]) / 100
        better += diff > 0
        print(f"{seed:<12} {x['marginCents'] / 100:>11,.0f} {y['marginCents'] / 100:>11,.0f} {diff:>+10,.0f}   {x['onTimeShare']:>9.1%} {y['onTimeShare']:>9.1%}   "
              f"{x['wonOrders']:>8} {y['wonOrders']:>8}   {'yes' if x['ranked'] else 'NO':>3} / {'yes' if y['ranked'] else 'NO'}")
    (ma, oa, ta, ra), (mb, ob, tb, rb) = totals([a[s] for s in seeds]), totals([b[s] for s in seeds])
    print(f"\n{'total':<12} {ma:>11,.0f} {mb:>11,.0f} {mb - ma:>+10,.0f}   {ta:>9.1%} {tb:>9.1%}   {oa:>8} {ob:>8}   {ra}/{len(seeds)} / {rb}/{len(seeds)}")
    print(f"B has the higher margin on {better} of {len(seeds)} weeks. B is ranked on {rb}, A on {ra}.")


if __name__ == "__main__":
    main()
