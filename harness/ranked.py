"""Plays one approved ranking run on the TEST team, with a frozen policy. Nothing else creates ranking runs.

A ranking run counts in the practice rankings even when it fails or is deleted, so this entry:

- uses only the test team's key, SPREAD_TEST_KEY, and never SPREAD_KEY;
- plays only the frozen policy below, from a clean checkout at the commit named on the command line;
- checks the environment first, read-only: the clock is outside the low-capacity windows, no practice is
  paused for a test final, the test team has a free slot and no unfinished ranking run, and a ranking round is open;
- needs SPREAD_ALLOW_RANKED=L<level>:<token> with a token never used before (`harness.slots.approve_ranked`);
- never deletes the run on an error: a practice world stands still until advanced, so `--resume` goes on with it.

    python -m harness.ranked --check --commit <sha>                 the checks only; creates nothing
    SPREAD_ALLOW_RANKED=L8:<token> python -m harness.ranked --commit <sha>
    python -m harness.ranked --resume <world id> --commit <sha>     a ranking run that a stopped process left
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import subprocess
import urllib.request
from zoneinfo import ZoneInfo

from dispatch.policies import load

from . import config, slots
from .play import run_week

# The frozen candidate: the dial quoter (cost 1.3 typical fees, 1.1 with same_day), fees open at 0.85 x typical, same_day quoted when the car is ready a day later,
# the fee climb paused from 19:00 to 06:00, when drivers view but hardly book, the note reader (dispatch/reader.py),
# and long lanes (up to 600 road min, no same_day) through the volume gate at 1.15 x, with only within_3_days where both ends are thin.
POLICY, PARAMS, LEVEL = "reach", {"open": 0.85, "future_same_day": True, "quoter": "dial", "cost_next": 1.3, "cost_same": 1.1,
                           "night": True, "sleep": 19, "wake": 6, "notes": "read",
                           "long_lanes": True, "long_markup": 1.15, "thin_both": True, "thin_drivers": 20, "long_same_day": False}, 8
TRACK = "orch"
# Helsinki times when practice falls to 20 requests a second (test finals) or the final is set.
QUIET_NOT = [((5, 13, 45), (5, 14, 20)), ((5, 19, 45), (5, 20, 20)), ((6, 7, 30), (6, 8, 40))]  # (weekday, hour, minute)


def git(*args: str) -> str:
    return subprocess.run(["git", *args], capture_output=True, text=True, check=False).stdout.strip()


def checks(client: config.CountingClient, commit: str, resume: str | None) -> list[str]:
    """Every reason not to start now. Empty when the run may start."""
    problems = []
    head = git("rev-parse", "HEAD")
    if not commit or not head.startswith(commit):
        problems.append(f"HEAD is {head[:12]}, not the frozen commit {commit}")
    if git("status", "--porcelain", "--", "dispatch", "spread", "harness"):
        problems.append("the checkout has uncommitted changes in dispatch, spread or harness")
    now = datetime.datetime.now(ZoneInfo("Europe/Helsinki"))
    for (d1, h1, m1), (d2, h2, m2) in QUIET_NOT:
        if now.weekday() == d1 and (h1, m1) <= (now.hour, now.minute) < (h2, m2):
            problems.append(f"{now:%a %H:%M} Helsinki is inside a low-capacity window")
    if os.path.exists(config.PAUSE):
        problems.append(f"practice is paused ({config.PAUSE} exists)")
    worlds = client.worlds()
    open_worlds = [w for w in worlds if not w["ended"]]
    print(f"test team: {len(worlds)} worlds, {len(open_worlds)} not ended")
    for w in open_worlds:
        kind = "RANKING RUN" if w["boardRun"] is not None else "final" if w["kind"] == "final" else "practice"
        print(f"  {w['worldId']}  level {w['level']}  {kind}")
    if any(w["boardRun"] is not None and w["worldId"] != resume for w in open_worlds):
        problems.append("the test team has an unfinished ranking run: resume it instead")
    if not resume and len(open_worlds) >= 8:
        problems.append("the test team holds 8 worlds that have not ended")
    if not resume and open_worlds:
        problems.append("other practice worlds are open on the test team: the environment is not quiet")
    board = json.load(urllib.request.urlopen(f"{client.url}/v1/leaderboards/practice?level={LEVEL}", timeout=20))
    current = board.get("current")
    print(f"ranking round now: {current['name'] if current else None}")
    if not resume and not current:
        problems.append("no ranking round is open")
    return problems


def main() -> None:
    parser = argparse.ArgumentParser(description="Plays one approved ranking run on the test team.")
    parser.add_argument("--commit", required=True, help="the frozen commit; HEAD must be it")
    parser.add_argument("--check", action="store_true", help="run the checks only; create nothing")
    parser.add_argument("--resume", metavar="WORLD_ID", help="go on with a ranking run that a stopped process left")
    args = parser.parse_args()
    config.load_env()
    test_key = os.environ.get("SPREAD_TEST_KEY", "")
    if not test_key:
        raise SystemExit("SPREAD_TEST_KEY is not set. A ranking run uses only the test team's key.")
    client = config.CountingClient(key=test_key)  # never SPREAD_KEY
    problems = checks(client, args.commit, args.resume)
    for problem in problems:
        print(f"NOT READY: {problem}")
    if args.check or problems:
        raise SystemExit(0 if args.check and not problems else 1)
    board = True
    if args.resume:  # a ranking run, or a practice world to try the restart path on
        left = next((w for w in client.worlds() if w["worldId"] == args.resume), None)
        if left is None or left["ended"] or left["level"] != LEVEL:
            raise SystemExit(f"{args.resume} is not an unfinished level {LEVEL} world of the test team.")
        board = left["boardRun"] is not None
    label = ("ranked-" if board else "resumed-") + POLICY + "".join(f"-{k}{v}" for k, v in PARAMS.items()) + f"@{args.commit[:7]}"
    row = run_week(POLICY, load(POLICY), dict(PARAMS), LEVEL, None, label, TRACK, board=board, client=client, resume=args.resume)
    print(f"{'ranking run' if board else 'practice world'} {row['worldId']}: margin €{row['marginCents'] / 100:,.2f}  {row['wonOrders']} orders  "
          f"{row['onTimeShare']:.1%} on time  {'ranked' if row['ranked'] else 'NOT RANKED'}  {row['requests']} requests  {row['seconds']:.0f} s")


if __name__ == "__main__":
    main()
