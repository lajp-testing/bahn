"""Adds the rows of another copy of the index to this one, each week once.

    python3 -m harness.merge_index <other runs.jsonl>

The index lives on the practice machine and here. `bin/vps` merges that machine's copy into this one,
so rows that only one side holds are never lost.
"""
from __future__ import annotations

import fcntl
import json
import os
import sys

from . import config


def merge(other: str) -> int:
    os.makedirs(config.DATA, exist_ok=True)
    with open(config.INDEX, "a+", encoding="utf-8") as index:
        fcntl.flock(index, fcntl.LOCK_EX)
        index.seek(0)
        have = {json.loads(line)["worldId"] for line in index if line.strip()}
        added = 0
        for line in open(other, encoding="utf-8"):
            if line.strip() and json.loads(line)["worldId"] not in have:
                have.add(json.loads(line)["worldId"])
                index.write(line if line.endswith("\n") else line + "\n")
                added += 1
    return added


if __name__ == "__main__":
    print(f"{merge(sys.argv[1])} rows added to {config.INDEX}")
