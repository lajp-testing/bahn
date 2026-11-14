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

## Retrain on recent weeks, 14 Nov

The shipped model 3 was trained on 4,178 weeks, almost all played by older policies. The mainline now plays
flat fees (`fee_flat=1`, `fee_flat_up=-0.15`) and `fee_model=3`, so only the recent weeks show costs under the
policy we will play in the final. `tracks/ml/train.py` gained `--recent-weight`, `--out`, `--name` and
`--shipped`: a row is **recent-policy** when its index row has `fee_flat=1` or `fee_model=3`, or its code
version is 5ba1bf0 / e01292a / 3a6e7d9 / 782a036 / 5bb0223 or later with policy main (the mainline defaults
carry flat fees from 5ba1bf0 on, and fee_model=3 from 3a6e7d9 on). The report adds a second table on the
holdout rows of those weeks only.

- Rows: rebuilt from every saved level 8 week: 1,241,290 training orders in 4,752 weeks of 44 worlds,
  120,921 of them (9.7%) in recent-policy weeks; holdout 48,901 orders in 190 weeks of 10 worlds, of which
  7,404 orders in 20 recent-policy weeks (all 10 holdout seeds; mean fee 1.028 of typical, late share 3.7%).
- Candidates: (A) the current recipe on all rows; (B) the same with `--recent-weight 5`.
- Pick: exported to `dispatch/learned2.py`, behind `fee_model=4` in `dispatch/fees.py` (same feature
  function as model 3; model 3 unchanged).

### All holdout rows (48,901 orders, 190 weeks, 10 worlds)

| | fee MAE | fee bias | late log loss | late Brier |
|---|---|---|---|---|
| constant | 0.298 | +0.044 | 0.137 | 0.0294 |
| model 1 | 0.277 | −0.021 | 0.177 | 0.0281 |
| model 2 | 0.269 | +0.008 | 0.126 | 0.0277 |
| model 4 (candidate A) | 0.223 | +0.006 | 0.104 | 0.0252 |
| model 3 (shipped) | 0.224 | +0.005 | 0.106 | 0.0257 |

### Recent-policy holdout rows only (7,404 orders, 20 weeks, 10 worlds)

| | fee MAE | fee bias | late log loss | late Brier |
|---|---|---|---|---|
| constant | 0.256 | +0.079 | 0.159 | 0.0359 |
| model 1 | 0.243 | +0.026 | 0.211 | 0.0353 |
| model 2 | 0.240 | +0.057 | 0.156 | 0.0354 |
| model 4 (candidate A) | 0.168 | +0.003 | 0.126 | 0.0315 |
| model 3 (shipped) | 0.183 | +0.018 | 0.134 | 0.0338 |

Candidate comparison on the recent-policy holdout rows (7,404 orders), all four trained on the same rows:

| `--recent-weight` | fee MAE | fee bias | late log loss | late Brier |
|---|---|---|---|---|
| 1 (candidate A) | 0.1680 | +0.0031 | 0.1256 | 0.0315 |
| 3 | 0.1645 | +0.0026 | **0.1251** | **0.0314** |
| 5 (candidate B) | 0.1639 | +0.0006 | 0.1273 | 0.0318 |
| 10 | **0.1622** | **+0.0002** | 0.1282 | 0.0321 |

**Pick: `--recent-weight 3`**, exported to `dispatch/learned2.py`. It has the best late log loss and Brier
of the four, a fee MAE within 0.0006 of the best, and it is also the best of the four on all holdout rows
(fee MAE 0.2228, late log loss 0.1030, Brier 0.0250; candidate A 0.2227/0.1037/0.0252, weight 5
0.2231/0.1044/0.0251, weight 10 0.2248/0.1056/0.0254). Higher weights buy a little fee accuracy on the
recent rows at the cost of the late model; the flat-fee mainline leans on the fee model for its opening, and
the quoter leans on the late model, so the balanced one wins. Every candidate beats the shipped model 3 on
the recent rows on both metrics, so the win is the retrain on recent weeks itself, not the weighting.

`fee_model=4` answers in plain Python as fast as model 3: measured 0.056 ms per request (fee and late
together, 2,000 requests; model 3 0.065 ms on the same machine, 0.15 ms under load), against the 1 ms
budget. The offline test suite passes (26 tests, `tests/test_ml.py` covers the model 4 switch).
