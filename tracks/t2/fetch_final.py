"""Fetches a finished world's events, reveal and snapshot as JSON files.

Run on the practice machine (the key lives there):

    SPREAD_TRACK=t2 bin/vps python3 tracks/t2/fetch_final.py WORLD_ID OUTDIR

Writes OUTDIR/events.json, OUTDIR/reveal.json (when the world allows it) and
OUTDIR/snapshot.json. bin/vps copies tracks/ back, so the files land in the
worktree's OUTDIR too.
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from spread.client import SpreadError  # noqa: E402

from harness.config import client  # noqa: E402


def fetch_events(world) -> list[dict]:
    events, after = [], -1
    while True:
        batch = world.events(after=after, limit=1000)
        if not batch:
            return events
        events += batch
        after = batch[-1]["seq"]


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    world_id, outdir = sys.argv[1], sys.argv[2]
    os.makedirs(outdir, exist_ok=True)
    world = client().world(world_id)

    events = fetch_events(world)
    path = os.path.join(outdir, "events.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(events, fh)
    print(f"{len(events)} events -> {path}")

    try:
        reveal = world.reveal()
    except SpreadError as error:
        print(f"reveal refused: {error}")
    else:
        path = os.path.join(outdir, "reveal.json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(reveal, fh)
        print(f"reveal -> {path}")

    snapshot = world.snapshot()
    path = os.path.join(outdir, "snapshot.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(snapshot, fh)
    print(f"snapshot -> {path}")


if __name__ == "__main__":
    main()
