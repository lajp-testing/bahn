"""Fetch the driver list (roster) of an ended world: SPREAD_TRACK=orch bin/vps python3 tracks/orch/fetch_roster.py <worldId> <out.json>."""
import json, sys
import os
sys.path.insert(0, os.getcwd())
from harness import config
config.load_env()
c = config.client()
w = c.world(sys.argv[1] if len(sys.argv) > 1 else "f53b4661bfe50ae2e4c23")
r = w.roster()
json.dump(r, open(sys.argv[2] if len(sys.argv) > 2 else "roster.json", "w"))
print("drivers", len(r))
