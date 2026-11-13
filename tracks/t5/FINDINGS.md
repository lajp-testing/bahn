# Track 5: more cars per driver

**Verdict: not established.** The saved-week screen finds 17 consecutive same-town gig pairs across 10 mainline dev weeks (1.7 per week), but does not measure how many orders a combined gig or direct offer could add, nor its fee saving. No policy should be adopted on this evidence. The required driving-time feasibility analysis and copy experiments remain to be done.

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
