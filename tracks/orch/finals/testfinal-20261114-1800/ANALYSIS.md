# Test final 18:00: what the top teams did that we did not

World `f53b4661bfe50ae2e4c23`, level 8, 1,030 requests. We: 5th, €17,443, 356 orders, 97.2% on time. Analysis only: no weeks were played. Times are world minutes or weekday hours; "top 4" is the mean of Juhus, MathNet1, Progresful and source-exp.

## The short answer

1. **The gap is about 110 short, cheap cars, not our prices in the middle.** Juhus's books equal ours plus about 110 cars under 100 km: revenue about €45 and cost about €28 each (the typical fee). We win 24% of the requests under 100 km and pay 1.0 to 1.5 times the typical fee for them. Confidence: medium (the feed shows totals, not orders).
2. **Our fee floors make those cars dear.** 73% of our single-car gigs open exactly at the hard 0.85 floor, and half of them book within 7 minutes; every gig under 40 km opens at the 1.15 floor and books in one minute at the first view. Confidence: high for the facts, medium for how low the fee can go.
3. **The queue hypothesis explains little.** The queue was under a third full in the windows where we lost most (Monday, Wednesday). It bites only Thursday 16–20 and Friday 12–18: at most 15 to 25 orders.
4. **Wednesday was the price war**, and Monday has no dealer trust: both days our quotes sat about 0.1 list prices over what dealers accepted.
5. **One late car, three minutes late (€9.77 refund), halved the trust of dealer D01**, which sends 31% of all requests. Its win rate fell from 60% on Thursday to 30% on Friday.

This world was not an easy one: our result is inside our dev range (dev weeks of the same code: €10.2k–€23.4k, 341–433 orders, median booking time 6–14 min; here €17.4k, 356, 12 min). So the other teams' volume is not an effect of the world.

## 1. How the week grew

The feed starts Tuesday 13:51. Orders count when won; the feed window is by decision time.

| Window (by decision time) | Requests decided | We won | Top 4 won | Juhus | MathNet1 | Progresful | source-exp |
|---|---|---|---|---|---|---|---|
| Mon 08:00 – Tue 13:51 | 301 | 97 | 136.2 | 150 | 129 | 118 | 148 |
| Tue 13:51 – Wed 08 | 122 | 50 | 61.5 | 59 | 61 | 60 | 66 |
| Wed 08–12 | 57 | 12 | 15.5 | 15 | 14 | 12 | 21 |
| Wed 12–14 (bulk order) | 66 | 13 | 32.8 | 27 | 34 | 31 | 39 |
| Wed 14–18 | 86 | 15 | 28.0 | 27 | 28 | 23 | 34 |
| Wed 18 – Thu 08 (war over) | 12 | 9 | 10.8 | 11 | 10 | 11 | 11 |
| Thu 08–16 | 126 | 64 | 63.5 | 61 | 75 | 61 | 57 |
| Thu 16 – Fri 08 | 81 | 32 | 39.5 | 41 | 49 | 38 | 30 |
| Fri 08–12 | 50 | 21 | 28.0 | 25 | 29 | 26 | 32 |
| Fri 12 – end | 129 | 43 | 58.2 | 53 | 71 | 62 | 47 |
| **Week** | **1,030** | **356** | **474** | 469 | 500 | 442 | 485 |

Where the 118 missing orders are: **39 before Tuesday 13:51, 12 on Tuesday afternoon, 38 on Wednesday, 7 on Thursday, 22 on Friday.** Monday and Wednesday carry two thirds of the gap. It is steady inside those days, with one burst: Wednesday 12–14, when a dealer group (D05, batch B0138) sent 30 cars from one yard in Vantaa; we won 4 of them.

Our own days: Mon 69 of 219 (32%), Tue 79 of 204 (39%), Wed 50 of 221 (23%), Thu 100 of 207 (48%), Fri 64 of 179 (36%).

## 2. What the feed says about their strategy

**They win cheap cars at a normal margin share.**

| | Orders | Revenue/order | Cost/order | Margin share |
|---|---|---|---|---|
| Juhus | 469 | €102.5 | €60.7 | 40.8% |
| Progresful | 442 | €98.7 | €58.5 | 40.7% |
| source-exp | 485 | €96.1 | €59.8 | 37.8% |
| MathNet1 | 500 | €105.1 | €67.9 | 35.4% |
| us | 356 | €119.7 | €70.7 | 40.9% |

Juhus has 113 more orders than we do, €5,451 more revenue and €2,149 more margin: **€48 revenue and €19 margin for each extra order**. Two fingerprints, from our own request list and a win curve fitted on our quotes:

| Hypothesis | Orders | Revenue/order | Cost/order |
|---|---|---|---|
| Juhus (observed) | 469 | €102.5 | €60.7 |
| Our orders, all quotes 5% lower | 466 | €110.4 | – |
| Our orders, all quotes 10% lower | 567 | €104.5 | – |
| Our orders + 110 of the 197 requests under 100 km that we lost, at 1.4 × list, moved at the typical fee | 466 | €102.3 | €60.7 |

Only the last one fits orders, revenue and cost together. The requests under 100 km: 261 of 1,030, mean list price €32.6, mean typical fee €29.1.

**Other readings of the feed.**
- Delivery speed is the same for everyone: every top team had booked 44–47% of its final revenue by Friday 00:00 and 75–77% by Saturday 00:00 (we: 47%, 75%). No team delivers earlier.
- By Friday 00:00 we had 75% of Juhus's orders but 92% of its revenue and margin (€7,594 against €8,295). The margin gap opened with Friday's and Monday's deliveries (−€701 → −€1,890 → −€2,149).
- No team takes more risk early and less late. On-time shares fall slowly all week; the lowest points are at the end (Juhus 97.7%, MathNet1 95.8%, Progresful 98.9%).
- Volume has a ceiling near 500 orders: the two teams at 500+ (MathNet1, Test-Team1114) have 95.8% and 96.2% on time, 0.4% not delivered, and €67 cost an order. Test-Team1114 (504 orders, €94.6 revenue an order, 29.7% margin share, 33rd) is the price-only route: it does not pay.
- Across the 75 ranked teams, orders and margin correlate at 0.80; in the top 30 at 0.65. Revenue per order does not predict margin (0.22).

## 3. Our side of the same windows

`held` = our orders without a booked driver when a request arrived (limit 35, 45 before noon; safe cars up to 80). `declined` = quoted at 5 × list. `median quote` = lowest quote ÷ list price of real quotes.

| Window (by arrival) | Requests | Won | Win % | Declined (queue) | Quote > 2× | Median quote | same_day offered / quoted | held mean | held+pending max |
|---|---|---|---|---|---|---|---|---|---|
| Mon 08–12 | 68 | 25 | 37 | 4 (0) | 0 | 1.35 | 47 / 22 | 1.5 | 13 |
| Mon 12–20 | 151 | 44 | 29 | 14 (0) | 11 | 1.33 | 94 / 33 | 8.9 | 24 |
| Tue 08–14 | 94 | 36 | 38 | 10 (0) | 6 | 1.44 | 67 / 31 | 6.1 | 16 |
| Tue 14–20 | 110 | 43 | 39 | 10 (0) | 2 | 1.46 | 67 / 33 | 10.9 | 25 |
| Wed 08–12 | 58 | 13 | 22 | 2 (0) | 0 | 1.38 | 50 / 15 | 7.7 | 21 |
| Wed 12–14 | 74 | 15 | 20 | 5 (0) | 2 | 1.36 | 60 / 33 | 10.9 | 25 |
| Wed 14–18 | 82 | 16 | 20 | 3 (0) | 4 | 1.35 | 42 / 20 | 10.8 | 25 |
| Wed 18–20 | 7 | 6 | 86 | 0 (0) | 0 | 1.24 | 6 / 3 | 2.1 | 5 |
| Thu 08–16 | 129 | 67 | 52 | 6 (0) | 14 | 1.75 | 89 / 34 | 13.8 | 28 |
| Thu 16–20 | 78 | 33 | 42 | 10 (8) | 5 | 1.62 | 46 / 29 | 24.5 | 40 |
| Fri 08–12 | 60 | 21 | 35 | 11 (0) | 4 | 1.49 | 54 / 17 | 12.5 | 27 |
| Fri 12–14 | 42 | 18 | 43 | 2 (0) | 0 | 1.50 | 34 / 0 | 20.2 | 36 |
| Fri 14–18 | 77 | 25 | 32 | 13 (11) | 13 | 1.70 | 8 / 0 | 29.4 | 42 |

Wins here count the 362 `order_won` events (6 orders were cancelled later); the table in section 1 counts the feed's 356.

**The queue.** On Monday and Wednesday the queue held 2 to 12 orders: the queue charge was under 0.03 list prices and no request was declined for it. It reached the limit only Thursday 16–20 and Friday 14–18: 19 queue declines in the week, and a charge of 0.1–0.2 list prices on the cars that are not safe. Of the 90 declines, 53 had no option with enough slack, 19 were the queue, the rest notes and private addresses (D04: 32 of its 46 requests declined, mostly same_day only from Oulu).

**What dealers accepted.** A logistic fit on our 940 real quotes (win ~ quote ratio, the dealer's trust count, the day, whether same_day was quoted, the list price):

| Term | Effect on the price a dealer accepts, in list prices | |
|---|---|---|
| Monday, no trust, €66 list | 1.32 at a 50% chance; the curve's scale is 0.11 (the quoter assumes 0.2) | |
| Tuesday / Thursday / Friday | +0.09 / +0.24 / +0.06 | |
| Wednesday (price war, 08–18) | −0.22 | ±0.03 |
| Each order on time to the dealer | +0.016 | ±0.0015 |
| A cheaper car, per halving of the list price | −0.075 | ±0.013 |
| same_day offered and not quoted | −0.09 | ±0.02 |
| same_day offered and quoted | −0.05 | ±0.03 |

Win rate by our quote ratio and day (n / won %):

| Day | 1.2–1.3 | 1.3–1.4 | 1.4–1.5 | 1.5–1.7 | 1.7–2.0 |
|---|---|---|---|---|---|
| Mon | 65 / 52% | 62 / 32% | 25 / 28% | 19 / 5% | 8 / 0% |
| Tue | 13 / 77% | 54 / 65% | 47 / 47% | 44 / 20% | 18 / 17% |
| Wed | 48 / 38% | 57 / 26% | 30 / 33% | 36 / 3% | 12 / 0% |
| Thu | 1 | 14 / 71% | 21 / 76% | 51 / 43% | 85 / 58% |
| Fri | 2 | 8 / 100% | 48 / 40% | 55 / 49% | 23 / 35% |

The quoter followed the level up (Thursday 1.75) but on Monday and Wednesday its cost held the price up: the median quote stayed at 1.33–1.38 all Wednesday while we won 20%. This agrees with track 2's queue rebuild (the queue never reached 35) and with track 3's `step`/`boost` runs (a faster level loses): on the price war day the level is not slow, the car's cost is the floor.

**By lane length.**

| Road km | Requests | Won | Win % | Typical ÷ list | Our cost ÷ typical | Margin/order | Single gig: opening fee ÷ typical | Booked within 5 min |
|---|---|---|---|---|---|---|---|---|
| 0–50 | 89 | 15 | 17 | 0.67 | 1.50 | €14 | 1.29 | 90% (n=10) |
| 50–100 | 172 | 48 | 28 | 0.99 | 1.01 | €22 | 0.87 | 42% |
| 100–200 | 287 | 110 | 38 | 0.98 | 0.91 | €36 | 0.85 | 51% |
| 200–300 | 158 | 82 | 52 | 0.97 | 0.85 | €51 | 0.85 | 26% |
| 300–500 | 195 | 81 | 42 | 0.99 | 0.91 | €76 | 0.85 | 24% |
| 500+ | 129 | 20 | 16 | 1.02 | 1.06 | €105 | 0.86 | 33% |

**The fee floors** (`dispatch/fees.py:234`: the flat fee is kept above 0.85 × typical, and above 1.15 for a lane under 40 km). First single-car gig of each order:

| Opening fee | Gigs | Booked | At the opening fee | Within 5 min | Median minutes | Median viewers |
|---|---|---|---|---|---|---|
| at the 0.85 floor | 181 | 137 | 124 | 62 | 7 | 5 |
| 0.855–1.0 | 49 | 31 | 23 | 9 | 40 | 9 |
| at the 1.15 floor, lane under 40 km | 8 | 8 | 8 | 8 | 1 | 1 |

The model asks for less than the floor on 73% of our single cars, so `fee_flat_up` (tested at −0.15 and −0.2) moves only the other quarter. Two-car gigs cost 0.75 × typical a car and book in 5.5 minutes.

**The late cars.** 10 orders late, €634 of refunds. 6 were D01's, at a trust count of 25:

- R00490 (D01, Porvoo → Turku): delivered Thursday 20:03 against 20:00, refund €9.77. D01's count went 25 → 12. A second (R00672, same_day, a note "closed at 14:00" met by a gig that expired at 14:01) halved it again Friday 10:13.
- D01, real quotes: Thursday 62 requests, 60% won at a median 1.78; Friday 54 requests, 30% won at 1.54. The other dealers: 49% and 48%.
- 5 of the 10 are lanes of 420–830 km won Thursday 09:39–14:29 as next_day (Ylivieska twice, Oulu, Vaasa, Rovaniemi): €531 of refunds. Three of them drew 96–436 views and no booking at 0.85–1.15 × typical until after the deadline.

## 4. Ideas, ranked by expected gain

The euro figures come from the fitted curve at our realised cost per car and ignore that more cars strain the drivers: read them as upper bounds. Dev weeks decide.

| # | Idea | Reason | Evidence | Change | Test |
|---|---|---|---|---|---|
| 1 | **Lower the two fee floors.** | We pay the floor, not what the driver needs. | 181 of 248 single cars open at the 0.85 floor; 124 book at it, half within 7 minutes. All 8 lanes under 40 km book in 1 minute at 1.15, at the first view. About 124 cars × €75 typical × 0.10 ≈ €900 a week at 0.75 if they still book. | `dispatch/fees.py:234`: make 0.85 and 1.15 parameters (`flat_floor`, `flat_short`; two lines, plus `FEES` in `policies/main.py`). No switch exists today. | `--set fee_flat_floor=0.8`, `0.75`; `--set fee_flat_short=1.0`, `0.9`. Watch booking time, drops and the lowest week. |
| 2 | **Price short cars at what they cost.** | The top teams' extra orders are cars under 100 km at about the typical fee; ours cost 1.0–1.5 × typical, so we quote 1.46–1.50 where dealers accept about 1.25. | Section 2 fingerprint; 261 requests under 100 km, 24% won; delivery towns Espoo, Helsinki, Hyvinkää, Vantaa are where the competitor is cheapest (`dispatch/lanes.py`). Short cars are already "safe" cars for the intake. Upper bound +120 orders, +€1.3k a week. | With idea 1 the fee falls; the learned model was trained with the floor, so the quoter also needs a tilt for short lanes: `car_short` (the `car` multiplier for a lane under 100 km) in `ProfitQuoter.prices`. | After idea 1: `--set fee_flat_short=0.95 --set car_short=0.85`, then `0.75`. |
| 3 | **Count a dealer's trust in the cost of being late.** | A late order to a dealer at 25 costs half of that dealer's price premium, far more than its refund. | D01: 31% of requests; Friday 30% won against 60% Thursday; the fit gives +14 orders, +€630 with the count kept at 25. | Exists: `invest` in `ProfitQuoter` (off; no run in any FINDINGS). It adds `risk × count/2 × 1% of the dealer's expected revenue` to the cost and takes the trust gain off early orders. It overvalues early orders of a dealer that reaches 25 anyway, so test it small. | `--set invest=0.25`, `0.5`. |
| 4 | **Raise long lanes that drivers view and pass.** | A flat fee that waits 6 hours loses the car when the lane is 400 km or more. | 5 of 10 late cars, €531; 96–436 views, no booking. Three were D01's (idea 3). The view-count raise was tested for all cars (+€2,760 on 30 weeks, not adopted); the new reason is trust, and the narrower target. | `fee_flat_views` exists; limit it to lanes of 300 km or more (one condition in `Desk.viewed`). | `--set fee_flat_views=40 --set fee_flat_views_steps=2`, with and without the km condition. |
| 5 | **A lower level for cheap cars.** | Dealers accept less over list on a cheap car, and the quoter keeps one level for all. | −0.075 list prices per halving of the list price (±0.013) in this world; `lanes.py` has the same sign from six scans (−0.027 per log). Alone it wins cheap cars at a loss; it pays only after ideas 1 and 2. | `lanes` exists (0.5 gave +€920 on 10 weeks on an older mainline, lowest week 91.7%). | `--set lanes=0.5` on top of ideas 1–2. |
| 6 | **Half the queue charge.** | The charge and the limit bite only on Thursday and Friday afternoon, on cars due a business day later. | 19 queue declines, quotes 0.1–0.2 higher in those windows; upper bound +25 orders, +€1.6k. Track 1's `queue_hours` and `limit=40` gained under €1.5k on 30 weeks and lowered the worst week: low confidence. | `queue` exists (0.3). | `--set queue=0.15`. |

Not worth a run tonight:

- **Lower prices everywhere.** The curve says our quotes sit 0.11–0.17 over the margin optimum at realised cost (all quotes 5% lower: +104 orders, +€2.0k), but `car` 0.9 and 0.85 lost on dev weeks, and Test-Team1114 shows the price-only route. The price follows once the car is cheaper (ideas 1, 2).
- **The price war.** Wednesday 10% lower: +38 orders at €11 each. The margin is in the other four days.
- **More same_day quotes.** 327 of 664 unquoted, but in this world the quote adds only 0.04 list prices (+18 orders, +€920 at most), and `same_day_slack=360` lost a dev week.
- **The requests we price out.** 151 declined or over 2 × list; 96 of them are lanes of 300 km or more. The top teams' revenue per order says they do not take these either.

## How this was made

One frame per world minute from the feed; our queue rebuilt from the events and the journal (an order is `held` while it has no gig or an unbooked one); costs per order from the ledger, a gig's fee shared among its cars; the win curve by Newton steps on the 940 real quotes. The fit is on our own quotes, which are higher where our cost is higher, so its slope may overstate what a lower price wins.
