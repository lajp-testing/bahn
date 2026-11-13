# Track 3: fees and drivers

## For other tracks

The complete `t1-limit15-later-price16-fee13` control (opening 1.3, 0.1 steps hourly) made €12,113.94 over 10 dev weeks, 96.2% on time, worst 93.2%, ranked 10/10. The 1.5 control made −€31,979, 96.0%, worst 93.4%, ranked 10/10; 1.1 made €37,221, 95.3%, worst 89.8%, ranked 9/10. The 1.3 control meets the 92% per-week threshold; 1.1 does not. The 1.71 cost estimate remains an unvalidated overloaded-week benchmark.

## Findings table

| Measurement | Sample | Result | Limit |
|---|---:|---|---|
| Fork fee grid | 10 single-car orders, one study seed | Repeated 1.5 agreed; kept-booking outcomes monotone at 0.5 increments, at both horizons | Not proof of monotonicity between grid points or on other orders; future parent decisions are not replayed in copies. |
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

No causal schedule comparison yet. The starter's overloaded weeks do not identify the cost of timely transport; successful bookings are a selected subset, and later reposts are excluded from the first-post fee statistic.

## Provisional cost estimate

Across 8,819 orders with attributed driver-fee ledger entries, total attributed fees average 1.71 times the typical fee (median 1.5), including reposts. `Fees.estimate` exposes that unadjusted benchmark for the whole request; it is not an on-time cost or calibrated chance, and excludes orders with no attributed driver fee and other costs. It should not be used as a validated profitability model.
