#!/usr/bin/env bash
set -euo pipefail
export SPREAD_TRACK=orch
rob=(); for i in $(seq -w 1 20); do rob+=(--seed "rob-$i"); done
python3 -m harness.run --policy main --label b23-limit35-privatefalse --set fee_model=2 --set bundle=3 --set limit=35 --set morning_limit=45 --set private=false --seeds dev "${rob[@]}"
echo 'batch done'
