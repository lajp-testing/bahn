# Track 5: more cars per driver

**Verdict: not established.** The direct-offer pilot covered one gig: 8 offers sent, 4 read, 0 accepted; this cannot establish whether offers beat the app. At 1.0 times typical fee, none of 315 offers across 30 gigs in two seeds was accepted. On 30 fresh gigs, viewer offers at 0.5, 0.7 and 0.9 times typical also found no driver (67 offers per fee, 26 gigs with viewers); the parent app later booked 27 of those 30 gigs. No accepted offer exists to measure a fee saving. Do not adopt a policy on this evidence.

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
