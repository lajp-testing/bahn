"""Plays the final, or a test final, from the live stream. The clock moves by itself.

    python -m dispatch.live --policy base
    python -m dispatch.live --policy base --set markup=1.3

It waits for the organisers to set a final, rebuilds the books from the world, then answers events
as they come. Stop it and start it again at any time: it rejoins the same week. When the server
restarts or the network breaks, it waits five seconds and rebuilds.

A reader thread takes events off the stream. The desk answers every event that has arrived, then
sends its actions in one request: a burst of price requests costs one round trip, not one each.
"""
from __future__ import annotations

import argparse
import gzip
import json
import os
import queue
import sys
import threading
import time
from typing import Any, Callable, Optional

from spread.client import Client, SpreadError, Unreachable, World

from .context import Context
from .desk import DAY, Desk
from .parts import Parts
from .policies import load, parse_params

WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
IDLE = 1.0  # seconds without an event before the desk reads the clock and ticks


def report(label: str, score: dict[str, Any]) -> None:
    orders = f"{score['wonOrders']:>4} orders  {score['onTimeShare']:6.1%} on time  {score['undeliveredShare']:5.1%} not delivered"
    print(f"{label:<9}  margin €{score['marginCents'] / 100:>11,.2f}  revenue €{score['revenueCents'] / 100:>11,.2f}  {orders}", flush=True)


def next_final(client: Client) -> World:
    """The team's copy of the final that is set or runs now. Waits while none is set and while the last one has ended."""
    said = False
    while True:
        try:
            world: Optional[World] = client.world(client.final()["worldId"])
        except SpreadError as error:
            if error.status != 404:
                raise
            world = None
        if world is not None:
            snapshot = world.snapshot()
            if snapshot["now"] < snapshot["endsAt"]:
                return world
        if not said:
            print("No final is set. Waiting: the organisers set a test final 15 minutes before its start, and the final 30 minutes before.", flush=True)
            said = True
        time.sleep(10)


def read_stream(world: World, after: int, events: "queue.Queue[Any]", stop: threading.Event) -> None:
    """Puts each event of the stream in the queue; an exception too, so the desk can rebuild."""
    try:
        for event in world.stream(after=after, idle=IDLE):
            if stop.is_set():
                return
            if event is not None:
                events.put(event)
        events.put(StopIteration())  # the stream ended: the world is over or deleted
    except BaseException as error:
        events.put(error)


def play_live(world: World, level: int, world_map: dict[str, Any], build: Callable[[Context], Parts], log: Optional[Any] = None,
              clock: Optional[Callable[[], int]] = None) -> None:
    """Rebuilds the books, then answers events until the world ends. Raises `Unreachable` when the server is gone."""
    history = world.events()
    snapshot = world.snapshot()
    if snapshot["now"] >= snapshot["endsAt"]:
        return
    ctx = Context.build(level, world_map, world.roster())
    desk = Desk(world, ctx, build(ctx), snapshot["now"])
    desk.rejoin(snapshot, history)
    desk.send()
    clock = clock or (lambda: world.client.final()["now"])
    events: "queue.Queue[Any]" = queue.Queue()
    stop = threading.Event()
    threading.Thread(target=read_stream, args=(world, history[-1]["seq"] if history else -1, events, stop), daemon=True).start()
    slowest = 0.0
    try:
        while desk.now < snapshot["endsAt"]:
            day = desk.now // DAY
            try:
                batch = [events.get(timeout=IDLE)]
            except queue.Empty:
                batch = []
            while True:  # everything that has arrived by now
                try:
                    batch.append(events.get_nowait())
                except queue.Empty:
                    break
            if not batch:
                desk.now = max(desk.now, clock())
            started = time.perf_counter()
            ended = False
            for event in batch:
                if isinstance(event, StopIteration):  # the stream ended: answer what came before it, then stop
                    ended = True
                    break
                if isinstance(event, BaseException):
                    raise event
                desk.now = max(desk.now, event["at"])
                if log is not None:
                    log.write(json.dumps(event, ensure_ascii=False, separators=(",", ":")) + "\n")
                desk.handle(event)
            desk.tick()
            slowest = max(slowest, time.perf_counter() - started)
            desk.send()
            if ended:
                return
            if desk.now // DAY > day:
                report(WEEKDAYS[day % 7], world.score())
    finally:
        print(f"Slowest desk batch: {slowest:.6f} seconds (excluding final send).", flush=True)
        stop.set()


def main() -> None:
    from harness import config  # the key, the data folder and the map

    parser = argparse.ArgumentParser(description="Plays the team's copy of the final from the live stream.")
    parser.add_argument("--world", help="non-ranking practice world for rehearsal")
    parser.add_argument("--policy", default="base", help="a module of dispatch/policies")
    parser.add_argument("--set", action="append", default=[], metavar="KEY=VALUE", help="a parameter of the policy; repeat for more")
    args = parser.parse_args()
    params = parse_params(args.set)
    build = load(args.policy)
    config.load_env()
    client = Client()
    world_map = client.map()
    world: Optional[World] = None
    log = None
    try:
        while True:
            try:
                if world is None:
                    if args.world:
                        entry = next((w for w in client.worlds() if w["worldId"] == args.world), None)
                        if not entry or entry["kind"] != "practice" or entry.get("boardRun") is not None or entry.get("season") is not None:
                            raise SystemExit("--world requires a non-ranking practice world")
                        world = client.world(args.world)
                        level = entry["level"]
                    else:
                        world = next_final(client)
                        level = next((w["level"] for w in client.worlds() if w["worldId"] == world.id), 8)
                    folder = os.path.join(config.DATA, "rehearsal" if args.world else "final", world.id)
                    os.makedirs(folder, exist_ok=True)
                    log = gzip.open(os.path.join(folder, f"events-{int(time.time())}.jsonl.gz"), "wt", encoding="utf-8")
                    print(f"Final world {world.id}, level {level}, policy {args.policy} {params}.", flush=True)
                play_live(world, level, world_map, lambda ctx: build(ctx, **params), log,
                          clock=(lambda: world.snapshot()["now"]) if args.world else None)
                break
            except Unreachable as error:  # the server restarts, or the network broke: rebuild from the world
                print(f"spread: {error}. Rebuilding in 5 seconds.", file=sys.stderr, flush=True)
                time.sleep(5)
        score = world.score()
        report("End", score)
        print("Ranked." if score["ranked"] else "Not ranked.", flush=True)
        try:
            with gzip.open(os.path.join(folder, "reveal.json.gz"), "wt", encoding="utf-8") as file:
                json.dump(world.reveal(), file, ensure_ascii=False)
        except SpreadError as error:
            print(f"No reveal yet: {error}", flush=True)
    except KeyboardInterrupt:
        sys.exit("Stopped. The final world keeps running without the system: start it again at once.")
    finally:
        if log is not None:
            log.close()


if __name__ == "__main__":
    main()
