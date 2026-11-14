# Track 2: Quotes

**Question.** At what price against the list price do quotes start to lose, by lane, dealer, day and hour?

**Answer so far.** A dealer takes a quote whose markup over list is under a limit of about 1.33 ×, and the limits scatter
by about 9% around it. No flat markup beats 1.5 ×, but a quoter that prices each request at the markup with the best
expected margin does, by a third. The limit moves with the options the dealer offers, the list price, the dealer's
trust and, the same in every world, the place the car goes to.

All weeks are level 8 practice weeks on the test team's key. Dev is `dev-01..10`. Study is `t2-study-01..20`, this
track's own seeds. Holdout numbers are the integrator's. "Worst" is the lowest on-time share of a week.

## Findings

### 1. No flat markup beats 1.5 × (e7bf4da, dev)

| Label | Margin | Orders | Worst | Ranked | What it shows |
|---|---|---|---|---|---|
| `ctl` (1.5) | €63,285 | 2,280 | 94.1% | 10/10 | The baseline |
| `m1.3` | €39,455 | 3,757 | 91.3% | 10/10 | More orders at a thin margin, and later |
| `m1.7` | €45,509 | 1,005 | 95.5% | 10/10 | Orders fall faster than the price rises |
| `m1.85` | €24,556 | 432 | 90.0% | 10/10 | |
| `m2.0` | €11,385 | 172 | 95.5% | 10/10 | |

### 2. The dial: price each request by its cost and its chance (`quoter=dial`, a13aa1c)

`DialQuoter` asks for the markup that makes `(price - cost) x chance` largest, and moves its level after every answer.

| Label | Seeds | Margin | Against | Worst | Ranked | What it shows |
|---|---|---|---|---|---|---|
| `dial-c1@a13aa1c` (cost 1.3 / 1.1) | dev | €77,385 | +€8,121 on base, 9/10 | 93.7% | 10/10 | **Merged.** 3,488 orders against 2,280 |
| `dial-c1@a13aa1c` | holdout | €86,501 | +€20,348 on `fr@e7bf4da`, 9/10 | 96.9% | 10/10 | Holds on unseen weeks |
| `dial-c2@a13aa1c` (cost 1.45 / 1.25) | dev | €81,716 | +€4,331 on c1, | 94.9% | 10/10 | Wins on dev |
| `dial-c2` | holdout | €81,480 | −€5,021 on c1, 3/10 | 97.3% | 10/10 | and loses unseen: a cost is a markup, and it must transfer |
| `c2n@1e30321` | study | €168,585 | −€8,877 on `c1n`, 6/20 | 94.1% | 20/20 | The study weeks agree with holdout |
| `c0n@1e30321` (cost 1.2 / 1.0) | dev | €71,862 | −€7,786 on `c1n`, 0/10 | 90.8% | 10/10 | A lower cost takes too many orders |
| `c0n@1e30321` | study | €164,381 | −€13,081, 4/20 | 89.4% | 19/20 | and drops a week out of the ranking |

The cost is above the fees paid (about 1.0 × the typical fee) because every order makes the drivers scarcer for the
others. 1.3 / 1.1 is the only setting that wins on dev, on study and on holdout.

### 3. The place table (`lanes=1`, 2423508)

The handbook says one part of the competitor's lane factor "is almost the same in every world". `dispatch/places.py`
holds it per pickup and per delivery place, fitted on 71,369 quoted requests of 30 practice weeks (`places.py`).
Dealers accept about 10% less for a car to Vantaa, Helsinki, Espoo or Hyvinkää, and 10 to 14% more for one to Kotka,
Savonlinna, Kemi or Ylivieska. Delivery carries most of it. A table fitted on the study weeks takes 7.1% off the dev
weeks' win/loss likelihood, and the reverse holds; the two tables correlate 0.90 for delivery and 0.35 for pickup
(`fit7.py`, `fit9.py`). A full table of 603 lanes adds nothing over pickup plus delivery.

| Label | Seeds | Margin | Against `rd@042b1a3` | Worst | Ranked | Orders, late |
|---|---|---|---|---|---|---|
| `lanes1@2423508` | dev | €90,417 | +€3,869, 8/10 | 94.8% | 10/10 | 3,470, 108 (control 3,498, 116) |
| `lanes1@2423508` | study | €196,046 | +€7,383, 17/20 | 94.3% | 20/20 | 6,940, 133 (control 7,037, 165) |

Both rows play the weeks that the table was fitted on. The unseen tests, on the long-lane base's flags (327f4ce):

| Label | Seeds | Margin | Against | Worst | Ranked | What it shows |
|---|---|---|---|---|---|---|
| `nsd-lanes1@4f287d9` | holdout | €107,905 | +€2,094 on the frozen build, 7/10 | 96.5% | 10/10 | **Passed** (the integrator's run) |
| `lanes1@4f287d9` | dev | €98,104 | +€1,749 on `vr@4f287d9`, 7/10 | 93.9% | 10/10 | In-sample |
| `lanes1@4f287d9` | study | €214,087 | +€3,821, 15/20 | 91.9% | 20/20 | In-sample; the control's worst week is the same 91.9% |
| `lanes-xs@97ae3f6` | dev | €97,149 | +€794 on `vr@4f287d9`, 7/10 | 92.3% | 10/10 | The table fitted on the study weeks alone: half the dev gain is fit |

About €200 a week holds on unseen weeks. On the note-reading gate's build (3ea3f7f, merged as 90a19a6) the control of
the sweeps below is `lanes1@90a19a6`: dev €98,847 (worst 93.4%), study €217,136 (worst 92.4%, `t2-study-12`).

### 3b. Trust in the log (beb6528)

RULES.md line 164: each counted order raises the prices a dealer accepts by 1%, so the limit moves by
`log(1 + trust / 100)`, not by 1% in the log. With every switch off, `vr@4f287d9` makes +€385 on dev against the frozen
build and +€2,640 on study against `vr0@67faf35`.

### 3c. What a week still hides (`fit12.py`, `fit13.py`, `trust1.py`; fits, not played weeks)

- **A dealer is not the same in two worlds.** A table of dealer levels fitted on the study weeks takes 0.0% off the dev
  weeks' win/loss likelihood, and the reverse; the place table takes 8%. So a dealer's level must be learned in the
  week (`dealer_gain`). In hindsight a world's own dealer levels take 6% off, its own pickup and delivery levels 3% each,
  its own slope by list price 1.6% (the slope runs from 0.01 to 0.25 around 0.12).
- **No fat tail above 1.5 ×.** Where the model gives a quote under 5% (mean markup 1.54), 1.7% win. The model is right
  to within a point in every band, so there is no unpriced group of dealers who take any price.
- **Trust is slow, and it is most of the price.** The biggest dealer of a world sends 310 requests a week and reaches a
  mean count of 10 on Tuesday, 19 on Wednesday and 24 on Friday; the second 5, 12 and 21; the others stay under 12.
  At a count of 25 the median quote is 1.56 × and 49% win; at 0 it is 1.32 × and 25% win.

### 4. A request that offers only `same_day` (`only_same`, 4f287d9)

For a car that is ready on a later day, a dealer who offers `same_day` alone accepts about 17% more than one who
offers a later option beside it (dev 0.19, study 0.16, the long-lane base's weeks 0.18; `fit10.py`, `fit11.py`). The
dial quotes these at 1.33 × and wins 78% of them, against 43% elsewhere. About 37 orders a week.

Played, the higher price loses: `lo@4f287d9` (`lanes=1 only_same=0.17`) makes −€1,357 on dev (4/10) and −€1,008 on
study (11/20) against `lanes1@4f287d9`. These are the cheap orders: a car that is ready a day later, with a whole
day for its gig. Winning 78% of them at 1.33 × is worth more than the 17%. Off stays the default.

### 5. `same_day` on a car that is ready today (`today_days`, 46d5dbb; `same_up`)

`same_day=true` at a premium drops weeks out of the ranking: `lsd15@90a19a6` (`same_up=0.15`) makes +€1,613 on dev and
+€15,733 on study against `lanes1@90a19a6`, with 5 of 10 and 17 of 20 weeks ranked. Where it is late (`sd1.py`, dev;
the study weeks agree):

| `same_day` orders of `lsd15` | Orders | Late | Margin per order | Fee / typical |
|---|---|---|---|---|
| under 4 h beyond the drive | 24 | 62% | −€19 | 1.57 |
| 4 to 6 h | 275 | 40% | −€3 | 1.47 |
| 6 to 8 h | 236 | 29% | €8 | 1.30 |
| 8 to 12 h | 233 | 21% | €15 | 1.14 |
| a day or more (the base's `future_same_day`) | 1,021 | 9% | €25 | 1.03 |
| due the same day, asked on Monday | 137 | 9% | €21 | 1.15 |
| ... Tuesday / Wednesday / Thursday | 112 / 127 / 142 | 21 / 29 / 24% | €8 / €5 / €7 | 1.29 / 1.40 / 1.38 |
| ... Friday | 250 | 54% | −€5 | 1.45 |
| one leg, a drive of at most 150 min, 6 h to spare: Monday | 79 (study 59) | 0% (3%) | €22 (€20) | 0.99 |
| ... Tuesday / Wednesday | 71 / 70 (129 / 154) | 11 / 17% (9 / 8%) | €17 / €11 (€16 / €18) | 1.10 / 1.28 |

The week's drivers have room on Monday and none on Friday. `today_days=N` (intake) quotes `same_day` on a car that is
ready today on the first N days, for one leg without a private address, a drive of at most `today_drive` (150) minutes
and `today_hours` (6) beyond the drive; `same_up` prices it 15% above. Against `lanes1@90a19a6`:

| Label | Seeds | Margin | Against | Worst (control) | Ranked |
|---|---|---|---|---|---|
| `ltd1@46d5dbb` (`today_days=1 same_up=0.15`) | dev | €102,456 | +€3,609, 7/10 | 94.4% (93.4%) | 10/10 |
| `ltd1@46d5dbb` | study | €218,752 | +€1,616, 10/20 | 92.1% (92.4%) | 20/20 |
| `ltd1@46d5dbb` | fresh | €218,046 | +€1,697, 14/20 | 83.7% (82.6%) | 19/20 |
| `ltd3@46d5dbb` (`today_days=3`) | dev | €104,037 | +€5,190, 8/10 | 92.7% (93.4%) | 10/10 |
| `ltd3@46d5dbb` | study | €228,190 | +€11,054, 14/20 | 92.5% (92.4%) | 20/20 |

### 6. The crowded day (`crowd`, 95326e6)

`t2-fresh-06` is unranked with and without `lanes` (82.6%): 132 orders were due on Friday for 666 drivers and 51 of them
were late; 47 of the 121 orders won on Thursday were late, at markups of 1.5 to 2.4 and fees of 1.5 to 2.5 × typical. Over
the control's 50 weeks (`due1.py`), by the orders due on one working day for each driver of the week: under 0.10, 2.6%
late (169 days); 0.10 to 0.15, 7.2% (28 days); above, 20.7% (3 days). From 90 to 126 orders due, 36 more orders bring 23
more late ones. The quoter sees this a day ahead, in the deadlines of the orders it has won. `crowd` adds that many
typical fees to the cost for each order already due on the request's day beyond `room` (13) for each 100 drivers.
The room is not local: orders due from one pickup place for each driver near it say less than the whole day (`due2.py`).
The backlog that the desk sees while it happens says less too (`back1.py`). And the driver count misses `t2-fresh-08`
(857 drivers, 100 due on Friday, 19 late).

Against `lanes1@90a19a6` (dev €98,847, worst 93.4%; study €217,136, worst 92.4%; fresh €216,349, worst 82.6%, 19/20 ranked):

| Label | Seeds | Margin | Against | Worst | Ranked | Late (control) |
|---|---|---|---|---|---|---|
| `lcr10r10@95326e6` (`crowd=0.1 room=10`) | dev | €99,990 | +€1,143, 5 better, 3 worse | 96.2% | 10/10 | 84 (105) |
| `lcr10r10@95326e6` | study | €218,392 | +€1,256, 4 better, 2 worse | 93.7% | 20/20 | 158 (181) |
| `lcr10r10@95326e6` | fresh | €218,603 | +€2,254, 5 better, 4 worse | 90.1% | 20/20 | 213 (279) |
| `lcr10r8@95326e6` (`crowd=0.1 room=8`) | dev | €98,059 | −€788, 5/10 | 96.1% | 10/10 | 72 (105) |
| `lcr10r8@95326e6` | study | €217,348 | +€211, 6/20 | 94.7% | 20/20 | 140 (181) |
| `lcr10r8@95326e6` | fresh | €217,200 | +€851, 5 better, 7 worse | 92.3% | 20/20 | 185 (279) |
| `lcr100r11@95326e6` (`crowd=1 room=11`) | fresh | €217,513 | +€1,164, 5/20 | 90.5% | 20/20 | 210 |
| `lcr30r10@95326e6` (`crowd=0.3 room=10`) | fresh | €218,470 | +€2,121, 5/20 | 90.3% | 20/20 | 196 |
| `lcr30@95326e6` (`crowd=0.3`, room 13) | fresh | €217,425 | +€1,076, 3/20 | 89.8% | 19/20 | 243 |
| `lcr05@95326e6` (`crowd=0.05`, room 13) | fresh | €216,173 | −€176, 4/20 | 86.3% | 18/20 | 270 |

`t2-fresh-06` goes from 82.6% and €7,722 to 90.1% and €9,494 with room 10, and to 93.5% and €10,515 with room 8. A week
that never reaches the room plays to the cent as without the switch (27 of 50 weeks with room 10). Room 8 costs the best-paid
orders of a busy week that would have been fine: in `t2-fresh-15` (844 drivers, 99 orders due on Friday, 9% of them late) it
drops 24 orders asked on Thursday at 1.69 × and €1,250. Room 10 earns more on all three sets; room 8 puts every one of the
50 weeks at 92.3% or above.

Per order, by the orders already due on its day per 100 drivers when it was asked (`tight1.py`): under 4, 1.6% late and
€29.64 an order; 6 to 8, 6.4% and €24.77; 8 to 10, 10.9% and €21.28; 10 to 12, 14.0%; 12 to 14, 23.3%; 14 or more, 48.5%
and €11.12. With under 30 hours to the deadline it is 3.6% late under 4 and 25 to 49% from 12; with 36 hours or more it
stays near 1%. The drivers who view gigs say no more than the driver list: orders due per driver of the list correlates
0.63 with a day's late share over 150 days, per viewer of the day before 0.47 (`view1.py`). With room 8 the fees thread's
`day_cap=0.12` never acts: `dc12cr@3cc6e23` plays `t2-fresh-06`, `-07` and `-08` to the cent as `lcr10r8`.

### 7. Monday's `same_day` with the crowded day (`today_days=1 same_up=0.15 crowd=0.1 room=8`, 95326e6)

Room 8 alone gives up the best-paid orders of a busy Thursday; `today_days=1` alone leaves the worst weeks where they
were. Together, against `lanes1@90a19a6`:

| Label | Seeds | Margin | Against | Worst (control) | Ranked | Late (control) |
|---|---|---|---|---|---|---|
| `ltd1cr@95326e6` | dev | €101,735 | +€2,888, 6/10 | 96.2% (93.4%) | 10/10 | 80 (105) |
| `ltd1cr@95326e6` | study | €218,636 | +€1,500, 10/20 | 95.3% (92.4%) | 20/20 | 151 (181) |
| `ltd1cr@95326e6` | fresh | €220,773 | +€4,424, 13/20 | 93.3% (82.6%) | 20/20 | 178 (279) |
| `ltd1c10@95326e6` (the same with `room=10`) | dev | €101,816 | +€2,969, 5/10 | 95.1% | 10/10 | 85 |
| `ltd1c10@95326e6` | study | €217,931 | +€794, 9/20 | 93.6% | 20/20 | 176 |
| `ltd1c10@95326e6` | fresh | €220,488 | +€4,139, 14/20 | 89.1% | 19/20 | 223 |
| `ltd2cr@95326e6` (`today_days=2`, room 8) | dev / study / fresh | €103,276 / €223,052 / €220,110 | +€4,429, 8/10 / +€5,916, 12/20 / +€3,761, 14/20 | 95.0% / 94.4% / 91.5% | all | 84 / 164 / 198 |
| `ltd3cr@95326e6` (`today_days=3`, room 8) | dev / study / fresh | €104,936 / €227,575 / €224,074 | +€6,089, 8/10 / +€10,438, 14/20 / +€7,725, 16/20 | 95.3% / 94.6% / 90.8% | all | 91 / 184 / 236 |
| **`ltd3h8cr@95326e6`** (`today_days=3 today_hours=8`, room 8) | dev / study / fresh | €106,041 / €229,076 / €225,840 | **+€7,194, 9/10 / +€11,939, 17/20 / +€9,491, 15/20** | 96.5% / 95.1% / 92.1% | all | 84 / 158 / 201 |
| `ltd4h8cr@95326e6` (`today_days=4 today_hours=8`) | fresh | €226,748 | +€10,398, 16/20 | 90.8% | 20/20 | 225 |
| `ltd3h10cr@95326e6` (`today_days=3 today_hours=10`) | fresh | €223,667 | +€7,318, 11/20 | 92.1% | 20/20 | 201 |
| `ltd3h8s30@95326e6` (as `ltd3h8cr` with `same_up=0.3`) | dev / study / fresh | €100,670 / €222,089 / €222,460 | +€1,823, 9/10 / +€4,953, 13/20 / +€6,111, 14/20 | 96.0% / 93.1% / 91.7% | all | 74 / 151 / 172 |
| `ltd3h8s8@95326e6` (as `ltd3h8cr` with `same_up=0.08`) | dev / study / fresh | €106,024 / €230,292 / €226,947 | +€7,177, 8/10 / +€13,156, 19/20 / +€10,598, 16/20 | 95.8% / 93.7% / 90.0% | all | 99 / 184 / 233 |
| `ltd3c10@95326e6` (`today_days=3`, room 10) | dev / study | €105,581 / €228,013 | +€6,734, 9/10 / +€10,877, 14/20 | 93.3% / 93.7% | all | 116 / 195 |
| `lcr30r10@95326e6` (`crowd=0.3 room=10`, no `today_days`) | dev / study | €99,072 / €216,823 | +€225, 5/10 / −€313, 3/20 | 96.5% / 93.7% | all | 79 / 160 |
| `lcr10r9@95326e6` (`crowd=0.1 room=9`) | fresh | €217,095 | +€746, 3 better, 6 worse | 91.5% | 20/20 | 192 |

With room 8 every one of the 50 weeks is at 93.3% on time or above. With room 10, `today_days=1` puts `t2-fresh-06` back
under 90%: room 10 alone ranks that week by 0.1 points (90.1%), so it has no room for more orders.

More days earn more, and the hours to spare decide the floor. In the fresh weeks of `ltd3cr`, `same_day` due the same
day is 0 of 48 late on Monday, 5 of 89 on Tuesday and 35 of 117 on Wednesday. With 8 hours beyond the drive instead of 6
(`ltd3h8cr`) three days make +€28,624 over the 50 weeks, about €570 a week, better in 41 of them, with 443 late orders
against 565 and every week ranked; `t2-fresh-06` is at 92.2%. One day (`ltd1cr`) keeps the highest floor.
A fourth day, 10 hours, and a premium of 30% each make less or lower the floor; a premium of 8% makes €2,300 more
over the 50 weeks with 516 late orders against 443 and one fresh week at 90.0%, so 15% stays.

### 8. The other dial switches on top of the Sunday build (`ltd3h8cr@95326e6`)

Each switch alone on top of `lanes=1 today_days=3 today_hours=8 same_up=0.15 crowd=0.1 room=8`, against `ltd3h8cr@95326e6`
(dev €106,041, worst 96.5%; study €229,076, worst 95.1%; fresh €225,840, worst 92.1%). None wins on all three sets, and
every one loses on dev.

| Label | Switch | dev | study | fresh | Worst dev / study / fresh | Ranked |
|---|---|---|---|---|---|---|
| `hday@95326e6` | `day_sd=0.12 gain=0.015` | −€1,036, 6/10 | +€4,132, 14/20 | +€3,051, 10/20 | 95.5 / 94.7 / 92.7% | all |
| `hb3@95326e6` | `brake=3` | −€3,527, 2/10 | +€3,504, 13/20 | +€2,766, 13/20 | 95.7 / 95.8 / 93.2% | all |
| `hlg2@95326e6` | `list_gain=0.02` | −€1,511, 4/10 | +€4,220, 11/20 | −€443, 12/20 | 95.9 / 94.7 / 89.5% | fresh 19/20 |
| `hpg2@95326e6` | `place_gain=0.02` | −€2,109, 3/10 | +€496, 8/20 | −€3,048, 7/20 | 96.8 / 95.2 / 92.7% | all |
| `hw3@95326e6` | `war=0.3` | −€1,175, 6/10 | −€1,554, 10/20 | −€2,374, 9/20 | 95.8 / 94.3 / 90.5% | all |
| `hb6@95326e6` | `brake=6` | −€4,731, 1/10 | −€970, 11/20 | −€3,695, 10/20 | 95.6 / 94.8 / 91.1% | all |

The integrator held out the two best anyway. `hday`: holdout €117,961 (+€1,786, 6/10, worst 96.9%), orch-01..10 €114,733
(+€675, 6/10, worst 92.8%). `hb3`: holdout €117,338 (+€1,163, 5/10, worst 95.0%), orch €113,998 (−€60, 5/10, worst 91.6%).
Both fall under 93% in `orch-08` and lose on dev, so neither is merged. `brake` wins about 600 more orders over 50 weeks
by lowering the cost in a calm week, and pays for them in the weeks that turn. `list_gain=0.05` was not played.

The Sunday build is `ltd3h8cr` as it is: holdout €116,176 (+€4,018 on `crowd=0.1 room=10`, 7/10, worst 95.3%), orch-01..10
€114,058 (+€4,863, 8/10, worst 93.0%), the integrator's runs; 3a2dce2 on `sunday-ltd3h8`.

### 9. Where the Sunday build's orders and late orders are (`vol1.py`, `week1.py`, `thin1.py`, `load1.py`; saved weeks, no plays)

70 weeks of `ltd3h8cr@95326e6` (dev, study, fresh, and the integrator's holdout and orch weeks). A week has 1,036
requests; the intake declines 172, the dealers take 352 of the 864 quoted, and the margin is €11,303.

- **`orch-08`, the week that broke `day_sd` and `brake`.** It has 639 drivers, the fewest of the orch weeks, and only 16
  of them within 30 km of Turku or Raisio (29 to 51 in the other weeks). 11 of its 22 late orders are Turku–Raisio cars:
  a drive of 8 minutes at a list price of €22, quoted at 1.10 to 1.38 ×, mostly `same_day`, whose gigs waited for 1.75
  to 2.5 typical fees. `crowd` counts the whole week's drivers and does not see one town's.
- **The same holds in every week.** A drive under 30 minutes from a pickup with under 50 drivers within 30 km: 6.4
  orders a week, 22% late, €4 an order, 1.4 typical fees paid. With 50 to 150 drivers: 3.9 orders, 10% late, €11. With
  150 or more: 40 orders, 2.4% late, €15. A longer drive from a place with few drivers is not late (30 to 60 minutes,
  under 20 drivers near: 27 orders a week, 1.3% late, €19 an order). So the short cheap car from a thin town brings
  €29 a week and 1.4 of the week's 8 late orders: `thin` prices it at what it costs (below).
- **The load of the deadline day when a car is asked** (orders already due that day for each 100 drivers; drives
  under 300 minutes): under 2, fees 0.95 typical and 1% late; 2 to 4, 0.97 and 2%; 4 to 6, 1.03 and 3%; 6 to 8, 1.08
  and 5%; 8 to 10, 1.10 and 9%. The quoter's cost is 1.3 or 1.1 typical fees at every load under the room: `idle`
  lowers it on an empty day (below).
- **A week's margin is its win share** (correlation 0.85); the number of drivers says little (0.21). Weeks with 600 to
  700 drivers make €9,903 at 3.8% late, weeks with 700 to 1,000 about €11,700 at 1.4 to 2.4% late.
- **Where the volume is:** list price under €30: 58% won at 1.18 ×, €13 an order. List €110 or more: 34% declined, 26%
  won at 1.72 ×, €76 an order. A request with only `same_day`: 65% declined, 67% of the quoted won. Monday: 35% won at
  1.28 ×, against 44 to 50% from Tuesday, when the dealers' trust has grown.
- `hf100@95326e6` (`floor=1.0`, the cheap cars quoted under 1.10 ×): dev −€622 (5/10), study −€1,575 (9/20). The
  floor stays.

### 10. The outage (`outage`, 4d3e86a; `outage1.py`, `outage3.py`)

RULES.md: on one working day the competitor is down from 08:00 to 18:00 around one town (80 km), and the dealers
there pay a backup about 30% dearer. Nobody announces it, but our own answers show it: in 54 of the 70 weeks one day
and region wins at 5 standard errors or more above the rest of that day, by the pickup place (by the delivery place
only 9 weeks do). It is the Helsinki region in 51 of the 54 (Vantaa, Porvoo, Hyvinkää as the centre).

| Drives under 300 min, a week | Quoted | Quoted at | Win | Orders |
|---|---|---|---|---|
| The day before, inside the region | 91 | 1.41 × | 43% | 39 |
| The outage day, inside | 96 | 1.50 × | 67% | 64 |
| The outage day, outside | 56 | 1.53 × | 29% | 16 |
| The day after, inside | 75 | 1.46 × | 45% | 34 |
| Other days, outside | 125 | 1.41 × | 39% | 49 |

So 64 of a week's 352 orders are won in the outage, at a price only 6% above the day before: the dial climbs by 0.03
an answer and never reaches the 30%. And it climbs for every region, so outside the outage the win share falls from
38% to 29% that day. `outage=0.26` is the war's switch for a region: each answer moves the chance of an outage around
each of the 30 towns (one chance in five each morning, shared evenly), a quote's chance is the mix, and the dial learns
only what the mix did not expect. A restarted desk finds the same chances from the history (test).

Played, the switch is a tie: `hout26@4d3e86a` (`outage=0.26`) makes −€946 on dev (4/10, worst 95.9%) and +€522 on study
(11/20, worst 95.5%), with 232 late orders against 242. In the 19 of the 30 weeks with a clear outage it does what it was
built for (`outage6.py`): on the outage day it quotes the region at 1.62 × against 1.58 ×, wins 72 cars there against 76
and makes +€79; outside the region it quotes 1.55 × against 1.60 ×, wins 18 against 15 and makes +€66. On the other
days it sees outages that are not there and loses €79 a week, and in the 11 weeks without a clear outage it only has
those. The dial that follows the region up already collects most of an outage; what the switch adds is under 1% of a week.

**Why a lower price does not buy volume.** A week's requests are elastic (a limit's spread is 0.09 in the log), so at
the fees paid (0.9 of list) the best markup at an even chance would be 1.28 ×, not 1.40 ×. But the drivers are the
limit: `c0n` (cost 1.2 / 1.0) won 14.5% more orders and made 10% less, and `hf100` loses too. A driver's second gig of a
day is not cheaper either (`chain1.py`, 50 weeks: 0.98 typical fees when it starts within 30 minutes of the first gig's
end, 1.03 further away, against 1.01 to 1.07 for a first gig), so there is no cheap volume behind our own drivers.
The 172 declined requests a week (`decl1.py`) are 74 with `same_day` alone that is due today, about 50 long legs,
and about 33 with under 20 drivers near both ends; those are the intake's.

### 11. How much a paired test can see (`noise1.py`), and what is left in the quoter

The world is deterministic, but any change re-rolls it: a variant that changes ten quotes a week (`thin`) differs from
the control by a standard deviation of €410 to €450 a week, the dial switches by €460 to €680. So the total of the 10
dev weeks has a standard error of about €1,500 to €2,000, and of 50 weeks about €3,500 to €4,500: a switch that is
truly worth 1% of a week (€110) fails "beats the control on dev" one time in four, and one worth nothing passes five
times in ten. Over all the weeks played, against `ltd3h8cr@95326e6`:

| Label | Weeks | Mean a week | Standard error | Better |
|---|---|---|---|---|
| `hday` (`day_sd=0.12 gain=0.015`) | 70 | +€123 | €64 | 42/70 |
| `hb3` (`brake=3`) | 70 | +€55 | €81 | 38/70 |
| `hlg2` (`list_gain=0.02`) | 50 | +€45 | €83 | 27/50 |
| `hout26` (`outage=0.26`) | 30 | −€14 | €85 | 15/30 |
| `hf100` (`floor=1.0`) | 50 | −€40 | €85 | 23/50 |
| `hpg2` (`place_gain=0.02`) | 50 | −€93 | €65 | 18/50 |
| `hw3` (`war=0.3`) | 50 | −€102 | €74 | 25/50 |

What the saved weeks say is left (no plays):

- **The fee, not the price** (`fee1.py`). A week's 352 orders bring €32,637 and cost €20,895 in fees, 1.02 typical fees.
  168 of them book at the opening fee (0.85 typical; €39 an order, 0.3% late) and 49 at 1.3 to 1.4 typical (€20 an
  order). The 14 orders a week that pay over 1.5 typical fees lose €249 together and 37% of them are late. Every order
  at the opening fee would be €3,460 a week more. A car asked on Friday pays 1.13 typical fees (40% of them 1.25 or
  more) against 0.96 to 1.00 on the other days; a drive under 30 minutes pays 1.12 and is 5.6% late.
- **The competitor answers our wins** (`react1.py`; HANDBOOK: each morning it lowers its prices for a dealer whose
  requests we mostly won, and raises them where we won few). For a week's three biggest dealers, with a level for
  each week and day and each week and dealer, a dealer of whom we won 60% or more the day before accepts 3.5% less
  the next day, and one of whom we won under 30% accepts 2% more (the outage and a regression to the mean are in these
  numbers too). It is a few percent on one day, as the handbook says: too little to steer by.

### 12. The thin town and the day's level together (`hdth@e29df59`: `day_sd=0.12 gain=0.015 thin=1.0`)

`thin` adds up to one typical fee to the cost of a drive under 30 minutes from a pickup with under 150 drivers within
30 km (§9: 22% of such orders are late with under 50 drivers near, and they make €4 each). Alone it does not pay:
`hth10@4d3e86a` makes −€1,995 on dev (3/10), +€1,492 on study (12/20) and −€2,653 on fresh (8/20, worst 91.4%); −€63 a
week ± €70 over the 50 weeks.

With the day's level (`day_sd`, §8: +€123 a week ± €64 over 70 weeks, but 92.7% and 92.8% in two weeks) it is the first
quoter variant that beats the Sunday build on all three sets, against `ltd3h8cr@95326e6`:

| Set | `hdth@e29df59` | Δ | Better | Worst week | Late (control) |
|---|---|---|---|---|---|
| dev | €106,832 | +€790 | 7/10 | 96.8% | 65 (84) |
| study | €234,609 | +€5,533 | 14/20 | 95.1% | 132 (158) |
| fresh | €227,584 | +€1,744 | 12/20 | 92.5% (`t2-fresh-06`; control 92.2%) | 179 (201) |

Pooled: +€161 a week ± €73, better in 33 of 50 weeks, all ranked. `t2-fresh-08` goes from 92.1% to 93.8%. The day's
level wins more of a morning's cars; `thin` keeps the ones that would be late out of that. With the integrator for
holdout, in its form on top of `ahead_from=10` (below).

### 13. On top of `ahead_from=10` (the simple-bots thread's 2bba163; branch `t2-ah10`, 2da93fa)

`ahead_from=10` posts a single car that is ready now, from 10:00 on, as tomorrow's work. `sl-ah10@2bba163` makes
€113,172 on dev, +€7,131 on the Sunday build (9/10, worst 95.2%): the fee paid falls from 1.02 to 0.99 typical fees, for a
`next_day`-only order from 1.17 to 1.06, and for a car asked on Friday from 1.13 to 1.02 (`ah1.py`). That is the fee gap
of §11, and it is not the quoter's. `ah@2da93fa` (this branch with every quoter switch off) reproduces
`sl-ah10@2bba163` on `dev-01` and `dev-02` to the cent.

`ahdth@2da93fa` (`ahead_from=10` with `day_sd=0.12 gain=0.015 thin=1.0`) loses on dev: €110,527, −€2,645 on
`sl-ah10@2bba163` (2/10, worst 96.5%, 77 late against 68). The integrator's holdout of `sl-ah10@2bba163` passed
(€121,676, +€5,500, 7/10, worst 97.0%), so `ahead_from=10` is the base and `hdth` without it is moot. Later runs are on
246669f (2da93fa with the fix 74cc5a7, which is what ships).

On the study and fresh weeks `ahdth@2da93fa` does not settle it: study €250,900, +€7,501 on `ah@2da93fa` (17/20, worst
97.1%, 110 late against 125); fresh €237,712, −€1,197 on `sl-ah10@2bba163` (9/20, worst 92.0%, 199 late against 198).
Over the 50 weeks +€73 a week, better in 28: what the noise gives (§11). The study weeks favour the day's level every
time (`hday` +€4,132, `hdth` +€5,533, `ahdth` +€7,501) and the dev and fresh weeks do not; no reason found. What
holds is the floor: `t2-fresh-06` is 92.0% against 90.9%. `ah@2da93fa` itself makes €243,398 on study, +€14,322 on the
Sunday build, better in 20 of 20.

The Sunday candidate is now aeb03ea (`sl-wkah`: weekend fees, `ahead_from=10` with its note guard, `long_markup=1.05`).
Branch `t2-wkah` (e457c06) is aeb03ea with this track's switches, all off by default.

## What failed

| Label | Seeds | Margin | Against | Worst | Ranked | Why |
|---|---|---|---|---|---|---|
| `c2-ladder005@8d00a71` (trust ladder) | dev | €81,083 | −€633 on `dial-c2`, 6/10 | 93.3% | 10/10 | An on-time order is worth 1% on the dealer's later prices; buying it with a lower price costs more |
| `detail1@2423508` (cost per class) | dev | €88,290 | +€1,743 on `rd`, 5/10 | 94.9% | 10/10 | Fitted on dev |
| `detail1@2423508` | study | €187,004 | −€1,659, 7/20 | 93.9% | 20/20 | and loses where it was not fitted. It does cut late orders, 217 against 281 |
| `all5@3034b76` (war, day_sd, detail, dealer_gain, place_gain) | dev | €82,433 | +€2,785 on `c1n`, 8/10 | 94.2% | 10/10 | |
| `all5@3034b76` | study | €181,705 | +€4,243, 15/20 | 92.5% | 20/20 | A week under 93% |
| `sd0@2423508` (`same_day=true`) | dev | €81,526 | −€5,022 on `rd`, 3/10 | 75.5% | 0/10 | `same_day` on a car that is ready today is late too often at any price we tried |
| `sd0@2423508` | study | €192,961 | +€4,298, 12/20 | 70.2% | 10/20 | |
| `ldg@90a19a6` (`lanes=1 dealer_gain=0.02`) | dev / study | €98,847 / €216,585 | €0, 6/10 / −€551, 9/20 on `lanes1@90a19a6` | 93.1% / 92.9% | all | A dealer's own level is learned too late in the week to pay; the replay had it at +€1,277 |
| `lsd15@90a19a6` (`same_day=true same_up=0.15`) | dev / study | €100,460 / €232,869 | +€1,613, 6/10 / +€15,733, 17/20 | 83.4% / 77.2% | 5/10, 17/20 | See 5: `same_day` that is due today is late too often after Monday |
| the trust ladder, reworked (8f15e0c, f36ed37) | replay | €85,782 at best | +€6 on €85,776 (`ladder=0.005 ladder_drive=150`); every other form −€120 to −€5,000 | | | Not played: the replay says a count costs more in price than it returns |

Also ruled out, in the replay or in the earlier lab weeks: cold direct offers, rationing drivers, a late budget, fees by
driver density, and absolute lane prices.

## Tools

- `lab.py`: saved weeks to one row per request. `fitlib.py`: the logistic fit of the limit.
- `prep.py`, `sim.py`: a replay of the dev weeks' requests against a quoter, offline. It ranks variants; its euros are
  an estimate, and the played weeks decide.
- `places.py`: writes `dispatch/places.py`.
- `rejoin1.py`: a restart check without a server. One desk handles a played week's events up to a cut; another rejoins from
  the same history. On `ltd3h8cr@95326e6` (`t2-fresh-06`, `t2-study-12`, `dev-10`; four cuts each) the first desk sends
  exactly the played week's actions, and the rejoined quoter equals it in all 49 attributes: every quote, the dial, the
  crowded days, the trust.
