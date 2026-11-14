#!/usr/bin/env bash
set -euo pipefail
# Twenty weeks, sequentially in the orchestrator's single slot.
export SPREAD_TRACK=orch
python3 -m harness.run --policy main --label b21-bundle3-holdout --set fee_model=2 --set bundle=3 --seeds holdout
python3 -m harness.run --policy main --label b21-early300-holdout --set fee_model=2 --set bundle=3 --set fee_early=300 --seeds holdout
echo 'batch done'
