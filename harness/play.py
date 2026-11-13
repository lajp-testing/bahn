"""Plays one practice week with a policy and saves what happened.

Each week gets a folder in the shared data folder (`config.RUNS`) with:

    result.json         the run: track, label, policy, parameters, code version, level, seed, score, requests, seconds
    events.jsonl.gz     every event of the week, one a line
    actions.jsonl.gz    every action the desk sent, with the minute and the world's answer
    reveal.json.gz      the reveal (API.md): quotes and outcomes, the truth of the cars won, the views
    snapshot.json.gz    the world at its end: orders and gigs, with fees and drivers
    roster.json.gz      the driver list

and one line in `config.INDEX`, which `harness.compare` reads.
"""
from __future__ import annotations

import fcntl
import gzip
import json
import os
import time
from typing import Any, Callable, Optional

from dispatch.context import Context
from dispatch.desk import DAY, Desk
from dispatch.parts import Parts
from spread.client import World

from . import config, slots

_MAP: Optional[dict[str, Any]] = None


def world_map(client) -> dict[str, Any]:
    """The map, the same in every world: read once and kept in the data folder."""
    global _MAP
    path = os.path.join(config.DATA, "map.json")
    if _MAP is None and os.path.exists(path):
        _MAP = json.load(open(path, encoding="utf-8"))
    if _MAP is None:
        _MAP = client.map()
        os.makedirs(config.DATA, exist_ok=True)
        with open(path + ".tmp", "w", encoding="utf-8") as file:
            json.dump(_MAP, file)
        os.replace(path + ".tmp", path)
    return _MAP


class Log:
    """The week's events and actions, written as they come."""

    def __init__(self, folder: str):
        os.makedirs(folder, exist_ok=True)
        self.events = gzip.open(os.path.join(folder, "events.jsonl.gz"), "wt", encoding="utf-8")
        self.actions = gzip.open(os.path.join(folder, "actions.jsonl.gz"), "wt", encoding="utf-8")

    def event(self, event: dict[str, Any]) -> None:
        self.events.write(json.dumps(event, ensure_ascii=False, separators=(",", ":")) + "\n")

    def sent(self, now: int, actions: list[Any], results: list[Any]) -> None:
        for action, result in zip(actions, results):
            self.actions.write(json.dumps({"at": now, "action": action, "result": result}, ensure_ascii=False, separators=(",", ":")) + "\n")

    def close(self) -> None:
        self.events.close()
        self.actions.close()


class LoggedWorld:
    """A world whose `act` also writes to the log. The desk sends some actions itself, between two steps of the clock."""

    def __init__(self, world: World, log: Log, now: Callable[[], int]):
        self._world, self._log, self._now = world, log, now

    def act(self, actions):
        results = self._world.act(actions)
        self._log.sent(self._now(), list(actions), results)
        return results

    def __getattr__(self, name: str):
        return getattr(self._world, name)


def play(world: World, ctx: Context, parts: Parts, log: Optional[Log] = None, until: Optional[int] = None) -> Desk:
    """Steps a practice world to its end, or to the minute `until`: from one event that needs an answer to the
    next, with one request a step. The clock also stops at each midnight and at each minute a part asked for."""
    snapshot = world.snapshot()
    ends_at = snapshot["endsAt"] if until is None else min(until, snapshot["endsAt"])
    desk = Desk(world, ctx, parts, snapshot["now"])
    if log is not None:
        desk.world = LoggedWorld(world, log, lambda: desk.now)  # type: ignore[assignment]
    while desk.now < ends_at:
        slots.wait_while_paused()
        midnight = (desk.now // DAY + 1) * DAY
        stop = min(ends_at, midnight, desk.next_timer() or ends_at)
        actions, desk.outbox = desk.outbox, []
        sent_at = desk.now
        step = world.advance(until=desk.wake_on, max=stop, actions=actions)
        if log is not None:
            log.sent(sent_at, actions, step["results"])
        desk.read_results(actions, step["results"])
        desk.now = step["now"]  # the minute at which the desk's answers will apply; each event has its own `at`
        for event in step["events"]:
            if log is not None:
                log.event(event)
            desk.handle(event)
        desk.tick()
    return desk  # with `until`, the answers to the last step are still in `desk.outbox`


def _dump(folder: str, name: str, value: Any) -> None:
    with gzip.open(os.path.join(folder, name), "wt", encoding="utf-8") as file:
        json.dump(value, file, ensure_ascii=False, separators=(",", ":"))


def run_week(policy: str, build: Callable[..., Parts], params: dict[str, Any], level: int, seed: Optional[str], label: str,
             track: str, board: bool = False) -> dict[str, Any]:
    """One week from creation to its saved result. Returns the result row."""
    client = config.client()
    started = time.time()
    with slots.create(client, level=level, seed=seed, board=board, track=track) as world:
        stamp = time.strftime("%Y%m%dT%H%M%S", time.gmtime(started))
        folder = os.path.join(config.RUNS, f"{stamp}-{track}-L{level}-{seed or 'board'}-{world.id}")
        roster = world.roster()
        ctx = Context.build(level, world_map(client), roster)
        log = Log(folder)
        try:
            desk = play(world, ctx, build(ctx, **params), log)
        finally:
            log.close()
        score = world.score()
        final = world.snapshot()
        _dump(folder, "snapshot.json.gz", final)
        _dump(folder, "roster.json.gz", roster)
        if not board:  # a ranking run has no reveal
            _dump(folder, "reveal.json.gz", world.reveal())
    row = {
        "at": stamp, "track": track, "label": label, "policy": policy, "params": params, "version": config.git_version(),
        "level": level, "seed": seed, "board": board, "worldId": world.id, **score,
        "refused": len(desk.refused), "requests": client.requests, "seconds": round(time.time() - started, 1), "folder": folder,
    }
    with open(os.path.join(folder, "result.json"), "w", encoding="utf-8") as file:
        json.dump({**row, "refusedActions": desk.refused[:200]}, file, ensure_ascii=False, indent=1)
    os.makedirs(config.DATA, exist_ok=True)
    with open(config.INDEX, "a", encoding="utf-8") as index:
        fcntl.flock(index, fcntl.LOCK_EX)
        index.write(json.dumps(row, ensure_ascii=False) + "\n")
    return row


def read_index() -> list[dict[str, Any]]:
    if not os.path.exists(config.INDEX):
        return []
    with open(config.INDEX, encoding="utf-8") as index:
        return [json.loads(line) for line in index if line.strip()]
