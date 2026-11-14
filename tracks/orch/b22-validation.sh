#!/usr/bin/env bash
set -euo pipefail
# 125 weeks: five board runs; 40 baseline, 40 private=false, 40 private=false+early300.
# t1/t2/t3 own two slots each. Only orch uses the holdout and board slot.
ROB=()
for i in $(seq -w 1 20); do ROB+=(--seed "rob-$i"); done
run() {
  local track=$1 label=$2
  shift 2
  SPREAD_TRACK="$track" python3 -m harness.run --policy main --label "$label" --set fee_model=2 --set bundle=3 "$@"
}
board() {
  # A restart must not accidentally use a later round or replay five more runs.
  local played
  played=$(python3 - <<'PY'
import json, urllib.request
with urllib.request.urlopen('https://spread.bahnexpress.com/v1/leaderboards/practice?level=8', timeout=30) as response:
    current=json.load(response)['current']
assert current['season']==5 and current['name']=='Saturday 09:00', 'Ranking round changed: inspect before playing'
team=next(t for t in current['teams'] if t['team']=='pelaaja-juhlii')
print(team['played'])
PY
)
  for ((i=played+1; i<=5; i++)); do
    run orch "b22-board-s5-$i" --board
  done
}
run t1 b22-baseline --seeds dev "${ROB[@]}" & p1=$!
run t2 b22-private --set private=false --seeds dev "${ROB[@]}" & p2=$!
run t3 b22-private-early300 --set private=false --set fee_early=300 --seeds dev "${ROB[@]}" & p3=$!
# Keep all orch work sequential. Stop this lane on any board failure; never retry a consumed run.
(
  set -e
  board
  run orch b22-baseline --seeds holdout
  run orch b22-private --set private=false --seeds holdout
  run orch b22-private-early300 --set private=false --set fee_early=300 --seeds holdout
) & p4=$!
failed=0
for pid in "$p1" "$p2" "$p3" "$p4"; do
  wait "$pid" || failed=1
done
if ((failed)); then echo 'batch failed'; exit 1; fi
echo 'batch done'
