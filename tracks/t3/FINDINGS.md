# Track 3: fees and drivers

## For other tracks

`t3-main-low20-v1` (opening density estimate + 0.15, +0.1 every 20 minutes to 1.5, starter urgent) on main: €54,426.26, 96.0% on time, worst 93.1%, 10/10 ranked; mean booked fee 1.128 times typical, 207 drops / 1,772 bookings. Main baseline: −€27,162.41, 97.1%, worst 94.9%, 10/10. Same seeds; notes differ from the older `t3-density-buffer-v1`, so its €37,962.14 is not a controlled comparison. Further schedules and flat control are running.

Third stint mainline baseline `t3-stint3-main`: −€27,162.41, 97.1% on time, worst 94.9%, ranked 10/10 on dev. New fee experiments are in progress; earlier `t3-density-buffer-v1` used starter notes, so it is not a same-parts comparison to main.

The complete `t1-limit15-later-price16-fee13` control (opening 1.3, 0.1 steps hourly) made €12,113.94 over 10 dev weeks, 96.2% on time, worst 93.2%, ranked 10/10. The 1.5 control made −€31,979, 96.0%, worst 93.4%, ranked 10/10; 1.1 made €37,221, 95.3%, worst 89.8%, ranked 9/10. The 1.3 control meets the 92% per-week threshold; 1.1 does not. The experimental `Fees.estimate` is a two-hour booking threshold, not total delivery cost; see its limitations below.

Fork scans on 39 single-car wins in three `t3-study-*` weeks give a two-hour mean least retained-booking fee of 0.64 times typical among 38 with a booking at 3.0; one found none at 3.0. Fewer than 30 drivers within 30 km of pickup: 0.75 (16 measured, one none); 30 or more: 0.57 (22). These are selected orders, not delivery costs or representative estimates: the parent continues alone, copies receive no further desk actions, and a retained booking is only observed through the horizon. Trade-ins were excluded and private addresses numbered three. The selected schedule uses 0.60 + 0.15 for sparse pickups; the later refitted `Fees.estimate` is experimental and not a calibrated full-order cost. The earlier buffer schedule opened 0.45 above that estimate and added two 0.15 raises at 30-minute intervals; the selected newer schedule is described above.

`t3-main-low15-v1` (estimate, +0.1 every 15 minutes to 1.5) made €54,109.09, 96.3% on time, worst 92.5%, ranked 10/10; mean booked fee 1.118 times typical, 0.112 drops per booking. It meets the hard floor but is less robust than low20 on its worst week and makes slightly less margin.

`t3-main-buffer-v1` reproduces the earlier density buffer on main: €42,764.86, 96.6% on time, worst 93.6%, 10/10; mean fee 1.238, drops/booking 0.100. Against it low20 gains €11,661.40 with worst week 93.1%. `t3-main-deadline240-v1` starts at the estimate, rises 0.1 per 15 minutes, compresses that interval to reach 1.5 at least 240 minutes before last pickup, and uses the starter urgent schedule: €50,427.29, 95.7% on time, worst 92.4%, 10/10, mean fee 1.129, drops/booking 0.114. The deadline rule and schedule are tested together; this does not isolate the deadline rule.

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

An exploratory matched-copy study (`offers.py`) posted a flat gig at the refitted estimate and compared the app alone with the same app plus offers to three nearby drivers. The connection ended after two orders, so there is no usable estimate of the offer effect or read rate. On those two orders one offer was declined and five expired; expired conflates unread offers with offers made obsolete by a booking, so it does not identify how often offers were read. One app booking occurred in both copies. Repeat on several seeds with enough observations before deciding whether direct offers save fees.

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
