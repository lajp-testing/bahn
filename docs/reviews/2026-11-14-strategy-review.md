# Strategy review — 14 November 2026

The leaders' 430–470 orders at €39–45 do not establish how they dispatch. The most plausible explanation is that they turn more of each working driver-day into productive work **and** buy more appropriately priced demand; either alone may be insufficient. At 450 orders and €42, margin is €18,900, roughly €6,200 above our dev average. These are hypotheses, not additive forecasts. The 90% delivery floor makes a high-volume unranked week worth nothing.

Evidence: the saved `t1s11-base` index has all ten dev weeks: mean 287.9 orders, €12,692 margin per week, 96.77% weighted on time, worst 93.69%. Its 20 rob weeks average 277.1 orders, €12,235, 97.08% weighted on time, worst 94.77%. `b26-fix-wo` in the capacity study is a related earlier policy, not this exact baseline; its 40-week figures below are described in `tracks/t2/FINDINGS.md`, “Where our delivery capacity goes”. Earlier experiments and scans below have their own labels and cannot be treated as matched to today's baseline. The test-final quote figures and leaders' figures are supplied observations, not independently verified here. Estimates below are rough gross-margin effects per week, not measured gains.

## 1. Sell cars that can share a driver's day

**Mechanism.** A multi-car gig eliminates some travel between jobs, and a return leg can move a driver toward home. The 12-hour limit counts road travel between all stops; windows, opening hours and private slots still have to fit. A trade-in's return pickup immediately after the outbound delivery has special slot protection; splitting it loses that protection (RULES, “Gigs”; HANDBOOK, “Drivers”). The competitor cannot see our other orders (HANDBOOK, “Dealers compare prices”).

**Evidence.** In 40 `b26-fix-wo` weeks, 81% of gigs were single-car; 76% of 179 driver-days had only one gig. Median wheel time was 176 minutes per driver-day. Two-car gigs paid 0.79 and three-car gigs 0.74 times summed typical fees, versus 0.95 for singles. A loose partner screen found a partner for 736/908 quoted requests per week, but ignores real road times and feasibility. This is selection, not proof of savings from bundling a particular pair. Existing bundling and 120-minute patience already capture part of the opportunity; four-car bundles lost €5,653 over 30 weeks, and patience 180 lost €5,226, per orchestrator findings.

**Size.** Guess: 40–100 additional profitable cars, €1,500–4,000/week, plus perhaps €300–800 saved fees; overlap is substantial. The 405-car estimate at four wheel-hours per existing driver-day is arithmetic, not an achievable capacity forecast: availability, deadhead, windows and competing work are omitted.

**Smallest test.** Offline replay the saved quote-time open gigs through the actual join feasibility check, including travel, windows and the 12-hour rule; count feasible partners and how often they remain unbooked until the decision. Then compare the already proposed unbooked-chain rebuild against current main on all ten dev seeds, reporting orders, margin, every week's on-time share, cars per driver-day, split/refusal and late rates. Do not release booked drivers to obtain this first estimate.

## 2. Price to fill feasible capacity, not to maximise each quote in isolation

**Mechanism.** Dealer choice depends on price relative to the competitor and each option's value; a quote's value also depends on capacity consumed and future trust (HANDBOOK, “Dealers compare prices”; RULES, “Dealer trust”). The competitor cuts prices for dealers where we win most, so the extra volume can self-erode. A price that maximises immediate expected margin can leave capacity unused, while indiscriminate discounting can overload it.

**Evidence.** Today's shortened test final reportedly had median quote 1.41 times list, 16% wins, median winning quote 1.16; selection means that last figure is not the price needed to win all losses. Offline first-option scans found 331–489 wins at 1.4 and 498–643 at 1.3, assuming no changed competitor or trust, no real dispatch or delivery constraint. Against that optimistic proxy, `limit=35 + patience=120 + car=1.0` had a worst week of 87.4% across 30 matched weeks, hence failed ranking; it does not prove the current price is optimal. The 40-week adoption of limit 35 plus patience 120 added €27,072 and 876 orders relative to the older baseline, with worst 93.7% (orchestrator findings).

**Size.** Guess: 50–150 incremental orders and €1,000–5,000/week if capacity and mix permit; possibly negative or unranked. To bridge €6,200 using 150 extra cars requires about €41 incremental margin each, before any price reduction on existing wins.

**Smallest test.** Use the planned ceiling probe and win-chance quoter, separately against the current baseline on identical dev seeds. Record realised incremental margin and on-time share per week, option and lane, plus open workload and booking delay. Reject any claim based only on static scans or average on-time; test interaction with a capacity improvement before attributing failure to price alone.

## 3. Make slack a tradable resource, rather than treating option kinds alike

**Mechanism.** Same-day is only offered on qualifying early requests; next-day Friday means Monday; within-three-days extends to the third business day, subject to the last Monday. Private delivery and trade-ins have one option (RULES, “Price requests”). Longer deadlines can make chaining and off-peak pickup possible, but competing options cannibalise each other and dealers value speed differently (HANDBOOK, “Dealers compare prices”). The current intake requires 12 hours slack, with a separate same-day gate of six hours and 80 nearby drivers (`dispatch/policies/main.py`).

**Evidence.** In `t2s4-base`, next-day options were chosen 1,840/6,608 times versus 56/1,676 within-three-days; those are offered-option counts, not independent choice experiments. In a scan, same-day switching ratios averaged 0.189 higher than next-day in 725 paired requests, but quoting each alone changes the choice set. Discounting within-three-days by 0.2 or 0.4 lost €1,559 or €1,451 over ten dev weeks, likely including cannibalisation. A 12-hour slack screen reportedly leaves 86.6% of requests with a later option; availability does not imply affordable demand.

**Size.** Guess: 10–40 extra cars or €0–1,500/week from better option mix; could lose money by replacing profitable next-day sales.

**Smallest test.** Offline classify current losses and accepted orders by option, ready day, feasible pickup hours and deadline, including Friday-to-Monday and Saturday site hours. Then test a targeted later-option discount only when a feasible chain exists, against the same seeds; track which alternative the dealer would otherwise buy, on-time and margin, not just later-option wins.

## 4. Reach drivers away from home at a price they will actually take

**Mechanism.** New-gig notifications go only within 30 km of a driver's home, not their current location; raises do not notify, and notifications/offers are unread 23:00–07:00. A direct offer lasts ten minutes, has per-driver and per-gig limits, and a driver may accept less than in the app because there is no expected raise (HANDBOOK, “Drivers”; RULES, “Direct offers”).

**Evidence.** In the 40-week capacity study, 46 second gigs per week had median 110 km from the previous delivery to pickup; only 25% were within 30 km. Approximately 145 loose ride-home candidates per week were lost. The one-week `t2s12-home-smoke` won 68 rides but only 3 offers were accepted, 31 declined and 34 expired, at median 0.75 typical; margin was €457 lower and on-time 92.1% versus 93.7%. Earlier offers studies also lost €2,016/€1,236 over 30 weeks. These do not establish that offers at realistic fees work.

**Size.** Guess: 5–30 additional cars or €0–1,000/week; zero is plausible given read rates and driver opportunity cost.

**Smallest test.** On matched dev weeks, send one daylight offer only to a driver known to finish near pickup and travel homeward, at the current app fee or 0.85–0.9 typical, with no assumed cost discount in the quote. Measure reads, acceptances, eventual driver and fee, cancellations, margin and on-time; compare with identical pricing without offers. Respect offer limits and do not infer acceptance from an API-accepted offer.

## 5. Invest early in reliable dealer trust, while modelling the competitor's response

**Mechanism.** Each on-time order raises the price accepted by that dealer 1%, up to 25%; one late order halves its count, and satisfaction also moves. Each morning the competitor adjusts prices per dealer based on recent wins (RULES, “Dealer trust”; HANDBOOK, “Dealers compare prices”). An early reliable order can improve later prices, but aggressive wins can trigger a counter-cut, and trust improves acceptance rather than guaranteeing a higher realised price.

**Evidence.** D01 accounted for 2,319 of 7,909 really quoted requests across ten `t2s5-base` weeks; in earlier saved board weeks it reached trust 25 Wednesday or later. `invest` weights 0.5, 1 and 2 each lost €2,000–9,000 over ten dev weeks in older configurations; learned per-dealer offsets also lost €1,509–3,085. Trust greater than the actual 1% rule lost €1,315–2,416. These failures strongly challenge a blanket trust subsidy, not a capacity-aware early reliable-order strategy.

**Size.** Illustrative upper bound: one extra early trust count on 50 later €100 quotes is €50 of extra acceptance headroom, not €50 realised profit; halving a count of 20 removes ten such increments. Guess €0–1,000/week net, potentially negative.

**Smallest test.** Offline reconstruct dealer counts and late timing in `t1s11-base`, including how many future requests each increment actually precedes. If material, test a small Monday-only subsidy solely for low-risk, feasible-chain orders of high-volume dealers, with competitor response enabled; compare ten dev weeks with and without it and report trust trajectories, competitor-sensitive win rates, margin and worst on-time.

## 6. Stop teaching drivers that waiting always pays

**Mechanism.** Drivers who viewed and could do a booked order learn the booked fee relative to the first fee viewed and the waiting time; old observations fade. Reposting preserves order age, and raises do not notify. A low opening ladder can therefore create its own waiting and deadline risk (HANDBOOK, “Drivers learn your fees”; RULES, “Drivers”).

**Evidence.** In 40 saved weeks, 1,221 drops occurred, 1,068 rebooked, and the fee rose from 0.96 to 1.29 typical; 45% rebooked at the top step. The `b27-drops` restart saved only around 0.04 typical on rebookings, gained €2,441 over 30 weeks but lowered the worst on-time from 93.7% to 92.3%; it was not adopted. Correlation between waiting and high fees does not identify learned expectations: hard gigs wait and cost more anyway.

**Size.** Guess: €0–1,000/week or a few recovered on-time orders; raising all opening fees may instead erase margin.

**Smallest test.** Compare a modestly higher opening fee with fewer raises, holding urgent rescue intact, on the ten dev seeds. Stratify first-view-to-booking time, fee, drops and late orders by early versus late week and driver exposure; assess total margin and worst on-time, not just cheaper bookings. This is a whole-week test because beliefs persist.

## 7. Treat shocks and private slots as different capacity risks

**Mechanism.** Level 8 includes an unannounced price war, an outage, flu and a bulk order; flu removes 30% of drivers who intended to work that day, and the bulk is 30–40 cars at one yard. The outage covers a town and 80 km for a working day; the war cuts competitor prices 20% for a different day (RULES, “Practice and the final”; HANDBOOK, “The shortage”). Private pickup slots do not extend, unlike dealer windows; trade-in paired returns have special protection (RULES, “Gigs”).

**Evidence.** Four no-win scans found war-day switching means 0.76–0.83 of other days; outage pickup-region premiums were 26–43% in three observable scans. Region learning and an outage detector lost in prior matched tests; the latter lost €2,732 over 30 weeks. Excluding private addresses lost €13,522 over 40 weeks on the older limit-25 baseline, though it improved the worst week from 92.8% to 94.0%. So blanket avoidance sacrifices valuable business, and the detector has not earned adoption.

**Size.** Guess: €0–2,000 in a shock week and improved ranking odds, with little average gain if detection is slow or false. A bulk order could consume much of the 35-place open-work limit; 30–40 requests are not necessarily 30–40 won orders.

**Smallest test.** Offline annotate `t1s11-base` quotes, wins, open workload and late orders around observed bursts and private slots; do not claim to observe an unannounced event without a valid signal. If a measurable bottleneck appears, compare a simple burst-specific admission reserve or private-slot feasibility gate on the ten dev seeds. Report per-week margin and on-time, false alarms, and lost profitable private orders.
