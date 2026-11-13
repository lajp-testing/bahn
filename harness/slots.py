"""The slot broker. Every practice world is created through it.

The team holds at most 8 practice worlds that have not ended. Each of the 8 slots is a lock file
in the shared data folder, and each track owns some of them (`config.TRACKS`). A process holds a
slot's lock while its world lives. When a process dies, the lock goes with it, and the next
process that takes the slot deletes the world that was left behind.

    with slots.create(client, level=8, seed="dev-01") as world:
        ...play it to its end...

Use `slots.fork(world)` the same way for a copy: a copy needs a slot too.
"""
from __future__ import annotations

import fcntl
import os
import time
from contextlib import contextmanager
from typing import Iterator, Optional

from spread.client import Client, SpreadError, World

from . import config


class Slot:
    def __init__(self, index: int, file):
        self.index, self.file = index, file

    def record(self, world_id: str) -> None:
        self.file.seek(0)
        self.file.truncate()
        self.file.write(world_id)
        self.file.flush()

    def left_behind(self) -> str:
        self.file.seek(0)
        return self.file.read().strip()

    def release(self) -> None:
        fcntl.flock(self.file, fcntl.LOCK_UN)
        self.file.close()


def acquire(track: str, client: Client, wait: bool = True) -> Optional[Slot]:
    """Takes a free slot of the track, waiting for one when `wait`. Deletes a world that a dead process left in it."""
    os.makedirs(config.SLOTS, exist_ok=True)
    while True:
        for index in config.TRACKS[track]:
            file = open(os.path.join(config.SLOTS, f"slot-{index}"), "a+", encoding="utf-8")
            try:
                fcntl.flock(file, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError:
                file.close()
                continue
            slot = Slot(index, file)
            stale = slot.left_behind()
            if stale:
                try:
                    client.world(stale).delete()
                except SpreadError:
                    pass  # it has ended or is gone already
                slot.record("")
            return slot
        if not wait:
            return None
        time.sleep(0.5)


def _check(track: str, seed: Optional[str], board: bool) -> None:
    if board and track != "orch":
        raise SystemExit("Ranking runs are for the orchestrator only: a ranking run counts even when it fails.")
    if seed and seed.startswith("hold-") and track != "orch":
        raise SystemExit("The holdout seeds are for the orchestrator only. Use the dev seeds or seeds of your own.")


@contextmanager
def _held(track: str, client: Client, make) -> Iterator[World]:
    slot = acquire(track, client)
    assert slot is not None
    world: Optional[World] = None
    try:
        world = make()
        slot.record(world.id)
        yield world
        slot.record("")  # the caller played it to its end, or deleted it
    except BaseException:
        if world is not None:
            try:
                world.delete()  # frees the slot; a world that has ended stays readable
                slot.record("")
            except SpreadError:
                pass
        raise
    finally:
        slot.release()


def create(client: Client, level: int, seed: Optional[str] = None, board: bool = False, track: Optional[str] = None):
    """A new practice world in one of the track's slots, as a context manager. On an error it deletes the world."""
    track = track or config.track()
    _check(track, seed, board)
    return _held(track, client, lambda: client.create(level=level, seed=seed, board=board))


def fork(world: World, track: Optional[str] = None):
    """A copy of a practice world in another of the track's slots, as a context manager. Delete the copy
    or play it to its end before the block ends; a copy left alive is deleted when the slot is next taken."""
    track = track or config.track()

    @contextmanager
    def held() -> Iterator[World]:
        slot = acquire(track, world.client)
        assert slot is not None
        copy: Optional[World] = None
        try:
            copy = world.fork()
            slot.record(copy.id)
            yield copy
        finally:
            if copy is not None:
                try:
                    copy.delete()
                except SpreadError:
                    pass
                slot.record("")
            slot.release()

    return held()


def wait_while_paused() -> None:
    """Runners wait here while the orchestrator has paused practice, for example during a test final."""
    while os.path.exists(config.PAUSE):
        time.sleep(5)
