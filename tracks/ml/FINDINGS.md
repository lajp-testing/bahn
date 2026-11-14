# Fee model 3: a learned cost model (plan: `docs/ml-plan.md`)

Status 14 Nov, about 14:45 UTC: steps 1–3 done offline. Not yet played: the switch-off check and the 30 + 10 week measurement.

## What it is

- `dispatch/features.py`: `features(request, desk)`, 44 inputs known at quote time. They cover the lane, the time, the cars and the note, the options, our own books, and our fee schedule's opening and cap. The same function serves training and quoting.
- `tracks/ml/rows.py`: replays every saved level 8 week through a desk that only keeps the books, and writes one row per won order (not cancelled). The targets are those of `tracks/t3/cost.py`: `fee` (fees over typical), `late` (any late refund or undelivered penalty) and `refund` (over the price). The fee model 1 and 2 predictions are computed for the same request at the same minute.
- `tracks/ml/train.py`: HistGradientBoosting, Poisson for `fee` and `refund`, log loss for `late`, depth ≤ 5, at most 24 leaves and 400 rows per leaf. The tree count is chosen on 6 training worlds held back for that. The script exports to `dispatch/learned.py` (plain Python, 2.3 MB, 0.13 ms per request, identical to sklearn on 2,000 rows).
- `dispatch/fees.py`: `--set fee_model=3` makes `Fees.expected` and `Fees.late_risk` use `dispatch.learned`. Models 1 and 2 are unchanged.

Rerun: `SPREAD_DATA=<data> python3 tracks/ml/rows.py` (27 min for 4,351 weeks on 18 processes; cached per week), then `nix develop --command python tracks/ml/train.py` (4 min).

## Offline result (holdout worlds hold-01..10, never trained on)

Training used 1,039,591 orders in 4,178 weeks of 44 worlds. The test was 41,497 orders in 170 weeks of 10 worlds: mean fee 1.070 of typical, late share 2.9%.

| | fee MAE | fee bias | late log loss | late Brier |
|---|---|---|---|---|
| constant | 0.309 | +0.047 | 0.133 | 0.0282 |
| model 1 | 0.283 | −0.030 | 0.171 | 0.0268 |
| model 2 (mainline) | 0.274 | −0.001 | 0.121 | 0.0263 |
| **model 3** | **0.232** | +0.003 | **0.101** | **0.0242** |
| model 3 without our own state | 0.243 | +0.008 | 0.103 | 0.0246 |

- **Calibration of `late`:** good in every decile. The top decile is 0.161 predicted against 0.179 actual; model 2's is 0.150 against 0.124.
- **Cheapest fifth by predicted fee per list euro:**
  - model 3: the cars really cost 0.687 per list euro, late 4.0%;
  - model 2: 0.774, late 4.2%.

  Model 3's dearest fifth is dearer (1.177 against 1.086) and later (4.2% against 2.5%), so it separates the cars better. Its cheapest fifth is still late 4% of the time, because cheap fees and late risk are different cars. The quoter prices both.
- **By group:** model 3 is better in every one: bundles on or off, cars that fit an open gig, private addresses, same-day options.
- **`refund`:** as a stand-in for `late` (refund/0.25) it is worse than the `late` model (log loss 0.112), so `late` stays.
- **Largest split gains:**
  - fee: typical fee 22%, schedule opening 15%, lead 9%, bundles on 5%, slack, fits;
  - late: orders held 17%, open gigs 7%, slack, private delivery, legs.

## Caveats

- **Double counting:** `fits` is an input, so the quoter's `pair` discount counts the same saving twice. Measure `fee_model=3` with `pair=0` as well as with the current `pair`.
- **Policy dependence:** our state and our schedule are inputs. The holdout rows come from many policies, but a policy that changes what we win changes those inputs (feedback). Only the online measurement can tell.
- **Fee tree count:** the fee model chose 493 of 500 trees, so a few more might help a little.
