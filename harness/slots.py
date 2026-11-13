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


def acquire(track: str, client: Client, wait: bool = True, keep: Optional[str] = None) -> Optional[Slot]:
    """Takes a free slot of the track, waiting for one when `wait`. Deletes a practice world that a dead process
    left in it, except `keep`. It never deletes a ranking run that has not ended: deleted, it would play to its
    end without the system and count. It stops instead, so the run can be resumed."""
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
            if stale and stale != keep:
                left = next((w for w in client.worlds() if w["worldId"] == stale), None)
                if left is not None and left["boardRun"] is not None and not left["ended"]:
                    slot.release()
                    raise SystemExit(f"Slot {index} holds ranking run {stale}, which has not ended. Resume it with "
                                     f"python -m harness.ranked --resume {stale}; deleting it would play it to its end without the system.")
                if left is not None and left["boardRun"] is not None:  # an ended ranking run: keep it, only free the slot
                    slot.record("")
                    return slot
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
def _held(track: str, client: Client, make, delete_on_error: bool = True, keep: Optional[str] = None) -> Iterator[World]:
    slot = acquire(track, client, keep=keep)
    assert slot is not None
    world: Optional[World] = None
    try:
        world = make()
        slot.record(world.id)
        yield world
        slot.record("")  # the caller played it to its end, or deleted it
    except BaseException:
        if world is not None and not delete_on_error:
            # A practice world stands still until it is advanced: leave it, and resume it later.
            print(f"World {world.id} is left as it was, not deleted. Resume it with python -m harness.ranked --resume {world.id}.", flush=True)
        elif world is not None:
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
    if board:
        if seed is not None:
            raise SystemExit("A ranking run has no seed: the server chooses it.")
        approve_ranked(level)
    return _held(track, client, lambda: client.create(level=level, seed=seed, board=board), delete_on_error=not board)


def adopt(client: Client, world_id: str, board: bool, track: Optional[str] = None):
    """A world that a stopped process left as it was, held in one of the track's slots, as a context manager.
    It is never deleted on an error: a ranking run counts even when deleted."""
    track = track or config.track()
    _check(track, None, board)
    def make() -> World:
        forget(world_id)  # the slot of the process that stopped still names it: the next process there would delete it
        return client.world(world_id)

    return _held(track, client, make, delete_on_error=False, keep=world_id)


def forget(world_id: str) -> None:
    """Clears `world_id` from every slot that no live process holds. A slot that this process holds is locked
    too, so the slot that adopts the world keeps its record."""
    for index in range(8):
        path = os.path.join(config.SLOTS, f"slot-{index}")
        if not os.path.exists(path):
            continue
        with open(path, "a+", encoding="utf-8") as file:
            try:
                fcntl.flock(file, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError:
                continue
            slot = Slot(index, file)
            if slot.left_behind() == world_id:
                slot.record("")
            fcntl.flock(file, fcntl.LOCK_UN)


APPROVAL = "SPREAD_ALLOW_RANKED"


def approve_ranked(level: int) -> str:
    """A ranking run counts even when it fails, so each one needs an explicit OK for that one run:
    SPREAD_ALLOW_RANKED=L<level>:<token>, with a token that no earlier ranking run used. The token is
    spent before the world is created, so one approval can never start two runs."""
    value, prefix = os.environ.get(APPROVAL, ""), f"L{level}:"
    token = value[len(prefix):].strip() if value.startswith(prefix) else ""
    if not token:
        raise SystemExit(f"A ranking run needs an explicit approval for this one run: {APPROVAL}={prefix}<token>.")
    os.makedirs(config.DATA, exist_ok=True)
    with open(os.path.join(config.DATA, "ranked-approvals.txt"), "a+", encoding="utf-8") as spent:
        fcntl.flock(spent, fcntl.LOCK_EX)
        spent.seek(0)
        if token in spent.read().split():
            raise SystemExit(f"The approval {value} has been used: each approval covers one ranking run.")
        spent.write(token + "\n")
    return token


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
