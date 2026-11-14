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

## 2026-11-14 07:30 UTC — complete paired comparison, new board round

Collected b16, b17, b18, b20 sequentially, once each; all inactive with `batch done`. Also collected b21 once: complete. Exact settings recovered from the original batch scripts. Reproducible comparison: `python3 tracks/orch/compare_handoff.py`; full 30-week table is `tracks/orch/handoff-comparison.md`.

Baseline (`fee_model=2 bundle=3`, b17 dev+rob): €344,275.32, weighted on-time 97.20%, 30/30 ranked. Lowest three: rob-18 92.86%, rob-14 93.49%, dev-07 94.19%. With b21 holdout: €456,930.64, 97.01%, 40/40 ranked; lowest three 92.80%, 92.86%, 93.49%.

Earlier urgent fees 300: 30-week €347,441.54 (+€3,166.22), 97.47%, all ranked, but worst 91.67% (then 94.67%, 95.77%). Across 40 weeks: €458,636.96, 97.30%, all ranked, worst still 91.67%. Not adopted: violates the no-worse-lowest-weeks criterion. 480 loses €3,556.15 over 30 weeks despite 97.90% on time; worst 91.76%. Outage loses €2,732.32, on-time 97.13%, worst 92.12%; stays off.

Older-code candidates: limits 35/45 gain €11,300.65 over 30 seeds at 96.60% on time, lowest 92.70/92.86/93.17%; car=1 gains €4,927.99 at 96.51%, lowest 92.68/93.47/93.75%; patience=120 gains €11,050.46 at 97.36%, lowest 92.35/94.61/95.06%. None qualifies. Bundle=5 improves the worst to 93.67% but loses €1,915.36 at 97.38%. These runs predate joining unsent gigs and are leads, not isolated current-code effects. Pair=0.15 has only 20 matching rob weeks (€229,538.25, 96.86%, lowest 92.41/92.70/94.57%); dev pair=0.20 is a different setting, so not combined. car=1 plus limit=35 has only 20 matching rob weeks (€243,931.74, 96.26%, lowest 91.03/91.86/92.28%); not adopted.

No new optional setting adopted, and defaults unchanged pending current-code validation. The explicit baseline remains the best supported operational setting; its 92.80% minimum is below the preferred final safety margin. New detached batch b22 is prepared in `tracks/orch/b22-validation.sh`: five sequential board runs with the explicit baseline, then three 40-week configurations (dev+20 rob+10 holdout): baseline; private=false; private=false plus fee_early=300. The latter two are experiments, not adopted settings. Budget 125 weeks across t1/t2/t3 and orch, all through harness slots; no delegates. No dispatcher/harness changes in this turn.

Board observed once at 07:25 UTC: season 5 `Saturday 09:00`, our played count 0. b22 checks the season and played count before consuming the remaining five runs. It stops the board lane on failure. Results and competitor comparison pending completion.

b22 launch succeeded; systemd reported `active` from frozen checkout `14ac6f9`. One-shot collection and board comparison scheduled for 08:30 UTC (no interim polling). Script syntax checked with `bash -n`; analysis script ran successfully and asserts complete paired seed sets. Policy code unchanged, so dispatcher tests were not rerun this turn.

## Automatic follow-up

User requires automatic analysis after detached batches complete, grouped to
reduce usage. A recurring T3 task now checks every 10 minutes and continues
analysis in this thread (task d31b62a7-1a68-4848-9683-0d94ce493820; first run
2026-11-14 07:39:34 UTC). This is a scheduled completion check, not a VPS push
notification. Cover all future detached launches with automatic follow-up.
Batches b16/b17/b18/b20/b21 have now ended. b21 results were pulled locally;
the next follow-up should analyse the full matched sets before promotion.

## Completion watcher and overlapping scheduled follow-up

The scheduled 07:25 follow-up already completed the analysis above and launched
b22-validation before this interactive turn saw its findings. An attempted
reuse of b22 was refused by systemd (existing unit); do not relaunch it or use
b22-safety.sh. Its existing log shows validation making progress. b23-safety
adds a 30-week current-code limit35/private=false test in orch's locked slot.
Do not duplicate b22 validation. Completion watcher bin/watch-batches retries
SSH errors/timeouts without exiting, requires a terminal `batch done` marker
and inactive service, and writes an atomic ready JSON after the threshold.
Webhook delivery unavailable (T3 Connect off); scheduled follow-up consumes
marker data/batch-ready-b22-b23.json. No notification is generated by exit alone.
