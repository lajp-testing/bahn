# Orchestrator findings

## 2026-11-14 06:40 UTC — takeover

Read CLAUDE.md and HANDOFF.md. Main is clean at `2e178a7` (handoff documentation after `d603709`). No policy defaults changed: fee model 2 and bundles still require explicit settings.

Inspected b16, b17, b18 and b20 once each via `bin/vps-batch`; all four are active, none has reported `batch done`. Results pulled sequentially. Do not treat partial rob results as complete comparisons or adopt settings yet. No additional practice jobs or delegates started, leaving their lanes undisturbed.

Public practice board remains season 4, `Saturday 00:00`. Our five runs are already used: margin €49,200.29, on-time share 98.4824%, rank 41 of 154 listed teams. This is the old policy's result, not a measurement of bundles. No new board runs played.

T3 scheduled tasks were empty on takeover. Created one-shot tasks in the current thread:
- 14 Nov 07:25 UTC: collect batches, compare paired results, launch combination validation and arrange its follow-up; check board round once.
- 14 Nov 11:30 UTC: start/verify noon test-final runner, drain practice before 11:45; arrange post-final inspection.
- 14 Nov 17:30 UTC: start/verify evening test-final runner and arrange post-final inspection.
- 15 Nov 02:00 UTC: freeze measured mainline and document final settings.
- 15 Nov 05:15 UTC: start/verify real-final runner and arrange result inspection.

These are scheduled agent wake-ups, not evidence that a live runner has started. Current live service has not been inspected in this takeover turn. Continue using detached batches, sparse wake-ups, and only the user's specified GLM 5.3 configuration for any delegates.

## 14 November, orchestrator handoff resumed

Read HANDOFF.md and recovered the pending experiments. Batch b20 remains active;
its default outage detector finished dev at EUR 116,689.98, 97.0% on time,
10/10 ranked, with a lowest week of 93.96%. This does not justify adoption
against b17-unsent3 (approximately EUR 117,862).
The b16, b17 and b18 fresh-week results are still incomplete; do not compare
unpaired totals or promote defaults yet.

Started b21: 20 holdout weeks in the orchestrator's single slot, sequentially:
`b21-bundle3-holdout` versus `b21-early300-holdout`, both fee_model=2,
bundle=3, with fee_early=300 only in the latter. Script:
`tracks/orch/b21-holdout.sh`. This independently checks the strongest current
candidate while the existing fresh-week batches finish. No policy changes.
