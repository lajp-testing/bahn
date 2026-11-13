"""Where things are, who may use which practice slots, and the seed sets.

The team holds at most 8 practice worlds that have not ended, forks included. Each track owns
some of the 8 slots, so no track can starve another. `SPREAD_TRACK` names the track of a process.
"""
from __future__ import annotations

import os
import subprocess

from spread.client import Client

# The main checkout. Worktrees share its data folder and its key.
HOME = os.environ.get("SPREAD_HOME", "/home/agent/.t3/projects/bahn")
DATA = os.environ.get("SPREAD_DATA", os.path.join(HOME, "data"))
RUNS = os.path.join(DATA, "runs")  # one folder for each week played
INDEX = os.path.join(DATA, "runs.jsonl")  # one line for each week played
SLOTS = os.path.join(DATA, "slots")
PAUSE = os.path.join(DATA, "PAUSE")  # while this file exists, every runner waits (test finals)

TRACKS: dict[str, list[int]] = {
    "t1": [0, 1],  # intake and on-time
    "t2": [2, 3],  # quotes
    "t3": [4, 5],  # fees and drivers
    "t4": [6],  # notes
    "orch": [7],  # the orchestrator: holdout checks, ranking runs
}

SEEDS: dict[str, list[str]] = {
    "dev": [f"dev-{i:02d}" for i in range(1, 11)],  # for the tracks
    "holdout": [f"hold-{i:02d}" for i in range(1, 11)],  # for the orchestrator only: merge candidates
}


def track() -> str:
    name = os.environ.get("SPREAD_TRACK", "")
    if name not in TRACKS:
        raise SystemExit(f"Set SPREAD_TRACK to your track: one of {', '.join(TRACKS)}.")
    return name


def load_env() -> None:
    """Reads SPREAD_URL and SPREAD_KEY from the main checkout's .env when the shell has not set them."""
    path = os.path.join(HOME, ".env")
    if os.path.exists(path):
        for line in open(path, encoding="utf-8"):
            key, eq, value = line.strip().partition("=")
            if eq and key and not key.startswith("#"):
                os.environ.setdefault(key, value)


class CountingClient(Client):
    """A client that counts its requests."""

    requests = 0

    def call(self, *args, **kwargs):
        self.requests += 1
        return super().call(*args, **kwargs)


def client() -> CountingClient:
    load_env()
    return CountingClient()


def git_version() -> str:
    """The code's version: the commit, and a mark for uncommitted changes. It names a run's code."""
    def git(*args: str) -> str:
        return subprocess.run(["git", *args], capture_output=True, text=True, check=False).stdout.strip()

    commit = git("rev-parse", "--short", "HEAD") or "nogit"
    diff = git("diff", "HEAD", "--", "dispatch", "spread", "harness")
    if not diff:
        return commit
    import hashlib

    return f"{commit}+{hashlib.sha1(diff.encode()).hexdigest()[:6]}"
