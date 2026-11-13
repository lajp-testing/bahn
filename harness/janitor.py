"""Shows the team's practice worlds that have not ended and who holds which slot.

    python -m harness.janitor              list them
    python -m harness.janitor --clean      orchestrator only: delete the worlds that a dead process of ours left in a slot

It never deletes a ranking run: a deleted ranking run plays to its end without the system, and counts.
"""
from __future__ import annotations

import argparse
import fcntl
import os

from spread.client import SpreadError

from . import config


def held() -> dict[str, tuple[int, bool]]:
    """World id -> (slot, whether a live process holds the slot's lock)."""
    worlds: dict[str, tuple[int, bool]] = {}
    for index in range(8):
        path = os.path.join(config.SLOTS, f"slot-{index}")
        if not os.path.exists(path):
            continue
        with open(path, "a+", encoding="utf-8") as file:
            try:
                fcntl.flock(file, fcntl.LOCK_EX | fcntl.LOCK_NB)
                live = False
                fcntl.flock(file, fcntl.LOCK_UN)
            except OSError:
                live = True
            file.seek(0)
            world_id = file.read().strip()
            if world_id:
                worlds[world_id] = (index, live)
    return worlds


def main() -> None:
    parser = argparse.ArgumentParser(description="Lists the practice worlds that have not ended.")
    parser.add_argument("--clean", action="store_true", help="delete the worlds that a dead process of ours left in a slot")
    args = parser.parse_args()
    if args.clean and config.track() != "orch":
        raise SystemExit("Only the orchestrator cleans: another track's world may be mid-experiment.")
    client = config.client()
    slots = held()
    owner = {index: track for track, indexes in config.TRACKS.items() for index in indexes}
    alive = [world for world in client.worlds() if not world["ended"]]
    print(f"{len(alive)} of 8 practice slots in use")
    for world in alive:
        slot, live = slots.get(world["worldId"], (None, False))
        kind = "ranking run" if world["boardRun"] is not None else "final" if world["kind"] == "final" else "copy" if world["parent"] else "practice"
        where = f"slot {slot} ({owner[slot]}), {'held' if live else 'left behind'}" if slot is not None else "outside the broker"
        print(f"  {world['worldId']}  level {world['level']}  {kind:<11}  {where}")
        # A world outside the broker belongs to another system of the team on the same key: never touch it.
        if args.clean and slot is not None and not live and kind in ("practice", "copy"):
            try:
                client.world(world["worldId"]).delete()
                print("    deleted")
            except SpreadError as error:
                print(f"    not deleted: {error}")


if __name__ == "__main__":
    main()
