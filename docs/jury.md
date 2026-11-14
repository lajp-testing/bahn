# Bahn: earn the right to take the next car

This is the jury account of the system as it is now: the defaults of `dispatch/policies/main.py` at `fe7164a` and later. Every number cites a run label and its comparison; the linked findings files explain the scope. Money is game euros; the dispatcher itself works in whole cents and whole world minutes from Monday 00:00.

## 1. The problem

We dispatch car transport for a simulated week. A dealer sends a request, we quote delivery options, a win becomes an order, and we post a gig with a fee to attract a freelance driver. Margin is what remains after fees, refunds and penalties. Level 8 gives roughly a third of normal driver supply, unevenly spread between towns; drivers learn whether waiting brings a higher fee, and the competitor changes its prices in response to our wins. Outages, a price war, driver illness and bulk requests disturb the week. Winning work is easier than delivering it: below 90% of orders on time we are not ranked, and only the top 10 ranked teams by margin reach the jury. Our central decision is how much profitable work we can still promise. [Sources: kit **RULES**, **HANDBOOK**.]

## 2. The parts

The mainline, in one breath: a learned cost model (model 4, retrained on recent weeks) prices each car's expected fee and late risk; the quoter counts that cost at 1.1 (0.85 for lanes under 100 km) and quotes same-day whenever 8 hours of slack remain; the intake holds at most 35 orders without a booked driver (45 before noon), with a safe-car allowance up to 80; driver fees are flat, opened near the model's estimate and floored at 0.75 / 0.95 of the typical fee; up to 3 cars travel in one gig. Every part below has one reason and one measured effect.

**The desk keeps the books so every decision uses the same account of the week.** It remembers requests, orders, gigs, bookings and deliveries, answers changes and failed visits, and sends the actions. Practice and the live runner use this same desk, so what we measure is what we play. [Code: `dispatch/desk.py`.]

**The quoter learns what dealers will pay, over what their cars will cost.** For each option it searches for the price with the greatest expected margin: chance of winning times price, less expected driver fees and late losses and a charge for a filling queue. Wins raise the learned price level, losses lower it. Dealer trust is earned, not bought: timely deliveries raise that dealer's accepted price level, a late refund reduces its trust count, and no quote is discounted today to speculate on tomorrow's trust. The cost side is a learned model: gradient-boosted trees on 44 inputs known at quote time (the lane, the time, the cars, the note, our own books), trained on 1.24 million won orders from every saved level 8 week, with weeks played by recent policies counted three times, and exported to plain Python that answers in 0.056 ms. [Code: `dispatch/pricing.py`, `dispatch/features.py`, `dispatch/learned2.py`, `tracks/ml/FINDINGS.md`.]
*Measured:* the learned model (model 3) over the hand-fit model 2 on 40 paired weeks: **+€32,271**, better in 29 of 40, 390 orders a week instead of 364, and the worst weeks *rose* (rob-17 90.2% → 95.4%, dev-07 92.7% → 96.8%) [`b37-fee3` vs `t3s15-safe-flat15`]. The retrain on recent weeks (model 4) added **+€18,349** with the cost tilt `car=1.1` over 40 weeks [`b52-fee4-car110` vs `b46-car105-sameday480`]; offline, on recent-policy holdout weeks its fee error is 0.165 against 0.183 and its late log loss 0.125 against 0.134 [track ml findings]. Quoting same-day whenever 8 hours of slack remain (instead of also requiring 80 drivers near the pickup, which had dropped our same-day quote on 4,117 dev requests) added **+€31,975** over 40 weeks with the tilt `car=1.05` keeping the marginal cars out [`b46-car105-sameday480` vs `b37-fee3`]; alone the same-day rule lost a week (rob-18 89.2%, unranked), so the two belong together. Track 2's finding behind it: a request quoted both same_day and next_day is won 67% of the time, against 34% for next_day alone.

**The intake protects delivery capacity before we promise it away.** It counts orders without a booked driver and quotes awaiting a dealer decision, with a limit of 35 (45 before noon). Past the limit, up to 80, it still quotes the *safe* cars: no private address and a lane under 300 km, the cars a flood test showed stay on time. Options need 12 hours of slack after the first car's drive, using note-adjusted times; private addresses are allowed. These are admission rules, not forecasts of driver shifts. [Code: `dispatch/intake.py`, `dispatch/policies/main.py`.]
*Measured:* limit 35 plus bundle patience 120 over limit 25: **+€27,072** over 40 paired weeks (holdout +€5,126), orders 10,214 → 11,090, and the lowest on-time weeks rose from 92.8/92.9/93.5% to 93.7/93.8/94.0% [`b24-limit35-patience120` vs `b22-baseline`]. The safe-car allowance plus flat fees (the volume step): **+€69,993 (+14.3%)** over 40 weeks, better in 38 of 40, 364 orders a week instead of 277 [`t3s15-safe-flat15` vs `t1s11-base` / `t3s10-calm`]. The earlier slack and same-day rules: €73,495 → €83,223 over the 10 dev weeks, on time 98.1% → 97.6% [`t1s4-base` → `t1s4-same360-80`, track 1].

**The fees open at what the car is expected to cost, not at a ritual ladder.** A gig opens at the model's expected fee minus 15%, floored at 0.75 of the typical fee (0.95 for a lane under 40 km or a car with under 5 hours to its last pickup), and holds it: one step of 0.15 after 6 hours of the drivers' day without a booking, one more 24 hours before the last pickup. Steps skip the night (21:00–07:00): a sleeping driver cannot answer a raise. Deadline warnings still use the urgent ladder. [Code: `dispatch/fees.py`, `dispatch/policies/main.py`.]
*Measured:* the evening fix that came out of the test final — floors 0.75 / 0.95 with short lanes priced at their own cost tilt — earned **+€31,187** over 40 paired weeks (holdout +€10,243, better in 9 of 10), better in 34 of 40 weeks, 386 orders a week at €43.70 a car [`b68-floor075-short095-carshort085` vs `b52-fee4-car110`]. History of the fee part: the measured ladder with hourly raises made €67,234 against €64,350 for the starter's behaviour over 10 dev weeks [`t3-stint4-rise60` vs `t3-stint4-baseline`, track 3], and the hand-fit fee model 2 added +€280 while raising the worst week from 93.4% to 95.9% [`t3s5-model2`, track 3].

**Bundles let a scarce driver move more cars with less travel between jobs.** Up to three single-car orders (no private addresses, no urgent cars) share one gig when the route fits windows and opening hours, at 0.85 of the sum of the cars' fees. A bundle still without a driver splits after 120 minutes of the drivers' day, or 240 minutes before its last feasible start: patience gives bundling a chance without trapping cars together. [Code: `dispatch/bundles.py`, `dispatch/policies/main.py`.]
*Measured:* in 11 complete paired probes the same cars booked for €916 together against €1,068 alone, 14% less [`t5-pair-1-pairs.jsonl`, track 5]; the adopted patience is part of the limit combination above, which won 876 more orders over the same 40 weeks [`b24-limit35-patience120`]. Larger bundles lost: 4 cars −€5,653, 5 cars −€1,915 over 30 weeks [orchestrator findings].

**The note reader turns a dealer's words into constraints before a failed visit teaches us the same lesson.** It reads Finnish, Swedish and English clauses for ready times, release after payment, pickup and delivery hours, deadlines, manual licences and plates, and handles corrections and denied times. The planner uses these facts for stops and the intake uses them for slack. It is a local rule-based reader; no remote language-model call sits in the decision loop. [Code: `dispatch/reader.py`, `dispatch/notes.py`.] Its full-week effect was never isolated; it stays because the facts it reads are constraints the world enforces, and the intake's slack rules depend on them.

**The repairs keep cars moving and stop paying urgent fees when timeliness is already lost.** `windows` treats a window ending now as ended, preventing a refused repost; `orphans` posts an undelivered car again when it has neither a gig nor a pending post; `calm` puts an urgent car past its last pickup minute on the normal fee schedule instead of the urgent ladder. [Code: `Desk.cut`, `Desk.tick`, `Desk.fees_for`.]
*Measured:* `calm` over 40 paired weeks: **+€6,163** (dev+rob +€5,347, holdout +€816), higher in 25 of 40 [`t3s10-calm` vs `b26-fix-wo`, track 3 and orchestrator findings]. The honest tradeoff: the lowest weeks fell from 93.7/93.8/94.0% to 91.6/92.3/93.7%, and we accepted that deliberately for the margin — the change only touches cars that are already late. `windows` and `orphans` remove real failure modes; their switch is inert when off (`t3s10-check` dev-01 = `b26-fix-wo` dev-01 to the cent, €8,742.09).

## 3. How we decided

The world is deterministic, so every idea became a **switch, off by default**, and the mainline with the switch off must reproduce the previous adopted label **to the cent** before the paired comparison counts (`b72-main-check` dev-01 €12,348.31 reproduces `b68`; `b62-main-check` €11,284.69 reproduces `b52`; `b49-main-check` €11,361.54 reproduces `b46`).

Every comparison is **paired weeks on the same seeds**: 10 dev weeks, 20 rob weeks and 10 holdout weeks — 40 worlds per decision — and for the last step 10 more seeds (rob-21..30) never played before. We report margin and on-time share together, and we never add gains across the table: each row is one comparison on its own week set, and a changed booking changes the rest of the week.

The **worst-week rule** decides ties: a change that drops any week out of the ranking, or lowers the lowest weeks, is not adopted, however much margin it adds. Two examples: earlier urgent fees gained +€3,166 over 30 weeks but put the worst week at 91.67% — rejected; same-day quoting alone gained +€25,732 but lost rob-18 at 89.2%, unranked — adopted only together with the cost tilt that keeps the marginal cars out.

## 4. The evening's story

The organiser's test final on Saturday 14 November, 18:00 UTC, played by our live runner with the then mainline: **5th of 75 ranked teams, €17,442.75, 356 orders, 97.2% on time, nothing undelivered** [test final record]. We recorded the public leaderboard feed from Tuesday 13:51 to the end and analysed it against our own events, journal and the reveal [analysis: `tracks/orch/finals/testfinal-20261114-1800/`].

The analysis said the gap to the top was **volume, not price**: the books of Juhus (469 orders against our 356) matched ours plus about 110 cars under 100 km, each worth about €48 of revenue and €19 of margin, while our prices in the middle of the market were already near the fitted optimum. Why we lost them: 73% of our single-car gigs opened exactly at the 0.85 fee floor (every lane under 40 km at the 1.15 floor, booked in one minute at the first view), so short cars were dear to move and dear to quote. The intake queue explained little; it never filled on the days we lost most.

The fix went in the same evening: lower fee floors (0.75, and 0.95 for the shortest lanes) and a cost tilt of 0.85 for lanes under 100 km, so the model that had learnt costs under the old floors prices short cars at what they cost now. On 40 paired weeks: **+€31,187, holdout +€10,243, better in 34 of 40**, 386 orders a week at €43.70 a car [`b68-floor075-short095-carshort085` vs `b52-fee4-car110`]. Adopted at `fe7164a`; the mainline reproduces the label to the cent.

## 5. What we tried and rejected

Negative results, all paired weeks on the same seeds; the reason is the rule, not the number.

| Idea | Result | Why rejected |
|---|---|---|
| Earlier urgent fees (`fee_early` 300) | +€3,166 over 30 weeks | Worst week 91.67%; breaks the worst-week rule |
| Same-day quoting without the cost tilt | +€25,732 over 30 weeks | rob-18 89.2%, unranked |
| Holding fees back (`hold720` / `back300`) | −€65,251 / −€134,674 over 30 weeks | Unbooked gigs filled the intake queue; fewer orders |
| Direct offers to drivers | −€2,016; −€1,236 without the premium; 91 of 3,783 offers accepted | Drivers decline; the app books the gig anyway |
| Trust investment (discounting today's quote) | `invest` 0.25: −€1,164; 0.1: +€135 over 10 dev weeks | Gives away more price than the trust effect pays back |
| More intake (limits 38, 40, 45/55 with safe 100; per-due-day; limit 45 with patience) | −€878, −€2,213, +€2,602, −€693 (one week); limit 45 with patience +€22,271 but worst weeks 92.3% | Not enough delivery capacity behind it; the worst-week rule |
| Longer bundle patience (180) | −€5,226 over 30 weeks | Cars wait together too long |
| Bundles of 4 or 5 cars | −€5,653 / −€1,915 over 30 weeks | Routes stop fitting; fee saving does not return |
| Outage detector | −€2,732 over 30 weeks, worst 92.12% | The regional signal is too rare to learn in time |
| No private addresses | −€13,522 over 40 weeks | Private orders are profitable |
| View-count fee raise | +€2,760 over 30 weeks; on lanes ≥300 km −€2,727 | Worst week 91.4% / loses margin |
| Ladder schedule for the learned model | +€9,876 over 30 weeks | Worst week 91.0% |
| Cheaper cars everywhere (`car` 0.9 / 0.85 / 1.0) | Bought orders at ≈€75 of margin each; `car` 1.0 +€5,168, worst 92.6% | Volume without margin; Test-Team1114's price-only route ends 33rd |
| Chain offers at post time; quoter step/boost; kind offsets; yard pricing | −€1,466 (21 of 3,253 offers taken); −€3,835 / −€1,335; −€3,258 / −€1,459; −€379 | Each loses margin on its own paired weeks |

[Sources: orchestrator findings, tracks 1–5 findings.]

## 6. Robustness

The live runner preserves decisions, not just events: it journals every action with the world's answer and, on rejoin after a crash or a network failure, replays events and recorded results in minute order and rebuilds orders and gigs from the snapshot. A rehearsal with two interruptions advancing at final speed ended at €11,287.63 and 95.19% on time against a same-seed reference of €11,801.96 and 96.5% [`t3-live-2` / `t3-live-ref2`, live rehearsal record]; the slowest desk decision batch measured was 121 ms and the slowest action round trip 564 ms [`t3-live-5`]. An operational wrapper restarts the process after a crash; the test final above was played end to end by this runner.

Practice runs go through a machine near the server with shared slot locks, so every number in this account is reproducible from saved weeks.

## 7. What we still watch

The worst world in our sets (rob-18) ends at 91.3% on time under the final settings; the mean is 96.3% with a spread of ±1.5 points, and we judged the final's risk on the spread rather than the one hardest world. The action journal is not exactly-once: a crash between the server's acceptance and the local write leaves a reconciliation gap for restart replay. An on-time governor (a week whose on-time share slips quotes dearer and without same-day speed) is implemented and measured as insurance; it is off by default like every other switch.
