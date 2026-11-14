# Track 5: more cars per driver

**Verdict (14 Nov): one gig with two cars costs less than two gigs, and finds drivers for cars that nobody takes alone. The desk now bundles (`dispatch/bundles.py`, `--set bundle=2`).** Direct offers stay unproven (below).

## Two cars in one gig: the measurement

`tracks/t5/pairs.py --seed t5-pair-1` plays a week with the mainline. When a car is won that fits before or after an open car (the second pickup at most 30 minutes from the first delivery, both inside their windows), copies of the world find the lowest flat fee that books within 3 hours: each car alone, and both in one gig. 14 pairs, `t5-pair-1-pairs.jsonl`.

| | pairs | fee alone, both cars | fee as one gig | |
|---|---|---|---|---|
| all three found a driver | 11 | €1,068 | €916 | -14% |
| one car found no driver alone, at up to 2.3 times typical | 2 | - | 0.74 and 0.86 times typical | the gig booked |
| the gig found no driver (experienced drivers only) | 1 | 1.36 and 0.86 times typical | - | |

9 of the 11 complete pairs were cheaper as one gig (from -6% to -52%), 2 were dearer (+17%, +72%: one car alone happened to suit a driver going home). The saving is largest for two short city legs (-27%, -42%) and where one car is hard alone (-34%). A flat fee over 3 hours is a noisy measure of what a driver needs, so read the -14% as "between a tenth and a fifth".

`tracks/t5/potential.py b10-quiet21` counts, in the saved mainline weeks, the won cars that fit with another won car by the same test: 1,846 of 2,670 (an upper bound: it ignores that a car may have its driver before the partner is won).

## Bundles in the desk

A newly won car joins an open gig when one driver can do all stops in a row. The bundle's fee is the sum of what its cars' own schedules pay at each minute, times 0.85. A bundle without a driver goes back to one gig per car, each at the fee its own schedule shows then. First result, 7 dev weeks, `b13-bundle2` against `t3s5-model2`: €74,982 against €70,496 (+6.4%), 6 of 7 weeks higher, 97.4% against 97.6% on time; 430 bundles posted, 394 booked, median 80 minutes to the booking, booked at 0.87 to 0.91 times the typical fees. Later numbers are in the orchestrator's batch table.

## Direct offers

**Not established.** The direct-offer pilot covered one gig: 8 offers sent, 4 read, 0 accepted; this cannot establish whether offers beat the app. At 1.0 times typical fee, none of 315 offers across 30 gigs in two seeds was accepted. On 30 fresh gigs, viewer offers at 0.5, 0.7 and 0.9 times typical also found no driver (67 offers per fee, 26 gigs with viewers); the parent app later booked 27 of those 30 gigs. No accepted offer exists to measure a fee saving. Do not adopt a policy on this evidence.

**Earlier stint:** The saved-week screen finds 17 consecutive same-town gig pairs across 10 mainline dev weeks (1.7 per week), but does not measure how many orders a combined gig or direct offer could add, nor its fee saving. No policy should be adopted on this evidence. The required driving-time feasibility analysis and copy experiments remain to be done.

## Saved weeks: preliminary screen

`python3 tracks/t5/opportunity.py` reads the 10 saved `main-c-measured-m16-nopriv` dev weeks; per-week results are in `opportunity.jsonl`. The mainline made €46,702.99 total margin across 10 weeks, with on-time share between 95.21% and 100% (10 weeks). There were 1,590 non-cancelled orders in these snapshots.

A deliberately loose upper bound checks single-leg requests and orders for a directed match between the first delivery town and the second pickup town and compatible stated windows, assuming zero driving time. It finds at least one such partner for 10,126 of 10,353 requests and 1,561 of 1,590 won orders across 10 weeks; 11,034 directed won-order pairs pass. Pairs overlap, may have been known at different times, and are **not** the requested 12-hour feasible ceiling: driving times, opening hours, actual notes and availability are ignored. These numbers cannot be used to forecast gains. Multi-leg requests were excluded from pairing but included in the denominators.

Among completed single-order gigs, grouped by driver and gig-start day, 212 were subsequent gigs after 1,381 first gigs (10 weeks). Seventeen adjacent pairs had the first order's delivery town equal to the next pickup town; this is a same-town proxy, not proof that the driver travelled directly between stops. Subsequent gigs averaged €110.11 (212 gigs), versus €110.93 for the first gig of a driver-day (1,381 gigs). These are raw fee averages, not comparable jobs or causal savings. Driver days are defined by start day, so overnight sequences are omitted. Rounding per-week means before aggregation changes the aggregate by at most one cent.

## Not yet measured

- The requested feasible pairs by town pair and day require road minutes, site hours, deadlines, and actual ready times; the screen above is only an upper bound.
- No copies were run: the two-single versus two-car booking fee and booking speed comparison (target about 10 pairs) and direct offer acceptance versus app fee (target about 20 offers) remain outstanding. No `orch` slot was used.
- A combined gig would require the desk to defer posting, select compatible won orders, construct ordered stops, and handle cancellation, changes and reposting of remaining legs. Direct offers would require the desk to track finishing drivers, select eligible open gigs, send offers, and enforce daily limits. Neither change was implemented.

## Next

Calculate realistic candidate pairs using the world map and site hours, stratify by town and day, then use `tracks/t3/scan.py`'s slot-managed fork method on representative pairs and offers. Only test a policy across all 10 dev seeds if those controlled measurements show a clear gain; require higher total margin and at least 93% on time in every week.

## Direct offers: pilot

`t5-pilot-1-rules` sampled one open gig at 30 minutes, with offers at 1.0 times typical fee. Pickup-home: 3 sent, 2 read, 0 accepted (1 gig); delivery-home: 3 sent, 0 read, 0 accepted (1 gig); working near pickup: 0 sent (1 gig); viewers: 2 sent, 2 read, 0 accepted (1 gig). Expired offers may have been unread or no longer fit. The pilot is not an effectiveness estimate.

## Direct offers: rule screen

`t5-rules-1` and `t5-rules-2`: 30 gigs, 15 per seed, still open 30 minutes after posting, weekdays 07:00–22:45. Each rule ran in its own copy for 15 minutes. Pickup-home: 90 sent, 17 read, 0 accepted (30 gigs); delivery-home: 90 sent, 9 read, 0 accepted (30 gigs); working near pickup: 59 sent, 28 read, 0 accepted (27 gigs with candidates); viewers: 76 sent, 32 read, 0 accepted (28 gigs with candidates). An expiry can mean unread or that the gig no longer fits, so read counts are minimums. All four rules tied on acceptance; viewers were chosen provisionally for a fresh lower-fee screen because they had the most definite reads, not because acceptance was demonstrated. Planned working-driver destinations were included without predicted delivery time, a loose proxy for about-to-finish.

## Direct offers: fee screen and parent comparison

`t5-fees-1` and `t5-fees-2` sampled 30 fresh gigs, 15 per seed. Viewers were available for 26 gigs. At each of 0.5, 0.7 and 0.9 times typical fee, 67 offers were sent, 32 were definitely read and 0 accepted (26 gigs); four gigs had no viewers to offer to. The unchanged parent app booked 27 of the 30 sampled gigs later in the week; among those 27 first bookings, median delay from sampling was 52 minutes and median booked fee was 10,762 cents. Six of the 30 gigs booked within 15 minutes. No offer accepted, so there is no lowest accepted fee or paired fee saving to report. These are short 15-minute copy outcomes against subsequent parent app outcomes, not a randomized policy comparison; expirations conflate unread and no longer fitting, and simultaneous app bookings can preempt offers.

No `t5` policy or dev-week comparison was built: the controlled screen found no driver via offers. Next, inspect whether the high expiration rate reflects app preemption, driver availability or offer timing, and measure a revised rule in copies before considering a policy.

## Offers at realistic fees, 14 Nov

**Question.** The earlier screens offered at 0.5 to 1.0 times typical, below every fee the same gigs later booked at (median 1.35; review point 6). Do offers at the app's own fee add margin or on-time share where the rules say they should: urgent gigs (deadline warning) and dropped gigs, sent to drivers a notification does not reach?

**The rule** (`dispatch/offers.py`, off by default, `--set offers=urgent+drops`). When an order's deadline warning comes, or a driver drops or no-shows its gig, the gig goes as a direct offer to up to `offer_n=3` drivers, at the fee the app shows now plus `offer_up=0.1` times the gig's typical fee. Drivers, best first: our drivers whose last delivery for us is within `offer_near=30` km of the pickup (in the last `offer_fresh=180` minutes, or still to come); then the gig's viewers, last first. Never the driver who dropped it, an automatic-only licence for a manual car, a driver offered this car before, or one with three offers today. After the answers, one more round with the next drivers (`offer_rounds=2`). No offers from 22:50 to 07:00 (no driver reads them). The desk marks an `accepted` gig booked; the limits are rebuilt from the journal after a restart. Bundles are left alone (the urgent fees split them first).

**Measurement.** Baseline `t2s9-base` (mainline as it is), 10 dev seeds and `rob-01`…`rob-20`, 30 weeks paired.
