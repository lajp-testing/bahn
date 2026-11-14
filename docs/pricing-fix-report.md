# Pricing fix: the problem, the fix, the results (14 Nov)

Written for the next agent. Every number below is from saved weeks in `data/runs/` (track `t5`, played one world at a time) or from the 14:00 test final's saved reveal. Nothing is committed yet (see "State of the tree").

## 1. The problem

### What we saw
- **The 14:00 test final.**
  - We made €1,647 on 57 orders: €28.9 an order, the highest margin per order of any ranked team with real volume.
  - We finished 26th of 55 ranked teams. The top-10 median was 156 orders and €3,607; 10th place was €3,292.
- **From our reveal** (Thu and Fri; the test final started on Thursday):
  - 356 real quotes, 57 won (16%).
  - Dealers bought at about 1.2× list: we won 35 of 63 quotes at 1.0–1.2×, and 0 of 98 at 1.7× or higher.
  - Our median quote rose through the days: 1.35, 1.41, 1.51, 1.58× list.
  - Drivers were not the limit: 100% on time, 4 drops.
- **The practice rounds showed the same pattern.** In round "Saturday 12:00" we won about 317 orders a week against about 450 for the top 10, at a higher margin per order.

### The cause
The cause is the cost estimate inside `ProfitQuoter` (`dispatch/pricing.py`). I found it by replaying the test final offline through the mainline quoter with `tracks/t2/final_replay.py`; it reproduces our sent quotes to within 0.01–0.06× list.

- **The level was right.** It fell from 1.4 to about 1.05 and predicted 59 wins against 57 real ones. Correcting the level is not needed.
- **The queue charge was about 0** all week.
- **The cost was too high.**
  - With fee model 2 and `car=1.1`, the quoter expected won cars to cost **1.19× their typical fee**. From the ledger they really cost **0.92× on average** (median 0.85×).
  - The typical fee is about 0.96× the list price at level 8, so the cost floor alone sat at 1.08–1.26× list. The profit-maximising quote landed at 1.35–1.58×, above what dealers paid.
- **The ML fee model (`fee_model=3`, `tracks/ml/FINDINGS.md`) fixes the estimate.**
  - In the replay, `fee_model=3` with `car=1.0` expects 0.99× typical for the won cars, and the quotes fall to 1.17–1.30× list.

### A second, blocking problem: infinite recursion
`fee_model=3` together with the flat fee (`fee_flat=1`) crashed every week with endless recursion:

```
Fees.schedule → flat_schedule → flat_multiple → expected (model 3) → learned → features
  → schedule_features → Fees.schedule → flat_schedule → …
```

- The flat fee is set from the model's expected fee.
- One of the model's inputs is our fee schedule's opening and cap, which it gets by asking the fees part for a schedule.
- With the flat fee on, that schedule is the flat fee again.

The two switches had never been played together.

## 2. The fix

**Code:** one change, in `dispatch/features.py`, `schedule_features()`, 5 lines. This is the ML track's file.
- While computing the schedule input, it switches `fees.flat` off and restores it in a `finally`.
- So the model reads the ladder schedule that the same fees part would post with the flat fee off. Most of the model's training weeks posted that ladder (`tracks/ml/rows.py` takes the input from each car's first posted gig).
- No change to `desk.py`, `harness/` or the fees and quote logic.

**Settings:** no new code; these are existing switches, all passed with `--set` on `--policy main`.

```
safe_limit=80 safe_km=300 safe_near=0   # track 1's safe-car limit
fee_flat=1 fee_flat_up=-0.15            # track 3's flat fee (t3s15-safe-flat15)
fee_model=3                             # the ML fee and late-risk model (dispatch/learned.py)
car=0.95                                # the quoter's cost = 0.95 × the model's expected fee
```

**Offline checks:**
- `nix develop --command python -m pytest -q tests`: 24 passed, 1 skipped.
- A direct call with these settings returns a flat schedule, an expected fee (0.91× typical) and a quote. `fees.flat` is still on afterwards.
- `final_replay.py` with these settings runs the whole test final. Its quotes would have been 1.14–1.26× list, against the 1.35–1.58× we really sent.

## 3. Results

These are the 10 dev weeks, level 8, policy `main`, played one world at a time on track `t5` through `bin/vps`.

| Label | Settings | Margin | Orders | On time | Worst week | Ranked |
|---|---|---|---|---|---|---|
| `pr-main` | mainline defaults (`fee_model=2`, `car=1.1`) | €126,921.82 | 2,879 | 96.8% | 93.7% (dev-07) | 10/10 |
| `pr-m3-car10` | `fee_model=3 car=1.0` | €132,486.37 | 3,635 | 96.9% | 94.0% (dev-01) | 10/10 |
| `t3s15-safe-flat15` | safe limit + flat fee, `car=0.95`, model 2 (track 3's run, `tracks/t3/FINDINGS.md`) | €142,146 | about 3,710 | 95.4% | 92.7% (dev-07) | 10/10 |
| `pr-flat15-m3-car95v2` | the four settings above | €151,183.30 | 3,982 | 96.6% | 93.6% (dev-10) | 10/10 |
| **`pr-flat15-m3-car10`** | **the same, with `car=1.0`** | **€154,688.36** | **3,833** | **96.8%** | **94.8% (dev-10)** | **10/10** |

`pr-main` dev-01 equals `t1s11-base` to the cent (€8,764.79), so it is the plain mainline.

### Week by week, the new setting against the mainline

| Week | pr-main | pr-flat15-m3-car95v2 | Difference | Orders (new) | On time (new) |
|---|---|---|---|---|---|
| dev-01 | €8,764.79 | €10,437.08 | +€1,672.29 | 352 | 94.6% |
| dev-02 | €11,144.41 | €14,651.53 | +€3,507.12 | 389 | 96.4% |
| dev-03 | €15,704.45 | €17,811.62 | +€2,107.17 | 449 | 98.2% |
| dev-04 | €15,142.59 | €15,895.84 | +€753.25 | 410 | 97.3% |
| dev-05 | €9,559.35 | €10,929.47 | +€1,370.12 | 393 | 94.9% |
| dev-06 | €10,457.31 | €13,810.73 | +€3,353.42 | 381 | 99.0% |
| dev-07 | €13,047.78 | €15,937.88 | +€2,890.10 | 411 | 98.1% |
| dev-08 | €16,932.23 | €20,263.11 | +€3,330.88 | 446 | 96.4% |
| dev-09 | €11,805.70 | €15,626.53 | +€3,820.83 | 391 | 96.9% |
| dev-10 | €14,363.21 | €15,819.51 | +€1,456.30 | 360 | 93.6% |
| **Total** | **€126,921.82** | **€151,183.30** | **+€24,261.48, higher in 10 of 10** | 3,982 | 96.6% |

### Where the gain comes from
Totals over the 10 weeks, from the saved ledgers and reveals:

| | pr-main | pr-m3-car10 | pr-flat15-m3-car95v2 |
|---|---|---|---|
| Win rate of real quotes | 32% | 41% | 45% |
| Won quote / list (median) | 1.50 | 1.43 | 1.41 |
| Revenue | €320,184 | €393,984 | €415,614 |
| Driver fees | €187,026 | €255,135 | €256,721 |
| Driver fee / typical, per order (mean / median) | 1.059 / 0.950 | 1.050 / 0.950 | 1.016 / 0.912 |
| Late refunds and undelivered penalties | €5,295 | €5,406 | €6,841 |
| Done gigs with 1 / 2 / 3+ cars | 81 / 15 / 4% | 83 / 14 / 3% | 82 / 15 / 3% |

1. **A truer cost estimate wins more orders** (model 3, `car` ≤ 1.0). Quotes fall from about 1.50× to 1.41–1.43× list, and the win rate rises from 32% to 41–45%. With the old ladder fees, the extra cars come with their full fees: +€5,565.
2. **The flat fee carries the extra orders cheaply.**
   - Compared with `pr-m3-car10`: about 350 more orders for €1,586 more in driver fees. The fee per order falls from about €70 to about €64.50, and the median from 0.95× to 0.91× typical.
   - A ladder of raises teaches drivers to wait for the raise (handbook, "Drivers learn your fees"). A single fee near the car's need books at that fee.
   - The safe-car limit supplies the extra volume of short, non-private cars.
3. **The two help each other.** Separately they are worth +€5,565 (model 3) and +€15,224 (t3s15), about €20,800 in sum. Together they gain +€24,261, because the flat fee is set from the model's expected fee, so a better model makes each flat fee better.

### `car=1.0` against `car=0.95` (same other settings)

| Week | car=0.95 | car=1.0 | Difference |
|---|---|---|---|
| dev-01 | €10,437.08 | €10,261.79 | −€175.29 |
| dev-02 | €14,651.53 | €14,624.91 | −€26.62 |
| dev-03 | €17,811.62 | €17,643.30 | −€168.32 |
| dev-04 | €15,895.84 | €17,604.60 | +€1,708.76 |
| dev-05 | €10,929.47 | €10,838.65 | −€90.82 |
| dev-06 | €13,810.73 | €14,383.59 | +€572.86 |
| dev-07 | €15,937.88 | €16,819.06 | +€881.18 |
| dev-08 | €20,263.11 | €21,586.23 | +€1,323.12 |
| dev-09 | €15,626.53 | €14,940.51 | −€686.02 |
| dev-10 | €15,819.51 | €15,985.72 | +€166.21 |
| **Total** | **€151,183.30** | **€154,688.36** | **+€3,505.06, higher in 5 of 10** |

- **Fewer, better-paid orders.** `car=1.0` wins 149 fewer orders (3,833 against 3,982) at €40.4 an order against €38.0. The extra 5% discount at 0.95 bought orders that did not pay.
- **Safer.** The worst week rises from 93.6% to 94.8% on time; the three lowest are now dev-10 94.8%, dev-01 94.9% and dev-09 95.1%.
- **The margin gain is a lead.** dev-04 and dev-08 give +€3,032 of the +€3,505; the other eight weeks net out to +€473.
- **Choose `car=1.0` anyway.** The model's fee bias on held-out worlds is +0.003, so pricing at exactly its estimate needs no correction factor: "the quoter prices at the expected cost" has a one-sentence reason, and 0.95 was only a tuned number. Do not sweep `car` further on the dev seeds; the differences are too small to tell apart from fitting these 10 weeks.

**The recommended setting is now:**

```
safe_limit=80 safe_km=300 safe_near=0 fee_flat=1 fee_flat_up=-0.15 fee_model=3 car=1.0
```

## 4. Caveats
- **Chosen on the dev seeds.** These 10 seeds were used to pick between settings. The holdout seeds (`hold-01..10`, orchestrator only) have not been played with this setting.
- **One label per setting.** Every label is one week per seed, but the world is deterministic, so a replay gives the same result.
- **Bundling is unchanged.** 82% of gigs carry one car. Track 2's capacity study says multi-car gigs are where the top teams save, at 0.79× typical for 2 cars against 0.95× alone. That lever is still unused.
- **Late refunds rose** with the volume: €6,841 against €5,295. The worst week is 93.6%, a 3.6-point margin over the 90% minimum.
- **The test final started on Thursday** with no quotes from earlier days. The replay shows lower quotes, not what the extra orders would have done to on-time there.
- **Ignore `pr-flat15-m3-car95`.** It is a 1-week label in the index from the run that crashed before the fix.
- **A possibly leftover world.** At about 15:00 UTC one world was stalled at minute 0: `w594b987dc0f5c839ecd9`. It may be left over from the crashed runs, and its owner is unknown. Check on the practice machine before `harness.janitor --clean` (orchestrator only).

## 5. Next steps
1. **Holdout check** (orchestrator, `SPREAD_TRACK=orch`, one world at a time): play `main` with the recommended setting (`car=1.0`) on `--seeds holdout`, and the mainline on the same seeds. Adopt if the total is higher and all 10 are ranked with the worst week at 92% or higher.
2. **If it holds,** make the recommended setting the default in `dispatch/policies/main.py`. Then confirm the switch-off check still matches `t1s11-base` dev-01 (€8,764.79) with the new settings set back.
3. **Done:** `car=1.0` was played as `pr-flat15-m3-car10` (see above); it is the recommended value.
4. **Commit** `dispatch/features.py`, `tracks/t2/final_replay.py` and this report, with the label and its numbers in the message. The user hasn't asked for a commit yet; ask before committing.
5. **The 20:00 test final** is the outside check: compare orders, margin per order and on time with the 14:00 one.

## State of the tree
- **Modified, not committed:** `dispatch/features.py` (the fix).
- **New, not committed:** `tracks/t2/final_replay.py` (the offline replay) and this report.
- **Test-final data used here, outside the repo:** `/tmp/claude-final-events.json`, `/tmp/claude-final-reveal.json`, `/tmp/claude-final-snapshot.json`, `/tmp/claude-final-roster.json`. Replay with:

  ```sh
  python3 tracks/t2/final_replay.py /tmp/claude-final-{events,reveal,snapshot,roster}.json --set <key=value> ...
  ```
