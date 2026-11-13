# Track 3: fees and drivers

## For other tracks

In saved overloaded base dev runs, first posts with less than 3 hours to last pickup booked 5.2% and 3.9% of orders arrived on time (153 posts). Private-address orders arrived on time 39.6% versus 46.6% for others; trade-ins 21.6% versus 46.2% for single cars. These are associations under the overloaded starter, not predictions under a controlled intake. Treat tight slack and trade-ins as strong candidates for declining, not calibrated probabilities.

## Saved weeks: first posts

`python3 tracks/t3/analyse.py` reads all saved `base` dev runs (8,136 first posts; runs, rather than deduplicated seeds, are the unit). 58.9% of first posts received at least one booking; median booking was at 1.0 times the typical fee, 18 minutes after posting. This excludes bookings of later reposts and does not guarantee the driver completed the gig. 45.7% of these orders arrived on time. Cancelled orders and changes of plan are not separated; final last-pickup time can differ from its original value.

| Group | First-post booking | On-time order | Median minutes to first booking |
|---|---:|---:|---:|
| No driver living in pickup town (462) | 53.9% | 41.6% | 28 |
| 10+ living in pickup town (5,426) | 59.3% | 46.2% | 14.5 |
| Private address (1,076) | 47.8% | 39.6% | 48 |
| Trade-in (153) | 43.1% | 21.6% | 150 |
| Last pickup 3–12h away (2,029) | 25.8% | 24.3% | 16 |
| Last pickup 12h+ away (5,954) | 71.6% | 54.0% | 18 |
| Monday (2,064) | 85.0% | 71.3% | 6 |
| Friday (1,199) | 30.4% | 29.6% | 940.5 |

Friday median booking fee was 1.5 times typical, trade-ins 1.15, and the other groups above 1.0. Day, slack and load are confounded; exact-town counts omit neighbouring towns. Road length and 30 km catchments remain to be measured. This is not an estimate of a causal fee effect.

## Experiments

Running matched dev weeks with markup 1.5, starter schedule versus flat 1.5. Neither has yet established an improvement.

## What failed / limitations

No causal schedule comparison yet. The starter's overloaded weeks do not identify the cost of timely transport; successful bookings are a selected subset, and later reposts are excluded from the first-post fee statistic.
