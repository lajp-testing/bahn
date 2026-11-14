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

## Retrain on the floor-0.75 weeks, 14 Nov evening

Model 4 was trained at about 15:00 UTC. Since then the mainline changed twice: `fee_model=4` and `car=1.1`
(fc3e132, 17:00), then flat-fee floors 0.75 / 0.95 and short lanes at `car_short=0.85` (fe7164a, 19:45). The
lower floors change the schedules drivers see (the inputs `sched_open` / `sched_cap`) and the fees paid, and
model 4 has seen almost none of those weeks. On the floor-0.75 holdout weeks it **overpredicts the fee by
0.076 of typical** (model 3 by 0.050), which feeds straight into the flat opening and the quote.

`tracks/ml/train.py` gained `--tier PREFIXES=WEIGHT` (repeatable, first match wins; a prefix is a label
prefix, or a commit meaning "policy main at that commit or later"), `--no-lean` (skips the model without our
own state) and `--shipped` now reports models 3 and 4. Defaults are unchanged. The two tiers:

- **floor-0.75 (tier 1):** labels `b68-floor`, `b70`, `b71-winner`, `b72`..`b82`, `g1-yard`, `g2-viewskm`, or main at fe7164a or later.
- **recent fee4 (tier 2):** labels `b52`, `b62`..`b67`, `b69`, or main at fc3e132 or later (and not tier 1).

Rows: rebuilt from all 6,701 saved level 8 weeks (`rows.py --jobs 11`, about 9 minutes with the per-week
cache, no week skipped): 1,964,366 orders. Training 1,900,930 orders in 6,468 weeks of 54 worlds; 780,561 of
them in recent-policy weeks (flat fees or later), of which **256,333 in 644 floor-0.75 weeks** and 142,806 in
386 recent fee4 weeks. Holdout 63,436 orders in 230 weeks of 10 worlds; tier 1 holdout = `b68-floor075-short095-carshort085`
hold-01..10 (3,765 orders, 10 weeks), tier 2 holdout = `b52-fee4-car110` hold-01..10 (3,475 orders, 10 weeks).

Candidates, all with `--recent-weight 3` (model 4's recipe) for the other flat-fee weeks:

| candidate | tier 1 / tier 2 weight | (a) all: fee MAE / late LL / Brier | (b) floor-0.75: fee MAE / bias / late LL / Brier | (c) fee4: fee MAE / late LL |
|---|---|---|---|---|
| A | 3 / 2 | 0.2066 / 0.1079 / 0.0262 | **0.1651** / +0.0067 / 0.1173 / 0.0289 | **0.1495** / 0.1227 |
| B | 6 / 2 | 0.2071 / 0.1081 / 0.0262 | 0.1657 / **+0.0051** / 0.1177 / **0.0286** | 0.1498 / 0.1228 |
| **C (pick)** | 3 / 3 | **0.2068** / **0.1077** / **0.0260** | 0.1663 / +0.0077 / **0.1170** / **0.0286** | 0.1499 / 0.1232 |

The three are within noise of each other on (b): 3,765 orders, 10 weeks, differences of 0.001 in fee MAE
and 0.0007 in log loss. **Pick C**: it is the best on (a) on all three metrics, the best on late log loss and
Brier on (b), within 0.0012 of A on fee MAE, and it is the simplest: every recent week weighted 3, which is
model 4's recipe on the new rows. So an online difference measures the new weeks, not a new weighting.
Exported to `dispatch/learned3.py` (2.5 MB, 500 / 324 / 163 trees, identical to sklearn on 2,000 rows),
behind **`fee_model=5`** in `dispatch/fees.py` (same feature function as models 3 and 4; both unchanged).

### (a) All holdout rows (63,436 orders, 230 weeks, 10 worlds; mean fee 1.044, late 3.1%)

| | fee MAE | fee bias | late log loss | late Brier |
|---|---|---|---|---|
| constant | 0.2792 | +0.0217 | 0.1395 | 0.0302 |
| model 2 | 0.2690 | +0.0299 | 0.1327 | 0.0292 |
| model 3 (shipped) | 0.2126 | +0.0064 | 0.1118 | 0.0269 |
| model 4 (mainline) | 0.2092 | +0.0100 | 0.1086 | 0.0262 |
| **model 5** | **0.2068** | **+0.0019** | **0.1077** | **0.0260** |

### (b) Floor-0.75 holdout rows (3,765 orders, 10 weeks, 10 worlds; mean fee 0.959, late 3.3%)

| | fee MAE | fee bias | late log loss | late Brier |
|---|---|---|---|---|
| constant | 0.2886 | +0.1073 | 0.1454 | 0.0319 |
| model 2 | 0.2989 | +0.1211 | 0.1602 | 0.0338 |
| model 3 (shipped) | 0.1934 | +0.0499 | 0.1318 | 0.0310 |
| model 4 (mainline) | 0.1935 | +0.0755 | 0.1283 | 0.0307 |
| **model 5** | **0.1663** | **+0.0077** | **0.1170** | **0.0286** |

### (c) Recent fee4 holdout rows (3,475 orders, 10 weeks, 10 worlds; mean fee 0.983, late 3.6%)

| | fee MAE | fee bias | late log loss | late Brier |
|---|---|---|---|---|
| constant | 0.2515 | +0.0835 | 0.1551 | 0.0347 |
| model 2 | 0.2585 | +0.1001 | 0.1623 | 0.0357 |
| model 3 (shipped) | 0.1672 | −0.0016 | 0.1387 | 0.0322 |
| model 4 (mainline) | 0.1564 | +0.0074 | 0.1327 | 0.0315 |
| **model 5** | **0.1499** | −0.0079 | **0.1232** | **0.0304** |

On all recent-policy holdout rows (21,939 orders, 60 weeks) model 5 has fee MAE 0.1545 against 0.1638 and late log loss 0.1210 against 0.1265.

- **What it means:** on the floor-0.75 weeks model 5 cuts fee MAE by 14% (0.194 → 0.166), removes model 4's
  +0.076 fee overprediction and cuts late log loss by 9%. Model 4 thinks the cars under the new floors cost
  more than they do, so it opens higher and quotes higher than it needs to.
- **Caveat, feedback:** a lower expected fee also lowers the flat opening (`sched_open`), which is an input
  of the same model. The offline numbers hold the mainline's schedules fixed; only `--set fee_model=5`
  online can tell whether the lower openings still book on time.
- **Speed:** 0.099 ms per request in plain Python (fee and late, 2,000 rows; model 4 0.090 ms on the same
  machine), well under the 1 ms budget. `tests/test_ml.py` covers the switch; 37 tests pass.
- Rerun: `SPREAD_DATA=<data> python3 tracks/ml/rows.py --jobs 11`, then
  `nix develop --command python tracks/ml/train.py --no-lean --shipped --name "model 5" --recent-weight 3 --tier <tier 1>=3 --tier <tier 2>=3 --out dispatch/learned3.py`
  (the full prefix lists are in the train.py docstring; about 10 minutes).
