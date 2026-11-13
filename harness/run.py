"""Plays a policy on a set of seeds, as many weeks at once as the track has slots.

    SPREAD_TRACK=t1 python -m harness.run --policy base --seeds dev
    SPREAD_TRACK=t1 python -m harness.run --policy base --set markup=1.3 --set open=1.2 --seed dev-01 --seed dev-02
    SPREAD_TRACK=t2 python -m harness.run --policy base --level 6 --seed t2-study-1 --label my-experiment

A run is named by its label. Without `--label`, the label is the policy, its parameters and the code's
version, so a change to the code gives a new label. The world is deterministic: a week that the index
already holds for the same label, level and seed is not played again, unless `--again`.

Then compare two labels on the same seeds: python -m harness.compare <label A> <label B>

It plays practice weeks only. A ranking run goes through `harness.ranked`, with an approval for that one run.
"""
from __future__ import annotations

import argparse
import sys
import threading
import traceback
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from dispatch.policies import load, parse_params

from . import config
from .play import read_index, run_week

_print = threading.Lock()


def line(row: dict[str, Any]) -> str:
    ranked = "ranked" if row["ranked"] else "NOT RANKED"
    return (f"L{row['level']} {str(row['seed']):<12} margin €{row['marginCents'] / 100:>11,.2f}  revenue €{row['revenueCents'] / 100:>11,.2f}  "
            f"{row['wonOrders']:>4} orders  {row['onTimeShare']:6.1%} on time  {row['undeliveredShare']:5.1%} undelivered  {ranked:<10}  "
            f"{row['requests']:>5} req  {row['seconds']:>5.0f} s")


def default_label(policy: str, params: dict[str, Any]) -> str:
    settings = ",".join(f"{key}={value}" for key, value in sorted(params.items()))
    return f"{policy}{'[' + settings + ']' if settings else ''}@{config.git_version()}"


def main() -> None:
    parser = argparse.ArgumentParser(description="Plays a policy on practice weeks and saves the results.")
    parser.add_argument("--policy", default="base", help="a module of dispatch/policies (default base)")
    parser.add_argument("--set", action="append", default=[], metavar="KEY=VALUE", help="a parameter of the policy; repeat for more")
    parser.add_argument("--level", type=int, choices=range(1, 9), default=8)
    parser.add_argument("--seeds", choices=sorted(config.SEEDS), help="a seed set: dev (10 seeds) or holdout (orchestrator only)")
    parser.add_argument("--seed", action="append", default=[], help="one seed; repeat for more")
    parser.add_argument("--label", help="the name of this version in the index (default: policy, parameters and code version)")
    parser.add_argument("--again", action="store_true", help="play weeks that the index already holds for this label")
    args = parser.parse_args()

    track = config.track()
    params = parse_params(args.set)
    label = args.label or default_label(args.policy, params)
    build = load(args.policy)
    seeds: list[Any] = (config.SEEDS[args.seeds] if args.seeds else []) + args.seed
    if not seeds:
        parser.error("name the weeks: --seeds dev, or --seed <text>")

    done = {row["seed"]: row for row in read_index() if row["label"] == label and row["level"] == args.level and not row.get("board")}
    rows: list[dict[str, Any]] = [] if args.again else [done[seed] for seed in seeds if seed in done]
    todo = [seed for seed in seeds if args.again or seed not in done]
    print(f"label {label}  track {track}  level {args.level}  {len(todo)} weeks to play, {len(rows)} in the index already", flush=True)
    for row in rows:
        print("  (index) " + line(row), flush=True)

    failed: list[Any] = []

    def one(seed: Any) -> None:
        try:
            row = run_week(args.policy, build, dict(params), args.level, seed, label, track)
        except BaseException as error:  # the world is deleted; the other weeks go on
            failed.append(seed)
            with _print:
                print(f"  FAILED {seed}: {error!r}", file=sys.stderr, flush=True)
                traceback.print_exc()
            return
        rows.append(row)
        with _print:
            print("  " + line(row), flush=True)

    with ThreadPoolExecutor(max_workers=len(config.TRACKS[track])) as pool:
        list(pool.map(one, todo))

    if rows:
        ranked = sum(1 for row in rows if row["ranked"])
        orders = sum(row["wonOrders"] for row in rows)
        on_time = sum(row["onTimeShare"] * row["wonOrders"] for row in rows) / orders if orders else 0.0
        print(f"total over {len(rows)} weeks: margin €{sum(row['marginCents'] for row in rows) / 100:,.2f}  "
              f"{orders} orders  {on_time:.1%} on time  ranked {ranked}/{len(rows)}", flush=True)
    if failed:
        sys.exit(f"{len(failed)} weeks failed: {failed}")


if __name__ == "__main__":
    main()
