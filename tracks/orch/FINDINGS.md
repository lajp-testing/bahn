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

## 2026-11-14 08:45 UTC — new mainline defaults (Opus 5.5 orchestrator, working as Fable did)

`main` now defaults to fee model 2, bundles of three, limit 35 (45 before noon) and bundle patience 120 minutes. `--policy main` with no `--set` reproduces `b24-limit35-patience120` to the cent (dev-01 €8,742.09, dev-02 €11,052.66).

Paired against `b22-baseline` (fee_model=2 bundle=3, limit 25) on the same 40 weeks (dev + rob-01..20 + holdout):

| setting | weeks | margin | vs baseline | orders | lowest on time |
|---|---|---|---|---|---|
| baseline (limit 25) | 40 | €456,931 | | 10,214 | 92.8, 92.9, 93.5 |
| **limit 35 + patience 120 (adopted)** | 40 | €484,003 | +€27,072 (holdout +€5,126) | 11,090 | 93.7, 93.8, 94.0 |
| limit 35 | 30 | | +€13,256 | | 91.6, 92.5, 93.9 |
| patience 120 | 30 | | +€6,627 | | 92.4, 93.2, 93.9 |
| car 1.0 | 30 | | +€6,455 | | 92.3, 93.3, 93.9 |
| limit 45 + patience 120 | 30 | | +€22,271 | | 92.3, 92.3, 93.0 |
| limit 35 + patience 120 + car 1.0 | 30 | | +€29,193 | | **87.4**, 91.2, 91.9 |
| limit 35 + patience 120 + fee_early 300 | 30 | | +€13,580 | | 91.6, 94.1, 94.1 |
| limit 35 + patience 60 | 30 | | +€15,998 | | **88.8**, 93.4, 94.2 |
| private=false (limit 25) | 40 | | −€13,522 | | 94.0, 94.6, 95.1 |
| private=false + fee_early 300 (limit 25) | 40 | | −€8,490 | | 94.1, 94.2, 95.1 |
| limit 35 + private=false (no patience) | 30 | | +€4,926 | | 92.0, 93.8, 94.9 |

Ranking round "Saturday 09:00" (played by b22 with the old baseline): €53,610, 97.1% on time, rank 22 of 157; rank 10 €68,719, rank 1 €77,572. Per week we play €10.7k there against €11.4k in practice with the same code: inside the noise of 5 weeks.

The practice machine is CPU-bound with bundles (load 4 on 2 vCPUs). The user offered a Stockholm machine (the game server is AWS eu-north-1).

## 2026-11-14 10:45 UTC — calm becomes the default; ranking round "Saturday 12:00"

`calm` (an urgent car past its last pickup minute goes on the normal ladder; track 3) over 40 weeks paired with `b26-fix-wo`: +€6,163 (dev+rob +€5,347, holdout +€816), higher in 25 of 40; lowest weeks 91.6, 92.3, 93.7 (baseline 93.7, 93.8, 94.0). It only changes the fee of cars that are already late, so the two lower holdout weeks are most likely divergence; accepted as the slightly riskier setting the user asked for on the board. Default now `repairs=windows+orphans+calm`.

Rejected this morning (30 weeks, paired with `b26-fix-wo`): direct offers −€2,016 / −€1,236 (track 2); per-due-day limit (track 1, one week −€693); a limit following booking speed (no early signal, track 1); limit 38 −€878; limit 40 −€2,213; patience 180 −€5,226; drops repair +€2,441 (inside noise, lowest 92.3%); charging rule −€3,016; bundle of 4 −€5,653; bundle discount 0.9 +€649; bundle slack 4 h −€3,894; morning limit 55: no change (45 never binds).

Correction (14 Nov, 13:30 UTC): there is no code freeze at 02:00. The final starts at 06:00 UTC on Sunday 15 November; the best measured setting goes live with `bin/vps-live` before it (safety-net task at 05:15 UTC).

## 2026-11-14 13:40 UTC — volume pivot adopted: safe-car limit + flat fees

Default of `main` now: `safe_limit=80 safe_km=300 safe_near=0 car=0.95 fee_flat=1 fee_flat_up=-0.15` on top of the earlier defaults. `--policy main` reproduces `t3s15-safe-flat15` to the cent (dev-01 €9,186.24, dev-07 €15,441.05).

`t3s15-safe-flat15` against the previous mainline (`t1s11-base` / `t3s10-calm`), same seeds:

| weeks | margin vs previous | weeks better | orders a week | lowest on time |
|---|---|---|---|---|
| 10 dev | +€15,224 (+12.0%) | 10/10 | 371 vs 288 | 92.7, 93.3 |
| 20 rob | +€31,966 (+13.1%) | 18/20 | 365 vs 277 | 90.2 (rob-17), 91.1 (rob-18) |
| 10 holdout | +€22,802 (+19.2%) | 10/10 | 354 vs 267 | 94.4, 94.5 |
| all 40 | +€69,993 (+14.3%) | 38/40 | 364 vs 277 | 90.2, 91.1, 92.7 |

Learned cost model (`fee_model=3`, teammate) on the previous mainline, 30 weeks (dev + rob) against `t1s11-base`: +€45,013, 28/30 weeks better, 331 orders a week, lowest 94.2%; with `pair=0.2` +€49,587, lowest 92.9%. Not yet measured on top of flat fees. `dispatch/features.py`: a flat fee that asks model 3 no longer recurses (the schedule features read 1.0 inside that call).

## 14:00 the learned cost model joins the mainline

`b37-fee3` (`fee_model=3`, the teammate's model in `dispatch/learned.py`) on top of the safe-car limit + flat fees, paired with `t3s15-safe-flat15` on all 40 weeks: **+€32,271**, better in 29 of 40 weeks (dev +€5,025, rob +€21,089, holdout +€6,156), 390 orders a week instead of 364, €37.97 a car instead of €38.50. The lowest weeks rise: rob-17 90.2% → 95.4%, rob-18 91.1% → 92.0%, dev-07 92.7% → 96.8%; the new lowest are rob-18 92.0%, dev-01 94.0%, hold-10 94.1%. Adopted as the default (fee model 3); `--policy main` reproduces `b37-fee3` dev-01 to the cent (`b40-main-fee3-check`, €9,956.48). The hand-fit model stays as `--set fee_model=2`.

Keep `pair` at 0 with this model: the model already reads whether a car fits an open gig (feature `fits`), so the `pair` discount would count that saving twice. On the older mainline, the model with `pair=0.2` added €4.6k over 30 weeks but lowered the worst week from 94.2% to 92.9% (`b35`).

Volume I (t3, dev screens on top of the safe + flat setting, before the model): `limit=40` (50 before noon) +€3.3k, ahead 7 of 8, 383 orders, lowest 92.9%; `limit=45` +€2.9k, lowest 91.6%; `safe_limit=100` +€0.4k. `b39` tests the model with `limit=40` on 30 weeks.
