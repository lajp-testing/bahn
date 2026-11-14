# Track 3: fees and drivers

## For other tracks

Fourth stint: `Fees.expected(request, desk)` predicts the total driver fees in cents, using 0.966 times typical plus 0.076 for fewer than 30 drivers near pickup, 0.090 for fewer than 10 near delivery, 0.213 for a lane of at least 500 km, and 0.331 for any private address. These are additive and based on 824 non-cancelled orders in `t3-main-low20-v1` dev-01–06; term sample counts are respectively 338, 354, 92, 96 (overlapping). `Fees.late_risk` uses the same groups: −0.0017 + 0.0269 − 0.0130 + 0.0855 + 0.1676, clipped to [0, 1]. Both are observational, not causal, and use the first leg for location and distance; multi-leg and changed schedules are not separately calibrated. They are not yet wired into the quoter.

Validation on dev-07–10 (718 orders): mean absolute fee error €28.83 per order; actual total €84,793, predicted €83,740. Actual/predicted totals: sparse pickup €47,303/€45,927 (373), sparse delivery €36,575/€36,040 (265), long lanes €30,451/€31,382 (133), private €14,175/€14,400 (98). Actual/predicted late shares: all 4.7%/4.8%, sparse pickup 6.4%/5.8%, sparse delivery 6.4%/4.4%, long 12.8%/11.5%, private 14.3%/19.0%. These four weeks were not fitted; they still share the development seed set and older policy, with potential distribution shift under the new 24-hour slack rule. Fit and validation can be reproduced with `nix develop --command python tracks/t3/fit_expected.py`.

Fourth stint matched baseline `t3-stint4-baseline`, with slack=1440, private=true, queue_price=true, win_price=true: €64,350.29, 97.5% on time, 10/10 ranked; mean booked fee 1.107 times typical and 0.110 drops per booking. Worst week 96.4%. `t3-stint4-hold12` holds the opening until 12 hours before last pickup, then rises as low20: €41,405.87, 97.1% on time, worst 94.5%, 10/10; booked fee 1.038 and drops/booking 0.064. It loses €22,944.42 and wins 921 orders versus 1,768; delayed bookings filling the intake queue may explain the loss. `t3-stint4-rise60` changes only the interval to 60 minutes: €67,234.10, 97.9% on time, worst 96.1%, 10/10; mean booked fee 1.073, drops/booking 0.097. This is €2,883.81 above baseline, meeting the 93% floor, with 1,573 orders. `t3-stint4-rescue50` caps each urgent gig at 50% of its share of order price, a proxy rather than a guarantee of savings: €61,017.30, 96.3% on time, worst 94.1%, 10/10; mean fee 1.067, drops/booking 0.116. It loses €3,332.99 against baseline and is rejected. Its worst 12 orders all had zero driver fee and a double-price undelivered penalty; worst Salo–Rovaniemi −€1,189, versus baseline worst Ylivieska–Hyvinkää −€743 (also undelivered). Several baseline worst orders had fees above price, e.g. Salo–Rovaniemi €731 fee on €586 price. The cap prevents that expense but can prevent collection; the true counterfactual saving cannot be guaranteed from a schedule alone. The other hold schedules also lose margin: `t3-stint4-hold8` €47,130.49, 96.5% on time, worst 90.3%, booked fee 0.980, drops/booking 0.051; `t3-stint4-hold20` €43,329.92, 97.6%, worst 94.5%, fee 1.079, drops/booking 0.076. Both are rejected; hold8 also fails the 93% floor. `t3-stint4-rise120` made €61,252.52, 97.6% on time, worst 95.6%, booked fee 1.067, drops/booking 0.088; it loses €3,097.77 against baseline and is rejected. The t3 policy now defaults to the tested 60-minute interval; main still uses 20 minutes pending integration. The estimate is calibrated to low20, not the new t3 default, and must be recalibrated on rise60 before relying on it for quotes.

`t3-main-low20-v1` (opening density estimate + 0.15, +0.1 every 20 minutes to 1.5, starter urgent) on main: €54,426.26, 96.0% on time, worst 93.1%, 10/10 ranked; mean booked fee 1.128 times typical, 207 drops / 1,772 bookings. Main baseline: −€27,162.41, 97.1%, worst 94.9%, 10/10. Same seeds; notes differ from the older `t3-density-buffer-v1`, so its €37,962.14 is not a controlled comparison. Further schedules and flat control are running.

Third stint mainline baseline `t3-stint3-main`: −€27,162.41, 97.1% on time, worst 94.9%, ranked 10/10 on dev. New fee experiments are in progress; earlier `t3-density-buffer-v1` used starter notes, so it is not a same-parts comparison to main.

The complete `t1-limit15-later-price16-fee13` control (opening 1.3, 0.1 steps hourly) made €12,113.94 over 10 dev weeks, 96.2% on time, worst 93.2%, ranked 10/10. The 1.5 control made −€31,979, 96.0%, worst 93.4%, ranked 10/10; 1.1 made €37,221, 95.3%, worst 89.8%, ranked 9/10. The 1.3 control meets the 92% per-week threshold; 1.1 does not. The experimental `Fees.estimate` is a two-hour booking threshold, not total delivery cost; see its limitations below.

Fork scans on 39 single-car wins in three `t3-study-*` weeks give a two-hour mean least retained-booking fee of 0.64 times typical among 38 with a booking at 3.0; one found none at 3.0. Fewer than 30 drivers within 30 km of pickup: 0.75 (16 measured, one none); 30 or more: 0.57 (22). These are selected orders, not delivery costs or representative estimates: the parent continues alone, copies receive no further desk actions, and a retained booking is only observed through the horizon. Trade-ins were excluded and private addresses numbered three. The selected schedule uses 0.60 + 0.15 for sparse pickups; the later refitted `Fees.estimate` is experimental and not a calibrated full-order cost. The earlier buffer schedule opened 0.45 above that estimate and added two 0.15 raises at 30-minute intervals; the selected newer schedule is described above.

`t3-main-low15-v1` (estimate, +0.1 every 15 minutes to 1.5) made €54,109.09, 96.3% on time, worst 92.5%, ranked 10/10; mean booked fee 1.118 times typical, 0.112 drops per booking. It meets the hard floor but is less robust than low20 on its worst week and makes slightly less margin.

`t3-main-buffer-v1` reproduces the earlier density buffer on main: €42,764.86, 96.6% on time, worst 93.6%, 10/10; mean fee 1.238, drops/booking 0.100. Against it low20 gains €11,661.40 with worst week 93.1%. `t3-main-deadline240-v1` starts at the estimate, rises 0.1 per 15 minutes, compresses that interval to reach 1.5 at least 240 minutes before last pickup, and uses the starter urgent schedule: €50,427.29, 95.7% on time, worst 92.4%, 10/10, mean fee 1.129, drops/booking 0.114. The deadline rule and schedule are tested together; this does not isolate the deadline rule.

## Fifth stint: the cost model refit (fee model 2)

The old `expected`/`late_risk` (label low20) knew only four facts: drivers near the ends, a 500 km lane, a private address. It missed what the mainline's own weeks show most: when the pickup window opens and when the request arrives. `tracks/t3/cost.py` reads the label's saved weeks and prints what each won, non-cancelled order cost, as a share of the typical fee (y1: `driver_fee`+`waiting`+`failed_visit`+`release_fee` ledger lines) and whether it was late (y2: `late_refund` or `undelivered_penalty`).

### Step 1: what orders cost (`t3s5-fit`, 10 fresh mainline weeks, 2,717 orders; mean y1 1.077, mean y2 0.031)

| Lead to window × arrival | n | mean y1 | late y2 |
|---|---:|---:|---:|
| window open, before 12 | 417 | 1.106 | 0.050 |
| window open, 12–15 | 273 | 1.230 | 0.048 |
| window open, after 15 | 358 | 1.224 | 0.050 |
| ≤3 h, before 12 | 83 | 1.176 | 0.060 |
| ≤3 h, 12–15 | 54 | 1.182 | 0.000 |
| ≤3 h, after 15 | 87 | 1.150 | 0.034 |
| 3–12 h, before 12 | 27 | 1.087 | 0.000 |
| 3–12 h, 12–15 | 28 | 1.154 | 0.036 |
| 3–12 h, after 15 | 37 | 1.085 | 0.027 |
| 12–24 h, before 12 | 331 | 0.993 | 0.006 |
| 12–24 h, 12–15 | 329 | 0.989 | 0.009 |
| 12–24 h, after 15 | 391 | 0.951 | 0.031 |
| 24 h+, before 12 | 155 | 0.979 | 0.013 |
| 24 h+, 12–15 | 92 | 1.038 | 0.011 |
| 24 h+, after 15 | 55 | 0.982 | 0.036 |

| Group | n | mean y1 | late y2 |
|---|---:|---:|---:|
| option `next_day` | 1716 | 1.093 | 0.032 |
| option `same_day` | 879 | 1.048 | 0.031 |
| option `within_3_days` | 122 | 1.061 | 0.016 |
| private address | 101 | 1.332 | 0.257 |
| no private address | 2616 | 1.067 | 0.022 |
| lane < 50 km | 491 | 1.123 | 0.029 |
| lane 50–150 km | 629 | 1.049 | 0.029 |
| lane 150–300 km | 947 | 1.050 | 0.022 |
| lane 300–500 km | 514 | 1.083 | 0.033 |
| lane ≥ 500 km | 136 | 1.200 | 0.103 |
| < 10 drivers near pickup | 447 | 1.091 | 0.040 |
| < 30 near pickup | 297 | 1.122 | 0.030 |
| < 80 near pickup | 455 | 1.081 | 0.035 |
| 80+ near pickup | 1518 | 1.062 | 0.027 |
| < 10 drivers near delivery | 675 | 1.112 | 0.049 |
| < 30 near delivery | 577 | 1.096 | 0.031 |
| < 80 near delivery | 718 | 1.069 | 0.028 |
| 80+ near delivery | 747 | 1.038 | 0.017 |
| slack < 6 h | 10 | 2.259 | 0.700 |
| slack 6–12 h | 783 | 1.040 | 0.027 |
| slack 12–24 h | 164 | 1.037 | 0.049 |
| slack 24 h+ | 1760 | 1.090 | 0.027 |

The cheap, safe orders are those whose pickup window opens 12–24 h after arrival (y1 ≈ 0.98, late ≈ 1%); the dear, risky ones are ready at once or within 3 h (y1 ≈ 1.15–1.23, late ≈ 5%) and private addresses (y1 1.33, late 26%). Slack under 6 h is disastrous but rare (10 orders, y1 2.26, 70% late) — and slack depends on the option, so it cannot enter the per-request fee model.

### Step 2: the refit (model 2)

Fitted by least squares on the `t3s5-fit` weeks; every feature has at least 60 orders (least: lead 3–12 h, 83). The reference order: window opens 12–24 h away, arrives before noon, no private address, lane under 500 km, 30+ drivers near each end.

| Feature | expected2 (× typical) | late_risk2 |
|---|---:|---:|
| base | 0.9090 | −0.0075 |
| window opens ≤ 3 h after arrival (or already open) | +0.2041 | +0.0314 |
| window opens 3–12 h after arrival | +0.1343 | +0.0013 |
| window opens ≥ 24 h after arrival | +0.0323 | +0.0041 |
| arrives after 15:00 | +0.0368 | +0.0137 |
| arrives 12:00–15:00 | +0.0593 | −0.0045 |
| private address | +0.2642 | +0.2373 |
| lane ≥ 500 km | +0.1413 | +0.0823 |
| < 30 drivers near pickup | +0.0232 | +0.0048 |
| < 10 drivers near delivery | +0.0447 | +0.0218 |

Out of sample on the `t3s5-base` dev weeks (2,709 orders): fee MAE 0.229 of typical (old model 0.249); totals of y1 actual 2965, old 2816, new 2916. Predicted-risk bands, actual late share in each (old → new): under 2%: 2.3% (2011) → 1.1% (1324); 2–5%: 2.4% (463) → 3.6% (1034); 5–10%: 9.1% (77) → 4.3% (163); over 10%: 17.7% (158) → 18.1% (188). The new bands separate much better. Reproduce with `nix develop --command python tracks/t3/cost.py t3s5-fit t3s5-base`.

Wired in `dispatch/fees.py` as `model=2` (`MeasuredFees(model=2)`, `--set fee_model=2` on main); model 1 keeps the old coefficients. Option-dependent features (kind, slack) are excluded on purpose: `prices` asks for the fee once per request, before it prices the options.

### Step 3: playing model 2 (10 dev weeks each, same seeds)

| Label | Margin | Orders | On time | Worst week | Weeks better than base |
|---|---:|---:|---:|---:|---:|
| `t3s5-base` (model 1) | €105,898 | 2,709 | 96.6% | 93.4% | — |
| `t3s5-model2` (car 1.1, late 1.0) | €106,177.50 | 2,577 | 97.6% | 95.9% | 5/10 |
| `t3s5-model2-car10` | €103,246.59 | 2,851 | 96.1% | 91.9% | — |
| `t3s5-model2-car12` | €101,960.56 | 2,282 | 97.8% | 94.7% | — |
| `t3s5-model2-late2` | €98,564.03 | 2,438 | 98.2% | 94.8% | — |
| `t3s5-model2-late05` | €102,524.17 | 2,608 | 96.5% | 91.2% | — |

Model 2's margin gain over base is +€280 with 5 of 10 weeks better: noise by the margin rule, but the worst week rises from 93.4% to 95.9% and total on-time from 96.6% to 97.6%, with every week still ranked. It qualifies (higher total, better worst week) and is kept as the step 3 best. Both scales have an interior optimum at the defaults: `car` 1.0 loses margin and breaks the floor (dev-07 91.9%), 1.2 loses margin; `late` 2 loses €7,613, 0.5 breaks the floor (dev-07 91.2%). No end of a range won, so no further value was played.

The order mix moved towards the cheap, safe groups (`tracks/t3/shift.py`): orders whose pickup window opens at once or within 3 h fell from 45.6% to 34.6% of the won orders and their late share fell from 5.5% to 4.1%; the 12–24 h group rose from 40.0% to 49.0% (late 1.7% unchanged); 24 h+ rose from 11.7% to 13.8% (late 0.6% → 0.3%). The quoter prices the dear, risky ready-soon requests up, as the refit intended.

Note: the interrupted first attempt left dev-05–10 of `t3s5-model2` twice in the index (same margins, deterministic world); `harness.run` and `harness.compare` take one row per seed, but `harness.orders` counts both copies — `shift.py` dedupes.

### Step 4: where the fee opens (`far_open`, `soon_open`)

`MeasuredFees` gained two knobs, both 0 by default (`fee_far_open`, `fee_soon_open` in `FEES`): `far_open` comes off the opening when the first leg's pickup window opens 12 h or more after `desk.now`; `soon_open` goes on top when the car is ready within 3 h and the minute of the day is 15:00 or later. The opening rule itself (0.6, +0.15 sparse, +0.15 buffer) is unchanged; the knobs move it before the rise begins. Offline tests: 22 passed.

| Label | Margin | Orders | On time | Worst week | Verdict |
|---|---:|---:|---:|---:|---|
| `t3s5-far01` (far_open 0.1) | €95,730.65 | 2,489 | 96.6% | 90.4% | fails: −€10,167 and below the floor |
| `t3s5-soon015` (soon_open 0.15) | €103,597.77 | 2,745 | 96.4% | 92.9% | fails: −€2,300, floor held |
| `t3s5-model2-open` (model 2 + both) | €97,366.71 | 2,383 | 96.6% | 93.5% | fails: −€8,531 |

Both directions lose. Opening far-lead gigs lower books them too cheap: the far group was already the cheapest, safest one, and its fee cut is not repaid by extra wins. Opening ready-soon gigs higher after 15:00 loses margin as well, even though the ready-soon group is the dear one. The knobs stay at their default 0; the mainline's opening rule is unchanged, and the refit's pricing of the dear groups (step 3) is the only change this stint keeps.

## Fourth stint schedules (10 matched dev weeks each)

All use slack=1440, private=true, queue_price=true, win_price=true. Rescue50 changes urgent fees alone; other variants change normal timing alone. Every row ranked 10/10.

| Label | Margin | On time | Worst week | Booked fee / typical | Drops / booking |
|---|---:|---:|---:|---:|---:|
| `t3-stint4-baseline` (low20) | €64,350.29 | 97.5% | 96.4% | 1.107 | 0.110 |
| `t3-stint4-rise60` | €67,234.10 | 97.9% | 96.1% | 1.073 | 0.097 |
| `t3-stint4-rise120` | €61,252.52 | 97.6% | 95.6% | 1.067 | 0.088 |
| `t3-stint4-hold20` | €43,329.92 | 97.6% | 94.5% | 1.079 | 0.076 |
| `t3-stint4-hold12` | €41,405.87 | 97.1% | 94.5% | 1.038 | 0.064 |
| `t3-stint4-hold8` | €47,130.49 | 96.5% | 90.3% | 0.980 | 0.051 |
| `t3-stint4-rescue50` | €61,017.30 | 96.3% | 94.1% | 1.067 | 0.116 |

## Third stint schedules (10 dev weeks each)

| Label | Margin | On time | Worst | Ranked | Mean booked fee / typical | Drops / booking |
|---|---:|---:|---:|---:|---:|---:|
| `t3-stint3-main` | −€27,162.41 | 97.1% | 94.9% | 10/10 | 1.678 | 0.105 |
| `t3-main-buffer-v1` | €42,764.86 | 96.6% | 93.6% | 10/10 | 1.238 | 0.100 |
| `t3-main-low20-v1` | €54,426.26 | 96.0% | 93.1% | 10/10 | 1.128 | 0.117 |
| `t3-main-low15-v1` | €54,109.09 | 96.3% | 92.5% | 10/10 | 1.118 | 0.112 |
| `t3-main-deadline240-v1` | €50,427.29 | 95.7% | 92.4% | 10/10 | 1.129 | 0.114 |
| `t3-main-urgent18-v1` | €50,456.68 | 96.1% | 92.1% | 10/10 | 1.146 | 0.120 |
| `t3-main-refit-private-v1` | €54,095.35 | 96.3% | 93.7% | 10/10 | 1.133 | 0.112 |
| `t3-main-flat12-v1` | €46,293.91 | 95.3% | 91.4% | 10/10 | 1.200 | 0.086 |

The urgent variant changes low20's urgent opening from 1.5 to 1.8; the flat variant uses 1.2 throughout, including urgent. Flat falls below the 92% selection floor even though all weeks meet the game's 90% ranking rule. Booked fees include repeated bookings and reposts; drops are gig_dropped events, not no-shows. See `schedule_stats.py`.

Learning proxy, post day, all bookings: low20 Monday 310 bookings, mean booked/opening 1.304, mean 231 minutes; Friday 344, 1.398, 442 minutes. Flat Monday 314, 1.000, 183 minutes; Friday 358, 1.000, 442 minutes. Friday's higher relative fee under the rise is consistent with learning, but flat also books later; changes in workload, gig mix, reposting, and deadlines confound this observational comparison. It does not isolate driver beliefs or prove learning. The ratio uses each gig's opening, not the driver's first viewed fee. View events by event day: low20 Monday 4,555 (1,647 distinct seed-driver pairs), Friday 7,917 (2,617); flat Monday 2,193 (1,190), Friday 5,844 (2,377). These include views of gigs posted on earlier days.

## Expanded scan and refit

Six `t3-stint3-study-*` seeds produced 205 wins with an immediately postable gig, sampled every third eligible single-car win plus every eligible trade-in from seeds 3–6. The first two seeds sampled every third eligible order. There were 25 private-address orders and one trade-in; hour of day and pickup slack are recorded in the JSONL rows. Of 205, five found no retained booking at 3.0 in two hours. Among the other 200, the mean threshold was 0.728 times typical: 0.735 for 107 sparse-pickup observations and 0.719 for 93 dense-pickup observations; private 0.956 for 25, other 0.695 for 175. The one trade-in threshold was 1.359. Tight pickup slack under 24 hours: 26 measured mean 0.874, versus 174 measured mean 0.706 with more slack. Hour and slack are confounded with order mix. This selected sample does not establish no-driver probabilities, so no `chance` is proposed.

The candidate estimate is 0.70 times typical, plus 0.25 for any private address. This describes the retained-booking threshold, not a full delivery cost; the private premium is based on only 25 observations and the trade-in sample is insufficient to fit. Its ten-week policy test `t3-main-refit-private-v1` made €54,095.35, 96.3% on time, worst 93.7%, 10/10 ranked. This is €330.91 less than low20, so the selected schedule retains its old density opening independently of this experimental estimate. `t3-main-low20-refit-separate-v1` reproduced low20 exactly on all ten seeds: €54,426.26, 96.0% on time, worst 93.1%, ranked 10/10. The binary threshold assumes monotonicity: in `t3-stint3-grid-3`, all ten orders were monotone at both horizons on the 0.4–1.3 grid in 0.1 increments, then 1.5, 2.0 and 3.0. This is still not proof between grid points. Six additional `grid-2` orders were also monotone. Forks have no subsequent desk actions, and retained bookings may later drop or arrive late.

## Direct offers

An exploratory matched-copy study (`offers.py`) posted a flat gig at the refitted estimate and compared the app alone with the same app plus offers to three nearby drivers. Although the console connection ended, the copied file contains 30 comparisons from `t3-offer-study-1`: 11 bookings in each arm, with no booking unique to either arm within 11 minutes. Of 90 attempted offers, nine were refused because the gig had already booked; of 81 accepted offer actions, six were declined and 75 expired, with no offer acceptance. A decline proves a read, but an expired offer can be unread or made obsolete by another booking, so six is only a lower bound on reads. This single-seed, short-horizon study cannot establish a general offer effect or whether offers beat the app's true minimum fee; repeat across seeds and fee levels before deciding whether direct offers save fees.

## Findings table

| Measurement | Sample | Result | Limit |
|---|---:|---|---|
| Fork fee grid | 10 single-car orders, one study seed | Repeated 1.5 agreed; kept-booking outcomes monotone at 0.5 increments, at both horizons | Not proof of monotonicity between grid points or on other orders; future parent decisions are not replayed in copies. |
| Fork threshold scan | 39 single-car wins, 3 seeds | Two-hour mean 0.64; one none at 3.0; sparse pickup 0.75 vs 0.57 | Sampled every eighth eligible win; causal only for a fixed fee in the copied state. |
| `t3-density-buffer-v1` | 10 dev weeks | €37,962.14; 95.9% on time; worst 92.1%; 10/10 ranked | Meets 92% floor narrowly; changes fee levels and timing together. |
| t1 opening 1.3 | 10 dev weeks | €12,113.94; 96.2% on time; worst 93.2%; 10/10 ranked | Compared with 1.5 and 1.1 on the same seeds. |


In saved overloaded base dev runs, first posts with less than 3 hours to last pickup booked 5.8% and 4.6% of orders arrived on time (173 posts). Private-address orders arrived on time 38.4% versus 45.9% for others; trade-ins 22.5% versus 45.4% for single cars. These are associations under the overloaded starter, not predictions under a controlled intake. Treat tight slack and trade-ins as strong candidates for declining, not calibrated probabilities.

## Saved weeks: first posts

`python3 tracks/t3/analyse.py` reads all saved `base` dev runs (9,090 first posts, one run per dev seed). 58.4% of first posts received at least one booking; median booking was at 1.0 times the typical fee, 18 minutes after posting. This excludes bookings of later reposts and does not guarantee the driver completed the gig. 44.9% of these orders arrived on time. Cancelled orders and changes of plan are not separated; final last-pickup time can differ from its original value.

| Group | First-post booking | On-time order | Median minutes to first booking |
|---|---:|---:|---:|
| No driver living in pickup town (464) | 53.7% | 41.4% | 28 |
| 10+ living in pickup town (5,903) | 59.3% | 45.8% | 14 |
| Private address (1,198) | 46.7% | 38.4% | 50 |
| Trade-in (173) | 43.4% | 22.5% | 152 |
| Last pickup 3–12h away (2,259) | 25.1% | 23.8% | 12.5 |
| Last pickup 12h+ away (6,658) | 71.0% | 53.2% | 19 |
| Monday (2,323) | 83.7% | 70.3% | 6 |
| Friday (1,339) | 30.9% | 29.6% | 980.5 |

Friday median booking fee was 1.5 times typical, trade-ins 1.2, and the other groups above 1.0. Day, slack and load are confounded; exact-town counts omit neighbouring towns. Lanes over 300 km had 44.8% first-post bookings and 32.8% on time (2,348); lanes 150–300 km had 66.7% and 56.1% (2,783). With no driver within 30 km, 52.7% booked and 38.3% were on time (313); with 50 or more nearby, 60.1% and 46.4% (4,365). This is not an estimate of a causal fee effect.

## Experiments

`t3-m15-base-v1`: markup 1.5 with starter schedule, 10 dev weeks, total margin −€5,025.12, 3,823 orders, 77.0% on time, ranked 0/10. `t3-m15-flat15-v1`: flat 1.5 times typical, including after warning, total margin −€43,415, 3,957 orders, 76.5% on time, ranked 0/10. Flat won margin on 1/10 seeds and lost €38,390 in total. Neither qualifies as an improvement: neither ranks. The policy retains the starter schedule.

For the eight matched seeds with usable event logs, driver fees per delivered leg were €106.92 for the starter versus €113.70 flat; 538 drops from 3,579 bookings versus 482 from 3,626. Two flat runs (dev-03 and dev-04) have empty event files despite completed result rows, so these fee and drop figures exclude both pairs. These metrics include late deliveries, and different orders are won as trust evolves. The within-week Monday–Friday difference above cannot establish learning: workload and deadlines change too. Direct offers, alternative flat multiples and raise timings remain untested.

## What failed / limitations

The earlier starter fee experiment did not isolate a causal schedule effect. The starter's overloaded weeks do not identify the cost of timely transport; successful bookings are a selected subset, and later reposts are excluded from the first-post fee statistic.

## Provisional cost estimate

Across 8,819 orders with attributed driver-fee ledger entries, total attributed fees average 1.71 times the typical fee (median 1.5), including reposts. `Fees.estimate` exposes that unadjusted benchmark for the whole request; it is not an on-time cost or calibrated chance, and excludes orders with no attributed driver fee and other costs. It should not be used as a validated profitability model.

## Second stint limitations and next work

The fork method took 1,585 requests and 31.4 seconds for 10 grid checks, and 1,768, 1,124 and 2,204 requests for the three study weeks (15, 4 and 20 scans). Six binary rounds resolve 3.0 in steps of 0.046875, conditional on monotonicity; the ten-order grid cannot prove it. The warning horizon is clipped to one minute after posting when already inside the warning and to the end of the week. `none` means no retained booking at 3.0, not proof that no lower fee books. Copies advance without subsequent desk actions, and a booking held at the horizon may later drop or deliver late. The sample omits trade-ins and may differ from all orders.

`t3-density-buffer-v1` was compared with fee13 on the same 10 seeds: +€25,848.20, 95.9% versus 96.2% on time, worst 92.1% versus 93.2%, 10/10 ranked for both. Against fee11 it gained €741.14 and ranked 10/10 versus 9/10; against fee15 it gained €69,941.14, both 10/10. The scan and buffer were tested together; the test does not isolate the density term or prove the estimate predicts realised driver costs. A 92.1% worst week leaves very little room. Next: test more independent weeks and trade-ins, probe monotonicity more finely and isolate the density term, before using the estimate in quotes or intake. Direct offers and rising-versus-flat forks were not tested.

Offline tests: 9 passed with `SPREAD_ON_VPS=1`; without it the existing slot test fails on the local `REMOTE_ONLY` guard.

## Late cars and urgent fees, 14 Nov

Stint cut to 30 minutes, so this is offline analysis only; no week was played. Script: `tracks/t3/late_cars.py b26-fix-wol b26-fix-wo` (saved weeks, 30 seeds dev-01..10, rob-01..20).

**What the `late` repair did to its cars.** In `b26-fix-wol` it posted 121 orders again past `lastPickupAt`. Against the same orders in `b26-fix-wo`:

| Group | Orders | Fees, wol − wo | Refunds, wol − wo | Lateness |
|---|---|---|---|---|
| late in both labels | 91 | +€319 | −€475 (less refunded) | same: quartiles 15 / 18 / 62 h in both |
| on time in wo, late in wol | 25 | +€1,317 | +€1,531 | 23 h later (median) |
| not won or undelivered in one label | 5 | | | |

- In the 91 cars late in both labels, the late repost found a driver much sooner: the booking came a median 22 minutes after `lastPickupAt` instead of 121 (quartiles 4 / 22 / 107 against 32 / 121 / 270 minutes). The car still did not arrive sooner: 20 cars came more than an hour earlier and 20 more than an hour later. Overnight hours and site hours set the delivery time, not the booking minute. The repost opens on the urgent ladder at 1.50 times the typical fee and books at a median of 1.50. Net, these cars were roughly even (−€156 in cost).
- The 25 cars lost in wol had all been booked before `lastPickupAt` in wo, and in wol their gig was booked later or dropped. The weeks drift apart after the first change, so this is mostly path divergence: noise, not a mechanism. It makes up most of the −€1,837. `lastPickupAt` was not out of date: in all 121 cases the last value the world sent was before the repost minute.
- Tiers: 57 cars at 25% in both labels, 21 at 50% in both, 6 moved from 25% to 50% with the repair and 4 from 50% to 25%.

**Reading.** Once a car is past its last pickup minute, an earlier booking rarely moves its refund tier: most late cars sit in the 2 to 24 hour tier, and the delivery lands the next working morning either way. An urgent fee then buys nothing. This holds for the mainline too, which reposts the expired gig on the urgent ladder (`repost` → `fees_for` with `urgent`). So the lever is the fee of a car already late, not how soon it is posted again.

**Built, not measured.** Repair `calm` (`--set repairs=windows+orphans+calm`, off by default): in `Desk.fees_for` an urgent order past its `lastPickupAt` gets the normal measured ladder instead of the urgent one. Next, about 15 minutes of play: (1) `--seed dev-01 --set repairs=windows+orphans` with the new code, which must equal `b26-fix-wo` dev-01 (€8,742.09) to the cent; (2) `t3s9-calm` = windows+orphans+calm and `t3s9-late-calm` = windows+orphans+late+calm on the 30 seeds, paired with `b26-fix-wo`. Risk to watch: a late car on the slow ladder may drift from the 24-hour tier to the 50% tier; if so, add a guard that returns to the urgent ladder when deadline + 24 h − the drive comes near.

## `calm` measured, 14 Nov (stint 10)

Check: `t3s10-check` (main, repairs=windows+orphans, dev-01) = €8,742.09, equal to `b26-fix-wo` dev-01 to the cent, so the switch is inert when off.

**`t3s10-calm`** (`--set repairs=windows+orphans+calm`), 30 seeds dev-01..10 + rob-01..20, paired with `b26-fix-wo`:

| Label | Margin, 30 weeks | On time | Three lowest weeks |
|---|---|---|---|
| b26-fix-wo | €366,266.96 | 96.90% | dev-07 93.7%, rob-14 94.4%, rob-08 94.8% |
| t3s10-calm | €371,614.02 | 96.97% | dev-07 93.7%, rob-08 94.8%, rob-17 94.9% |

+€5,347 (+1.5%), higher in 20 of 30 weeks, every week ranked. Script: `tracks/t3/tiers.py b26-fix-wo t3s10-calm` (refund tiers of all orders, new).

- Fees −€6,618, refunds +€1,166: the normal ladder past `lastPickupAt` saves more fee than it costs in refunds.
- **The risk did happen:** 24 cars went from 25% to 50% back, and only 1 went the other way. Totals: 25% tier 170 → 138, 50% tier 50 → 66, 100% tier 3 → 7, undelivered 3 → 5. Other moves (on time ↔ late, 17+13 one way, 10+8+11 the other) are the usual path divergence.
- So the guard is worth doing: go back to the urgent ladder when a car is about to leave the 24-hour tier. Since `lastPickupAt` ≈ deadline − the drive, "deadline + 24 h − the drive" ≈ `lastPickupAt` + 24 h. If 24 cars × ~25% of a ~€300 price ≈ €1,800 comes back while the fee savings mostly stay, the guard is worth roughly +€1,000 to €1,500 over 30 weeks. Not measured.

**`t3s10-late-calm`** (`repairs=windows+orphans+late+calm`), only the 10 dev seeds (not enough time for 30): €127,381.46, 96.81% on time, lowest dev-07 93.4%, dev-10 95.2%, dev-03 96.2%. Against `b26-fix-wo` on dev: +€2,359, higher in 6 of 10. Against `t3s10-calm` on dev (€126,921.82, 96.77%): +€460 but higher in only 2 of 10, which is noise. With `calm`, `late` no longer loses (it lost €1,837 alone, `b26-fix-wol`), because its reposts no longer pay the urgent ladder. It does not earn anything either. Tiers the same as calm: 25% 54 → 40, 50% 24 → 30, 100% 1 → 3. **Reading:** `late` adds a part and gains nothing measurable, so leave it off.

**`t3s10-calm-guard`** (`repairs=windows+orphans+calm+guard`; past `lastPickupAt` the normal ladder, then the urgent ladder from `lastPickupAt` + 18 h), 10 dev seeds: €126,834.56, 96.77% on time, lowest dev-07 93.7%, dev-10 95.3%, dev-08 95.7%. Against `t3s10-calm` on dev: −€87, higher in 2 of 10, the same on-time share. The guard did not stop the slide: 25% back 42 → 41, 50% back 28 → 27, 100% back 1 → 5. **Reading:** the guard makes no difference, so leave it off. Cars that slide to the 50% tier probably cross it overnight or outside site hours, where a higher fee does not help, the same thing that made the urgent ladder useless. Recommendation: adopt `calm` alone (30 weeks +€5,347, 20/30 higher, every week ranked) and leave `late` and `guard` off.

## Stint 11: hold the ladder while a car has time (10:20 to 10:55 UTC, 14 Nov)

Question: does raising less while a car has plenty of time, and more when its time runs short, cut what we pay and keep the late tail down? Switches off: `main` = `b26-fix-wo` on dev-01 to the cent (€8,742.09, `t3s11-off`). Each variant on dev-01..10 + rob-01..20, `calm` off, paired with `b26-fix-wo` (€366,266.96, 96.90% on time, lowest 93.7 / 94.4 / 94.8, 8,424 orders, €43.48 per order).

| Label | Switch | Margin 30 wk | Δ vs b26-fix-wo | On time | Lowest 3 | Higher | Orders | € / order |
|---|---|---|---|---|---|---|---|---|
| `t3s11-hold720` | `fee_hold_until=720` (existing: raises start 12 h before `lastPickupAt`, counted in drivers'-day minutes) | €301,016.08 | **−€65,251** | 94.88% | 90.1, 91.0, 91.2 | 2/30 | 6,488 | 46.40 |
| `t3s11-back300` | `fee_backload=300` (new: wait at the opening fee, start the normal ladder as late as still reaches the cap 5 h of drivers' day before `lastPickupAt`) | €231,592.88 | **−€134,674** | 97.05% | 92.2, 95.1, 95.2 | 0/30 | 5,179 | 44.72 |

All 60 weeks ranked. **Reading:** both lose heavily, and not through fees: each order earns a little more (+€3 and +€1), but the desk wins 23% and 39% fewer orders. A held gig stays unbooked for longer, so it holds a place in the intake's queue (`limit`) for longer, and the intake quotes less work. `hold720` also loses on-time share (lowest week 90.1%, close to the 90% line): with quiet hours counted, 12 h of drivers' day often starts the ladder the evening before and ends it after the 3 h warning, so the gig reaches the urgent fees without having been near the cap.

Booked fee / fee at the booking driver's first view, and minutes from that view to booking, by day of booking (10 dev weeks, `tracks/t3/s11_viewratio.py`; per booking driver, so the numbers are lower than the brief's 1.12 / 1.19 / 1.33, which were first view by any driver):

| Day | `b26-fix-wo` | `t3s11-hold720` | `t3s11-back300` |
|---|---|---|---|
| Mon | 1.06, 26 min | 1.03, 14 min | 1.06, 36 min |
| Wed | 1.08, 82 min | 1.11, 179 min | 1.11, 152 min |
| Fri | 1.11, 84 min | 1.18, 306 min | 1.18, 263 min |
| after Sun | 29 gigs | 147 gigs | 181 gigs |

Holding the ladder does not teach drivers to book early: they wait longer (Friday 84 → 306 min) and book higher above the fee they first saw (1.11 → 1.18), because when the raise finally comes it comes in a run. **Recommendation:** keep `hold_until=0` and leave `backload` off (default 0, kept in the code as a measured negative). A fee schedule cannot be judged with intake held fixed: anything that keeps gigs open longer costs orders through the queue limit. The next fee experiment should go the other way (book sooner, e.g. a slightly higher opening for gigs with little time) or count a posted, unbooked gig less in the intake's queue while it still has many hours.

## Stint 12: rescue the single-car tail before the 3-hour warning (11:20 to 11:50 UTC, 14 Nov)

Track 1 found that weak weeks lose on single gigs that book only in the last two hours, often after a drop (75% posted more than once, 51% booked with under 4 h left; good weeks 53% and 30%). Holding fees back lost heavily (stint 11), so this rule only ever raises fees, and only on a car near its last pickup.

**Rule** (switch `--set fee_rescue=<minutes>`, off by default): a single-car gig that no driver holds, with fewer than `rescue` minutes of the drivers' day (07:00 to 21:00, as `MeasuredFees.after` counts) left before its `lastPickupAt`, goes at once to the top of its normal ladder (typical × `cap`, 1.5), so it books while a driver can still reach it. It does not touch urgent cars (the world's warning already gave them the urgent ladder) or cars past `lastPickupAt` (those are `calm`'s).

Where: `MeasuredFees.rescue`, `rescue_from`, `rescuing` and a one-step schedule in `MeasuredFees.schedule` (`dispatch/fees.py`, so every new post, repost and retry in the window opens at the top); `Desk.rescue`, called from `Desk.tick`, reprices existing gigs that cross the line or come back after a drop below the top (`dispatch/desk.py`, small: a `schedules` book of each gig's current schedule, filled from posts and accepted reprices and, after a restart, from the snapshot's gigs through `carry`; a wake-up at `rescue_from` on win and change). A drop leaves the gig's schedule as it was, so a dropped gig is repriced only if its fee is below the top. Nothing depends on state outside events, the snapshot and the replayed journal.

**Measured (test final at 12:00, so only two weeks):**

| Label | Seed | Margin | Orders | On time | Late or undelivered |
|---|---|---:|---:|---:|---:|
| `t1s11-base` | dev-01 | €8,764.79 | 246 | 97.6% | |
| `t3s12-off` (switch off) | dev-01 | €8,764.79 | 246 | 97.6% | equal to the cent |
| `t1s11-base` | dev-07 | €13,048 | 301 | 93.7% | 17 |
| `t3s12-rescue-smoke` (`fee_rescue=240`) | dev-07 | €13,307.26 | 304 | 93.8% | 17 |

On dev-07 the rule sent 16 rescue reprices. +€259 and the same 17 late orders: a lead at most, not a finding. Next: 30 weeks paired with `t1s11-base`, `fee_rescue=240` (and 360 if there is time):
`export SPREAD_TRACK=t3; bin/vps python3 -m harness.run --policy main --set fee_rescue=240 --seeds dev $(for i in $(seq -w 1 20); do printf -- '--seed rob-%s ' $i; done) --label t3s12-rescue240`, then `python3 -m harness.compare t1s11-base t3s12-rescue240` (all 30 weeks).

## A chain planner, 14 Nov

**Rule.** Every `bundle_plan` minutes, the cars whose gig no driver holds (one car, not urgent, no private address, not reposted late) are rebuilt greedily into chains: earliest last pickup first, then the open car whose pickup is nearest to the chain's last delivery, up to `bundle_reach` minutes of empty driving, while `Bundles.route` still finds a start (windows, opening hours, 11 hours of driving, the 6-hour `slack`) and up to `bundle` cars. A chain whose cars already form one gig is left alone; the others are withdrawn first and posted as one gig at the bundle fee (0.85 times the sum of the cars' own schedules). A car whose withdrawal failed (a driver booked it meanwhile) stays where it is. Code: `Bundles.tick` and `Bundles.chains` in `dispatch/bundles.py`; `route` takes a `reach` override. Off by default (`bundle_plan=0`). The plan comes from the desk's books, so it adds no state that `rejoin` has to rebuild.

**Off check.** `t3s13-off` dev-01: €8,764.79, 246 orders, 97.6%: equal to `t1s11-base`.

**Screen on dev-01..10** (a screen, not a finding). "In a gig with others" means delivered cars whose gig carried more than one car (`report_dev.py`, which is `tracks/t5/report.py` limited to the dev seeds).

| label | settings | margin € | orders | on time | lowest 3 weeks (on time) | cars with others |
|---|---|---|---|---|---|---|
| `t1s11-base` | | 126,922 | 2,879 | 96.8% | dev-07 93.7%, dev-10 95.3%, dev-08 96.0% | 877 / 2,877 = 30.5% |
| `t3s13-plan60` | plan 60, reach 60 | 126,158 (−763) | 2,883 | 96.8% | dev-07 91.5%, dev-03 95.2%, dev-09 96.0% | 927 / 2,881 = 32.2% |
| `t3s13-plan90` | plan 60, reach 90 | 127,005 (+83) | 2,883 | 96.4% | dev-07 91.3%, dev-08 94.7%, dev-01 95.9% | 906 / 2,881 = 31.4% |

Bundles by size (posted, kept a driver, delivered): base 2: 688/310/615, 3: 152/88/262; plan60 2: 1,141/307/611, 3: 330/107/316; plan90 2: 1,309/285/564, 3: 449/115/342. Single-car gigs posted: 2,782 base, 3,479 plan60, 4,043 plan90.

**What it shows.** The planner posts many more bundles, but about as many are booked: the share of cars in a shared gig moves from 30.5% to only 31 to 32%. Margin is flat (±€800 over 10 weeks, with week-to-week swings of ±€1,800), and dev-07 drops to 91.3–91.5%, close to the 90% line. The reason: a single car is booked in a median of about an hour, so when the planner runs, few cars are open, and those are mostly cars nobody wants. Rebuilding them reshuffles the leftovers and makes more posts and withdrawals (more single-car posts, because chains that lose a member fall back to one gig per car), not more cars per driver. Pooling the cars that are open at one moment cannot raise the share much: the chain has to exist before a driver takes the first car.

**Next.** (1) Hold a newly won car back for part of the plan interval (when its last pickup is far away) so the planner sees a larger pool. This trades booking speed for chain length, and the 6-hour slack keeps it safe. (2) Offer a chain to the driver who just booked its first car (a direct offer of the follow-on gig, as the t2 rides-home idea did), rather than reposting to everyone. (3) Count the driver-days used, not only the share.

## Flat fees at high volume, 14 Nov

**The rule.** With `fee_flat=1`, a gig opens at one fee and keeps it. That fee is the fee model's expected multiple of typical plus `fee_flat_up`, kept between 0.85 and the cap (1.5). The floor is 1.15 for a lane under 40 km or a car under 5 hours before its last pickup. The fee goes up one `fee_flat_step` (0.15) after `fee_flat_wait` (6 h of the drivers' day) without a booking, and one step more `fee_flat_last` (24 h) before the last pickup. At the deadline warning it takes the urgent fees, as now. After a drop it gets back the fee it was booked at, with no climb. Why: few raises, so drivers have no next raise to wait for. The schedule is a function of the request and the minute only, so after a restart the desk posts the same schedule. Code: `MeasuredFees.flat_multiple` and `flat_schedule` in `dispatch/fees.py`; `Desk.after_drop` gets a three-line flat branch. Off by default: `t3s14-off` dev-01 is €8,764.79, equal to `t1s11-base`.

Bug found on the way: the two look-again moments can fall on the same minute. The world then refuses the schedule ("Fee steps must be in time order") and the week fails. Fixed by merging equal times. The label `t3s14-flat-wide` mixes two versions of the code: ignore it.

**Screens** (10 dev weeks; on-time over all weeks; fee/typical from `tracks/t5/report.py`, for 1-car gigs and for 2- and 3-car gigs):

| label | orders/wk | €/car | total € | on time | ranked | 3 lowest weeks | fee/typ 1 car | 2-car | 3-car | late, 1-car gigs |
|---|---|---|---|---|---|---|---|---|---|---|
| t1s13-wide | 367 | 34.0 | 124,922 | 94.8% | 9/10 | 87.5, 91.6, 94.1 | 1.10 | 0.81 | 0.81 | 7.0% |
| t3s14-flat2-wide (up 0) | 378 | 30.6 | 115,681 | 95.0% | 9/10 | 89.4, 93.9, 94.2 | 1.11 | 0.96 | 0.96 | 5.8% |
| **t3s14-flat2-wide-down (up -0.1)** | 375 | **36.6** | **137,402** | 95.4% | 9/10 | 89.2, 93.9, 94.9 | **1.04** | 0.87 | 0.87 | 5.9% |
| t1s13-flood | 445 | 23.2 | 103,440 | 91.8% | 8/10 | 83.4, 86.6, … | 1.14 | 0.84 | 0.82 | 10.7% |
| t3s14-flat2-flood (up 0) | 453 | 21.4 | 97,094 | 92.7% | 8/10 | 83.7, 89.1, 92.3 | 1.15 | 0.96 | 0.96 | 8.8% |

What we saw:
- The flat fee books fast: the median time to a booking drops from 86 minutes to 7–12 for 1-car gigs, and late 1-car gigs drop from 7.0% to about 5.9%.
- At `fee_flat_up=0` the opening fee (about 1.0–1.1 times typical) is too high. 1-car gigs cost the same as the ladder, and bundles cost more (0.96 against 0.81). Cars book before a bundle can form: 736 two-car gigs against 978. The result is €9.2k lower on wide and €6.3k lower on flood.
- At `fee_flat_up=-0.1` the 1-car fee drops to 1.04 times typical. Total margin is €12.5k higher than `t1s13-wide`, ahead on 8 of 10 weeks, with on-time up 0.6 points and orders up 2%. dev-07 stays unranked in both (87.5% against 89.2%).
- The orchestrator's hypothesis (booking before the deadline warning decides being on time) fits: faster bookings cut late singles. I have not yet checked its numbers against our data.
- Neither flat version fixes flood's on-time. The flood cars' trouble is the drivers they can get, not the timing of fee raises.

Next: sweep `fee_flat_up` at -0.15 and -0.2, and try a lower bundle fee when cars are flat, on wide; then flood with -0.1; then the mainline's normal volume with -0.1.
