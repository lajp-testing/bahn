# Simple bot and outside-the-box framings

**Questions.** Does a bot of one price rule and one fee rule come close to our best? Which assumptions of the reach desk cost us money?

All weeks are level 8 on the dev seeds, test key, practice worlds on t3. Logs are in `logs/simple/`. A label's weeks are in the shared index.

## Findings

**1. A bot of 85 lines beat the frozen best of that hour, but it is not ranked on every week.** `dispatch/policies/simple.py` quotes list × m on every option whose deadline is at least 24 hours after the answer, for cars that drivers can reach; m follows the win rate towards `target`. The fee opens at 0.85 × typical and climbs 0.05 an hour to 1.1 ×.

| Label | Dev total | Worst week | Ranked | Orders |
|---|---|---|---|---|
| `dn19@2c73800` (frozen best at the time: dial-c1 + night19) | €79,624 | 94.0% | 10/10 | 3,482 |
| `simple-t45@1cb3c0c` (`target=0.45`) | €89,370 | 86.9% | 8/10 | 3,337 |
| `simple-flat145@1cb3c0c` (`gain=0`: a flat list × 1.45) | €87,438 | | 6/10 | 3,465 |
| `simple-r4@8b26548` (`ramp=4`) | €95,253 | 87.5% (dev-02) | 9/10 | 3,366 |

The simple bot earned more than the dial desk because of one rule the desk did not have: it takes a `same_day` option whenever the deadline is a day away. The dial, the reach test and the night fees buy on-time share, not margin: the simple bot falls under 90% on one to four weeks of ten. Finding 2 moves that one rule into the desk.

**`plain=true ramp=4` is ranked on every dev week and ties the frozen build on dev and fresh, but it is 6.7% behind over 40 weeks.** `plain=true` also declines trade-ins and private addresses. Against `lanes1@90a19a6` (the build frozen for the Saturday round: dial quoter with lanes, note reader, long and thin lanes, night fees):

| Weeks | `lanes1@90a19a6` | `simple-plain-r4@647ebfb` | Difference | Simple better on | Ranked (lanes / simple) | Worst ranked week (lanes / simple) | Orders (lanes / simple) |
|---|---|---|---|---|---|---|---|
| dev-01..10 | €98,847 | €98,858 | +€11 | 5/10 | 10 / 10 | 93.4% / 93.8% | 3,417 / 2,995 |
| t2-fresh-01..10 (unseen) | €102,108 | €99,489 | −€2,619 | 4/10 | 9 / 9 | 90.2% / 90.2% | 3,617 / 3,099 |

Both miss the delivery minimum on t2-fresh-06 only (82.6% and 85.5%). On the fresh weeks the simple bot wins the four hardest for lanes (fresh-06 +€2,250, -07 +€343, -08 +€3,205, -09 +€1,162) and loses the easy ones (fresh-01 −€3,122, -03 −€2,881, -04 −€1,732), with a lower on-time share on 5 of 10 and a higher one on 3. It takes about 13% fewer orders at a higher margin each. `simple-t40@647ebfb` (`target=0.40`, without `plain`) is worse: €93,767, ranked 9/10 (dev-02 87.3%).

The integrator then played it on the weeks it had not seen (control `rg-lanes1@90a19a6`, the same build):

| Weeks | Lanes | `simple-plain-r4@647ebfb` | Difference | Simple better on | Ranked (lanes / simple) | Simple's worst week | Orders (lanes / simple) |
|---|---|---|---|---|---|---|---|
| hold-01..10 | €112,271 | €97,030 | −€15,241 | 3/10 | 10 / 10 | 94.5% | 3,307 / 3,003 |
| orch-01..10 | €109,124 | €98,870 | −€10,254 | 4/10 | 10 / 10 | 93.8% | 3,499 / 3,046 |
| All 40 weeks | €422,350 | €394,247 | −€28,103 (−6.7%) | 16/40 | 39 / 39 | | 13,840 / 12,143 |

So the tie on dev and fresh did not hold. **The gap is the long lanes, not the price** (`.amp/in/gap.py`, `.amp/in/meant.py`):

- On the requests the simple bot means to win, the two builds win the same number of orders: 12,257 (simple) against 12,247 (lanes) over the 40 weeks, at the same price over list (1.44 to 1.47) and about €33 an order.
- Lanes also takes legs of 300 to 600 road minutes, which the simple bot declines (`max_drive=300`): 600 orders worth €65,972 over the 40 weeks (dev 118, €13,511; fresh 181, €14,934; holdout 159, €20,383; orch 142, €17,144), €110 an order. That is more than the whole gap.
- Private addresses give lanes little: 1,064 orders, €11,137. Trade-ins: 67 orders, €6,062.
- The markup that follows the win rate holds the simple bot at 40 to 46% of the quotes it means in every week. In a rich week lanes wins 49 to 56% of the same requests (hold-09, hold-10, orch-04, -06, -09) where the simple bot raises its markup to 1.5 to 1.8 instead; in a poor week the simple bot buys orders at 1.2 to 1.3 x list (hold-05: 42% against lanes' 28%). Over 40 weeks the two cancel.

A load rule cannot close this gap: it removes orders. `max_drive=600` is the first thing to play.

**`load=<orders per driver>`** (branch `simple-load`, `b24aa99`, 98 lines; played below): an option whose deadline day already holds that many orders per driver of the world is not quoted, so the dealer can take a later one; quotes still open count at the win target; the last Monday never fills. Offline, with the recorded dealers' answers (`.amp/in/replayload.py`), `load=0.12` cuts 79 of 6,156 orders over dev and fresh (about €3,100) and `load=0.10` cuts 250 (about €8,200); on t2-fresh-06 they remove 4 and 10 of the 41 late orders directly. Looked at and dropped (`.amp/in/feat.py`, `.amp/in/yard.py`, `.amp/in/supply.py`): no order class explains the lateness (long one-day cars are 11.5% late and earn €58 each); orders per driver near the pickup yard predict lateness no better than orders per driver of the world; how fast Monday's and Tuesday's gigs find drivers does not tell a thin week.

**2. `same_day_slack=1440`: take a `same_day` option whose deadline is at least 24 hours after the answer.** (`dispatch.intake.ReachIntake`, off by default.) The desk declined `same_day` unless it was the request's only option (`future_same_day`). Most `same_day` options are for a car that is ready tomorrow and due tomorrow at 20:00. That is a day of notice, and dealers accept the dial's `same_day` price far more often than its `next_day` price. Plain single-car requests only.

| Label | Base | Dev total | vs base | Better on | Worst week | Ranked | Orders |
|---|---|---|---|---|---|---|---|
| `dc2slr4@8b26548` | `dc2r4@8b26548` (dial-c2, step 0.05, ramp 4) | €101,324 | +€12,266 | 9/10 | 92.1% (dev-10) | 10/10 | 3,100 |
| `dn19sl@8b26548` | `dn19@2c73800` | €92,210 | +€12,586 | 8/10 | 90.5% (dev-10) | 10/10 | 3,880 |
| **`rdsl@9aa46e8`** | `rd@bc3b064` (+ note reader) | **€100,631** | **+€14,648** | **9/10** | 92.7% (dev-10) | 10/10 | 3,909 |
| `rdslr4@9aa46e8` (+ `ramp=4`) | `rd@bc3b064` | €100,749 | +€14,766 | 9/10 | 91.8% (dev-10) | 10/10 | 3,916 |
| `rdslr6@9aa46e8` (+ `ramp=6`) | `rd@bc3b064` | €100,823 | +€14,840 | 9/10 | 91.6% (dev-10) | 10/10 | 3,919 |
| `llsl@815c5f4` | `vol-rd-ll+mk115+tb20@e9f4286` (+ long and thin lanes) | €106,211 | +€11,446 | 8/10 | 90.8% (dev-10) | 10/10 | 3,837 |
| `llsl28@815c5f4` (`same_day_slack=1680`) | `vol-rd-ll+mk115+tb20@e9f4286` | €102,365 | +€7,600 | 7/10 | 91.0% (dev-10) | 10/10 | 3,730 |
| `llsl30@815c5f4` (`same_day_slack=1800`) | `vol-rd-ll+mk115+tb20@e9f4286` | €103,076 | +€8,311 | 7/10 | 92.3% (dev-10) | 10/10 | 3,701 |
| **`nssl@815c5f4`** | `vol-rd-ll+mk115+tb20+nosd@e9f4286` (+ `long_same_day=false`, the 327f4ce flags) | **€107,825** | **+€11,856** | **9/10** | 92.3% (dev-10) | 10/10 | 3,835 |

The gain holds on five bases, and on the holdout weeks: the integrator's run of `nssl@815c5f4` on the 327f4ce flags made €118,603 against €105,811 (+€12,792, better on 10 of 10, worst week 95.2%). A longer slack (28 or 30 hours) gives up €3,100 to €3,800 of it and still leaves dev-10 under 93%. The cost is on-time share: 95.1% overall against 96.4%, and dev-10 falls under the 93% that the other tracks hold. The new `same_day` orders are late 5% of the time, spread over all ready times and drive lengths (`.amp/in/window.py`), so no narrower class removes the lateness.

**3. `ramp=N`: climb towards the urgent fee before the deadline warning.** (`dispatch.fees.Fees`, off by default; ported to reach-intake as `e349483`.) `dc2r4@8b26548` €89,058 against `dc2st05@2c73800` €86,828: +€2,230, better on 8 of 10, worst week 94.7%. On top of the slack rule it adds €118 (`ramp=4`) or €192 (`ramp=6`) and lowers the worst week, so it does not pay for the slack rule's lateness.

**4. Late orders are decided before the urgent fees start.** In `rdsl@9aa46e8` (`.amp/in/late.py`), by when the order's driver booked:

| Driver booked | Orders | Fee / typical | Late | Margin |
|---|---|---|---|---|
| More than 3 hours before the last pickup | 3,653 | 1.03 | 1.1% | +€106,009 |
| In the 3 hours of the warning | 98 | 1.73–2.20 | 5% | −€848 |
| After the last pickup | 129 | 1.55–2.33 | 100% | −€4,110 |
| Never | 9 | | 100% | −€1,086 |

The urgent fees work when a driver books inside the warning. After the last pickup the order is late whatever the fee, yet the gig stays at up to 2.5 × typical. The refund is 25% of the price from 2 to 24 hours late, so `past=<factor>` (`dispatch.fees.Fees`, off by default) takes such a gig off the urgent fees: it climbs again from `past` × typical, a step an hour to 1.5 ×, and goes to 2.5 × only 14 hours after the last pickup. `llpast@9e3e1dd` (`past=1.0`, no slack rule) €96,109 against `vol-rd-ll+mk115+tb20@e9f4286` €94,765: +€1,344, better on 5 of 10, every week ranked, worst week 94.6% against 94.1%. dev-10 gains €777 and dev-08 €712; the largest loss is dev-03 at −€425. Clean commit: branch `simple-past`, `bd2b284` on `327f4ce`.

**5. The slack rule's worst week is one night of drops.** (`.amp/in/flu.py`, `.amp/in/drops.py`, `.amp/in/days.py`.) In dev-10 of `llsl@815c5f4`, 33 booked gigs come back between 00:00 and 02:00 on Friday. No forecast names that day; it looks like the handbook's flu. 18 of them are booked again by 13:00, most at 1.35 × typical. 15 are never booked before their window ends: drivers view them 18 to 136 times each through the day, at the normal top fee and then at the urgent fees. 30 of the 130 orders due that Friday are late, of 35 late in the week. The control has the same night (26 drops, 14 of 103 orders late) and stays at 94.1% only because fewer orders are due that day. Over the ten weeks of `llsl`, 73 of 173 late orders follow a drop, and a gig dropped on the day of its last pickup is late 14–15% of the time against 3.6% when the last pickup is a later day.

`redrop=<minutes>` (`dispatch.fees.Fees`, off by default, `647ebfb`) answers this: a gig that its driver gives back on the day of the order's last pickup starts the urgent fees then (from `wake` o'clock with `night=true`), a step every `redrop` minutes, instead of waiting at the normal top for the deadline warning.

**The fee cannot buy that Friday back.** `redrop=60` was played with and without the slack rule on the 327f4ce flags:

| Label | Dev total | vs `vol-rd-ll+mk115+tb20+nosd@e9f4286` (€95,969) | Better on | Worst week | dev-10 |
|---|---|---|---|---|---|
| `nssl@815c5f4` (slack) | €107,825 | +€11,856 | 9/10 | 92.3% | €11,471, 92.3% |
| `nsslrd60@647ebfb` (slack + `redrop=60`) | €99,873 | +€3,904 | 7/10 | 91.4% | €8,292, 91.4% |
| `nsrd60@647ebfb` (`redrop=60`) | €91,023 | −€4,946 | 2/10 | 94.0% | €8,897, 94.0% |

With `redrop`, 27 of the 35 gigs dropped in dev-10's flu night are booked again (18 of 33 without it), at up to 2.5 × typical, yet 26 of the 129 orders due that Friday are still late (30 of 130 without it). Against `nssl` it loses on 10 of 10 weeks (−€7,952): on an ordinary day a dropped gig finds a driver at the normal fees, and the urgent fees only pay more for it. On the flu day the limit is drivers, not the fee. The late orders of that day (`.amp/in/lateorders.py`) are mostly short `same_day` cars whose gig came back between midnight and 13:00, found nobody until it expired an hour before the deadline, and was booked within minutes once posted again with a later window.

**Friday is the slack rule's exposed day.** (`.amp/in/slackdays.py`, `.amp/in/days.py`.) Under the slack rule the Friday is the fullest deadline day in all 10 dev weeks (100 to 143 orders due; in the control the next Monday is). 633 of the 1,654 slack orders are due on a Friday. A car that misses Friday waits the weekend. dev-10 is the one dev week whose flu falls on the Friday.

**6. `slack_friday=false`: the slack rule, but not for a deadline on the Friday.** (`dispatch.intake.ReachIntake`, branch `simple-slack`, `7d5afa2`; `bundles/slack-friday.patch`.)

| Label | Dev total | vs `vol-rd-ll+mk115+tb20+nosd@e9f4286` | Better on | Worst week | dev-10 | Orders |
|---|---|---|---|---|---|---|
| `nsslnf@7d5afa2` | €103,329 | +€7,360 | 6/10 | 94.2% (dev-10) | €12,298, 94.2% | 3,706 |
| `nssl@815c5f4` (plain slack) | €107,825 | +€11,856 | 9/10 | 92.3% (dev-10) | €11,471, 92.3% | 3,835 |

Every week is at 94.2% or above and ranked. Four weeks are €40 to €151 under the control. Friday falls to 33 to 67 orders due in nine weeks, under the control's, because the Tuesday to Thursday slack orders also replace next-day orders that were due a day later; dev-10's flu Friday goes from 128 due and 25 late to 104 due and 16 late. The switch costs €4,495 of plain slack's dev gain. It was prompted by dev-10, the one dev week with a Friday flu, so the holdout weeks decide between the two.

Two more variants passed dev on the same flags: `nsslfl8@af1f854` (`flu_drops=8`: Friday slack again once a night has shown 8 drops) €107,073, +€11,104, 9/10, worst 94.2%; `nsslnfpast@199d589` (`slack_friday=false past=1.0`, branch `simple-combo`) €104,846, +€8,877, 8/10, worst 95.0%. `nsslpast@647ebfb` (plain slack + `past=1.0`) made €109,421, +€13,452, but dev-10 is 92.1%.

**7. The slack rule fails on unseen weeks, for one reason: a flu day carries about 0.1 orders per driver.** The integrator combined finding 6 with the lanes quoter (`rg-nfl@7507a3c`); it passed dev, holdout (+€5,502, 7/10) and the orch seeds, and was pulled before any ranking run, because on the pricing thread's unseen weeks it is not ranked on t2-fresh-04 (88.5%), -06 (82.9%) and -07 (86.4%), where lanes alone (`lanes1@90a19a6`) has 96.7%, 82.6% and 92.2%. It is dev-10's failure on another weekday: in fresh-04 and -07 the flu falls on the Wednesday, 38 and 28 gigs come back in the night (lanes: 5 and 4), and the day holds 107 and 102 orders, 26 late each. A `same_day` car has one day to move, so when its driver stays at home only that day's drivers can save it.

Orders due on the flu day (the weekday with the most drops between 00:00 and 03:00), per driver of the world's list (`.amp/in/flucap.py <seed-prefix> <label>`; `.amp/in/fresh.py` shows one week):

| Week, label | Drivers | Due on the flu day | Per driver | Late that day | On time per driver |
|---|---|---|---|---|---|
| fresh-06, `lanes1@90a19a6` | 666 | 132 | 0.20 | 51 (39%) | 0.12 |
| fresh-06, `rg-nfl@7507a3c` | 666 | 122 | 0.18 | 48 (39%) | 0.11 |
| dev-10, `nssl@815c5f4` | 712 | 123 | 0.17 | 25 (20%) | 0.14 |
| fresh-04, `rg-nfl@7507a3c` | 678 | 107 | 0.16 | 26 (24%) | 0.12 |
| fresh-07, `rg-nfl@7507a3c` | 646 | 102 | 0.16 | 26 (25%) | 0.12 |
| dev-10, `nsslnf@7d5afa2` | 712 | 100 | 0.14 | 16 (16%) | 0.12 |
| dev-10, control | 712 | 101 | 0.14 | 13 (13%) | 0.12 |
| fresh-08, `lanes1@90a19a6` | 857 | 99 | 0.12 | 19 (19%) | 0.09 |
| fresh-04, `lanes1@90a19a6` | 678 | 83 | 0.12 | 7 (8%) | 0.11 |
| dev-04, `nssl@815c5f4` | 651 | 76 | 0.12 | 9 (12%) | 0.10 |

Over 70 weeks of five labels (`.amp/in/flusum.py`: `lanes1@90a19a6` and `rg-nfl@7507a3c` on t2-fresh, the control, `nssl@815c5f4` and `nsslnf@7d5afa2` on dev), by orders due per driver on the flu day:

| Due per driver | Flu days | Late that day | Median | 13% or more late |
|---|---|---|---|---|
| under 0.08 | 37 | 0 to 21% | 2% | 2 |
| 0.08 to 0.12 | 21 | 2 to 19% | 5% | 2 |
| 0.12 to 0.14 | 4 | 2 to 14% | 8% | 1 |
| 0.14 or more | 8 | 5 to 39% | 24% | 7 |

The one flu day at 0.14 or more that held is fresh-16 with lanes: 119 due for 772 drivers (0.15), 6 late, with 9 drops in the night. No flu day delivered more than 0.146 orders per driver on time; other weekdays deliver up to 0.195 (dev-04's Friday in `nssl`: 131 due for 651 drivers, 4 late). The count per driver is not the whole story: fresh-08's flu Friday is 19 to 21% late at 0.07 to 0.12 due per driver, so the drivers' list does not tell a week's real room. The flu day here is the weekday with the most drops between 00:00 and 03:00, which is a guess in weeks where no night stands out.

**Caps per driver do not save the slack rule.** `sldc12sc6@58aee9b` (branch `simple-cap`: the t3 thread's `day_cap=0.12` with the slack rule and a new `same_day_cap=0.06`, at most 0.06 `same_day` orders per driver on one deadline day; no lanes) is ranked on fresh-04 (€11,870, 93.4%) and fresh-07 (€9,705, 91.1%) but not on fresh-08 (€6,501, 86.2%; `dc12@42fa639` without slack €6,814, 90.5%) or fresh-06 (€7,633, 89.7%; `dc12@42fa639` €8,407, 91.3%). Four weeks: €35,709, ranked 2 of 4. The slack rule is out.

**The simple bot after the Saturday round** (t3, 14 November):

| Label | Weeks | Result | Against |
|---|---|---|---|
| `simple-plain-r4@647ebfb` | t2-fresh-11..20 | €106,003, ranked 10/10, worst 93.8% (fresh-16) | `lanes1@90a19a6` €114,241: −€8,239, better on 2/10 |
| `simple-plain-r4@647ebfb` | t2-fresh-01..20 | €205,492, ranked 19/20 | `lanes1@90a19a6` €216,349 (19/20): −€10,858, 6/20. `ltd3h8cr@95326e6` (the Sunday build) €225,840 (20/20): −€20,349, 3/20 |
| `simple-load12@b24aa99` (`load=0.12`) | fresh-06, -07, -08 | €9,475 at 87.9% (not ranked), €10,110 at 90.1%, €11,306 at 90.2%: €30,891 | no load rule: €9,973 at 85.5% (not ranked), €10,647 at 93.8%, €11,306 at 90.2%: €31,926 |
| `simple-load10@b24aa99` (`load=0.10`) | fresh-06, -07, -08 | €9,000 at 90.8%, €10,592 at 93.6%, €10,965 at 89.9% (not ranked): €30,556 | `ltd3h8cr@95326e6`: €10,515 at 92.2%, €11,267 at 94.4%, €11,382 at 92.1% |
| `simple-long@f33590c` (`long_drive=600`, branch `simple-long`, 104 lines) | dev-01..10 | €104,819, ranked 10/10, worst 92.0% (dev-02) | `simple-plain-r4@647ebfb` €98,858: +€5,961, 7/10. `lanes1@90a19a6` €98,847: +€5,972. `ltd3h8cr@95326e6` €106,041: −€1,222, 3/10 |

- **The load rule failed.** At 0.12 it does not rank fresh-06 and costs fresh-07 3.7 points of on-time share. At 0.10 it ranks fresh-06 (90.8%) and pushes fresh-08 to 89.9%, a week it does not even bind on by its own count (857 drivers): fewer orders on the Friday there moved other orders, not the late ones. No value ranks all three weeks, and both cost margin. A cap per driver of the world does not read a week's real room, as finding 7 said of the slack rule.
- **The long-lane rule works on dev**: a leg of 300 to 600 road minutes, quoted at 1.25 x the price on options two days away and kept out of the markup's learning, adds €5,961. It closes the simple bot's gap to the frozen lanes build on dev and leaves it €1,222 behind the Sunday build, with dev-02 at 92.0%. It was not played on fresh, holdout or orch: the work moved to the Sunday build (branch `sunday-long`, where the same 48-hour reading became `reach_notice`).

## The Sunday build (14 November, from 12:00)

The integrator moved this thread from the simple bot to the Sunday build: branch `sunday-ltd3h8` at `3a2dce2`, control
`ltd3h8cr@95326e6` (dev €106,041, t2-study €229,076, t2-fresh €225,840). The top teams make about €14,000 a week on about
400 orders; the control makes about €11,300 on about 340. All offline numbers below are from the control's 70 saved weeks
(dev, t2-study, t2-fresh, holdout, orch) unless a line says otherwise. The scripts are in
`/var/lib/amp-runner/src/bahn-simple/.amp/in/`.

**S1. Long lanes (300 to 600 road minutes) are late only on short notice** (`long.py`). 872 orders, 13% of quotes won,
1.83 x list, €120 an order, 6.4% late. By hours from the answer to the deadline: under 30 h 22 orders, 18% late; 30 to
48 h 101 orders, 21% late, €67 an order; 48 h or more 749 orders, about 4% late, €127 an order. The win rate is flat
across price bands (10 to 16%), so the price is about right. `long_notice=2880` (branch `sunday-long`) quotes a long lane
only on options 48 h away: a safety trade, not a gain (estimate −€137 a week for 0.36 fewer late orders). `sl-n48@7e7838a`
on dev-01..03: −€132, with dev-02 and dev-03 identical to the control.

**S2. With 48 hours of notice, an order is on time however few drivers live near its pickup** (`mix.py`, `FINE=1`).
One car, no private address: with 48 h or more to the deadline, late 0 to 3% in every band of drivers near the pickup;
under 48 h, late 7 to 13% unless 60 or more drivers live near. The control declines by driver count all the same:
24 plain requests a week with under 3 drivers near, 21 on a thin lane, 23 long lanes with under 6 qualified drivers
(`replay.py`, which reproduces all 72,503 saved quotes and names the gate that declined each request).
`reach_notice=2880` (branch `sunday-long`, `dispatch/intake.py`) lets an option other than `same_day` with 48 h or more
to its deadline pass those three gates; `reach_long=true` includes the long lanes' gate. Replayed on dev it quotes 66
more requests a week. The lateness with 0 to 2 drivers near is extrapolated from 11 orders.

| Label | Weeks | Margin | Against `ltd3h8cr@95326e6` | Worst week | Late |
|---|---|---|---|---|---|
| `sl-rn48@2ad92ae` (`reach_notice=2880`, played on orch) | dev | €111,519 | +€5,478, 8/10 | 97.0% | 77 |
| `sl-rn48l@2ad92ae` (and `reach_long=true`) | dev | €113,545 | +€7,504, 9/10; +€2,026 on `sl-rn48`, 6/10 with 3 the same | 96.0% (dev-04) | 86 |
| `sl-rn48@2ad92ae` | holdout | | +€1,886 (the integrator) | | |
| `sl-rn48@2ad92ae` | orch, 8 weeks | | +€53 a week | | |
| `sl-rn48@2ad92ae` | t2-fresh-06 | €9,989 at 91.8% | −€526; the control is at 92.2% | | |

Under `sl-rn48l`, 61 orders in 6 dev weeks came from pickups with 0 to 2 drivers near, with 48 h of notice: none late,
€35 an order. **The gain is real per order and small per week** (`shrink.py`): an order that the control declined
nets about €32 on dev, holdout and orch alike, but dev has 23.6 of them a week (+€761), holdout 13.4 (+€436) and orch 8.8
(+€279), because dev weeks have more requests from pickups with under 3 drivers near (the rule newly quotes 53 requests
a week on dev, 33 on holdout, 22 on orch). Against that the new orders cost the old ones €150 to €250 a week in swapped
wins and dearer drivers. So the rule is worth +€50 to +€550 a week by how thin the week's map is. The integrator stopped
its fresh weeks after t2-fresh-08.

**S3. Rich weeks are rich on the dealers' side** (`rich.py`). The richest third of weeks wins 48% of quotes at
1.54 x list (€14,357 a week); the poorest third 34% at 1.38 (€8,465). The declines for driver counts are the same in
both (about 75 a week). So there is no rich-week intake to open beyond S2.

**S4. A private pickup on the day of the request loses money; every other private address is fine** (`priv.py`,
`privfee.py`, `privtoday.py`).

| Class (one car) | Orders a week | Fee paid / typical | Deadline warning | Slot missed | Late | Net an order |
|---|---|---|---|---|---|---|
| Plain | 322 | 1.01 | 2% | | 2.1% | €33.7 |
| Private delivery | 4.9 | 1.06 | | | 3.2% | €33.2 |
| Private pickup, slot on a later day | 10.3 | 1.08 | 15% | 5% | 0.1% | €25.1 |
| Private pickup, slot today | 9.6 | 1.54 | 80% | 38% | 10.5% | −€1.9 |
| of which slot from 15:00 | 4.9 | 1.72 | 87% | 50% | 19.0% | −€10.1 |

The slot starts under two hours after the win in 609 of the 674 orders and lasts three hours, so the gig gets its
deadline warning at once and goes at the urgent fees. `private_today=false` (branch `sunday-priv`, `72f6e0d`,
`dispatch/intake.py`, one test) declines them: 28.5 requests a week on dev. Expected: about one late order a week
fewer and a few tens of euros. Trade-ins are late 34% of the time (125 orders) and still earn €83 an order.

**S5. Pairs of orders for one gig** (`chains.py`, 30 weeks of dev and t2-fresh, 345 single-car orders a week). The fee
thread has the mechanism (`Desk.pair`, `8a1868c` in bahn-t3v), so nothing was built here. A pair is two won orders, both
without a driver when the later is won, one delivery within 30 km of the other pickup, windows that fit with under two
hours of waiting, at most 12 hours of driving. 90.9 pairs a week exist; the same driver took both cars in 2% of them,
and the orders were paid 1.12 x typical apart. A return to within 30 km of the first pickup with both drives of 60
minutes or more, the fee thread's back-haul, is 1.1 pairs a week; with one short drive 8.9. Pairs in which one driver
saves half or more of the two trips home, both drives 60 minutes or more: 10.9 a week, typical fees €150 a pair. Saving
20 to 50%: 32 a week. Under 20% (onward): 35 a week. What a driver accepts for a pair is in no saved week.
The fee thread widened its rule with these counts (`pair_save`, `db36887`) and plays `pairw50` and `pairw20`.

**S6. A trade-in is late because nothing tells the driver the customer's hour** (`trade.py`). 125 trade-ins in 70
weeks, 34% late, €83 an order (1.70 x list, 0.67 typical fees for the two cars). 93% were booked an hour or more before
the customer's hour, on average 11 hours after the win, so they are not late for want of a driver. The order's deadline
is the old car's (20:00), the new car's is the end of the customer's hour plus 30 minutes, and the desk posts the
delivery stop without a window, so the world lets a driver plan it up to 20:00: 49 of 143 new cars arrived 90 minutes or
more after the hour began (35 of them 3 hours or more). A single private delivery has its hour as its own deadline and
is on time 94% (378 of 401). With `trade_ins=true` (`vol-sun-trade@77ac4f8`, dev) the desk takes 49 trade-ins in 10
weeks and 37% are late. `trade_hour=true` (branch `sunday-trade`, `9935a3d`, `dispatch/notes.py` and one line in
`policies/reach.py`, one test) gives that delivery stop the customer's hour as its window while the hour has not
passed. Queued: `sl-tt@9935a3d` (Sunday flags + `trade_ins=true trade_hour=true`) on dev.

**S7. Drivers do not learn to wait for our raises** (`holdout.py`, 30 weeks, 11,320 first bookings on the normal
schedule). 49% book at the opening fee on their first view; 33% first see the gig after raises and book at once, at 1.16 x
typical; 18% saw a lower fee first (0.92) and booked after a raise (1.12), 6.8 hours later. That last share is the
same on every day of the week (20% on Monday, 19% on Friday), so the rule that drivers expect a gig to rise as far as
they have seen ours rise does not grow into more waiting. A flat fee or a new gig for each raise has nothing to gain there.

**S8. The cheap driver lives near the delivery, and the app does not tell them** (`accept.py`, 30 weeks, first views of
single-car gigs before any deadline warning).

| The viewer's home | First views at the opening fee | Booked at once | At 1.05 x typical | At 1.35 or more |
|---|---|---|---|---|
| Within 30 km of the delivery | 20,697 | 13.9% | 4.7% | 6.2% |
| Within 30 km of the pickup | 53,228 | 2.8% | 1.4% | 3.6% |
| Within 100 km of either | 24,724 | 2.5% | 1.2% | 2.3% |
| Farther | 19,200 | 2.0% | 0.8% | 0.9% |

A notification goes to drivers within 30 km of the pickup; the driver whom the car takes home finds the gig only by
browsing. Earlier offers (ours and the fee thread's) went to our own drivers after a delivery and were declined or not
read. `homeward=0.85` (branch `sunday-offer`, `7625b93`, new `dispatch/homeward.py`, three lines in
`policies/reach.py`, one test) offers each new single-car gig at 0.85 x typical to drivers who live within 30 km of
its delivery, those seen in the app that day first: three offers every eleven minutes, six rounds, 07:00 to 21:00.
Queued as a probe: `sl-hw85@7625b93` on dev-01 and dev-02, to read how many offers are accepted.

**S9. A gig that starts tomorrow books at once; a gig that can start now waits and costs more** (`posthour.py`,
`bookday.py`, `startday.py`; plain single-car orders whose last pickup is after the day of the post).

| The gig's pickup | Orders | First driver after | Fee of the first booking | At the opening fee | At 1.3 or more | Late |
|---|---|---|---|---|---|---|
| Can start at once | 9,716 | 7.1 h | 1.06 x typical | 38% | 19% | 2.7% |
| The order's window starts on a later day | 12,390 | 1.7 h | 0.91 | 72% | 3% | 1.2% |
| Ready at once, but the note moved the pickup to a later day | 85 | 0.5 h | 0.88 | 86% | 0% | 0.0% |

The third row is the same kind of order as the first with tomorrow's kind of gig, and it books like the second. By
the hour of the post, a car that is ready now books at 0.98 before 10:00, 1.06 from 10 to 13 and 1.12 from 13 to 16.
A driver who works today plans tomorrow from home, with a ticket bought ahead; a gig for now has to fit the day they
are in. The quoter's `DETAIL` already knew that a car ready on a later day costs 0.16 typical fees less, but only as a
cost, not as something the desk can choose. `ahead_from=10` (branch `sunday-ahead`, `2bba163`, `dispatch/notes.py` and
one line in `policies/reach.py`, one test) posts a single car that is ready now, from 10 o'clock on, with a pickup
window from midnight, when its last pickup leaves four hours of tomorrow's opening hours at the pickup site. About 110
orders a week qualify. What the saved weeks cannot show: tomorrow's drivers getting crowded by the cars moved to them.
The pricing track's slot played it: **`sl-ah10@2bba163` on dev: +€7,131, 9/10, worst week 95.2%** (the integrator's
count; holdout, orch and fresh follow there). On its first 7 dev weeks (`shrink.py`, `startday.py`) the whole gain is on
the orders that both builds won: the same 339 orders a week cost 0.99 typical fees instead of 1.03, +€640 a week, and
the swapped orders add €25. The 636 moved orders got their first driver after 1.5 h at 0.92 typical fees, 68% at the
opening fee, where the control's same class waited 7.6 h and paid 1.07; 2.5% of them were late against 2.8%.
`sl-wkah@2a96163` (branch `sunday-combo`: 3a2dce2 + the fee track's 9ae9be1 and cda2f14 + 2bba163; Sunday flags with
`long_markup=1.05 weekend=true ahead_from=10`) asks whether `weekend` and `ahead_from` add: both cut Friday's fees.
Cherry-picking cda2f14 alone conflicts in `dispatch/fees.py` with 9ae9be1 (`home_offer`), so the branch carries both.

**A fault in ahead_from, and its guard** (`aheadnote.py`, `aheadfix.py`). In `sl-ah10`'s 10 dev weeks the rule moved 5
cars whose note wanted them delivered before the next noon, and all 5 were late: the world's `lastPickupAt` does not know
a note's deadline. `74cc5a7` (branch `sunday-ahead`) leaves a car for today when the reader's latest delivery minus the
drive leaves under four hours of tomorrow's opening hours. Replayed on those weeks it leaves 9 of 1,042 moved orders
alone, 7 of them late, and moves the other 1,033. `sunday-combo` carries it as `f7ebca4` (label `sl-wkah@f7ebca4`).

**S10. A dropped gig comes back at the top of its climb** (`drops.py`, `drops2.py`). 47 single-car gigs a week (14% of
orders) lose their driver. The desk does nothing, so the gig is in the app again where its schedule stands, at 1.25
typical fees on average and at the top in 56% of drops, and the app tells the drivers near the pickup again at that fee.
The next driver takes 1.26 where the first took 1.01: €648 a week. A low fee does not cause the drops: 11.7% of bookings
at the opening fee are dropped, 12.4% at 0.9 to 1.1, 9.9% at 1.3 or more. 17 of the 47 are dropped between midnight and
06:00, when a driver plans the next day.

| The drop comes | Drops a week | Fee before | Fee after | More paid a week | Late |
|---|---|---|---|---|---|
| 24 h or more before the last pickup | 22.7 | 0.96 | 1.20 | €331 | 0.8% |
| 8 to 24 h before | 21.5 | 1.06 | 1.30 | €257 | 3.9% |
| 3 to 8 h before | 1.8 | 1.07 | 1.40 | €25 | 8.6% |
| Under 3 h before, or after | 1.7 | 1.41 | 1.93 | €35 | 41.0% |

The next driver takes what the app shows, and a low fee finds one as fast (`drops3.py`, rebookings before any deadline
warning). With 24 hours or more to the last pickup: a gig that came back at 0.93 typical fees went at 0.95, 92% within
the hour, 0.5% late (5.4 a week); one that came back at 1.34 went at 1.34, 75% within the hour, 0.5% late (13.2 a
week). With 8 to 24 hours: back at 0.92, gone at 1.00 after 4.5 h, none late (2.2 a week); back at 1.34, gone at 1.34
after 4.5 h, 1.7% late (14.5 a week). With ahead_from the drops cost more, €839 a week on `sl-ah10`'s dev weeks.

`drop_restart=24` (branch `sunday-drop`, `909fb25`, on cda2f14; `dispatch/fees.py`, one test) starts the normal
schedule again for a gig dropped 24 hours or more before its order's last pickup, unless the deadline warning has come.
The earlier `redrop` (urgent fees at once for a drop on the last day) went the other way and lost.

Played on the 10 dev weeks with the Sunday flags, against `ltd3h8cr@95326e6` (€106,041):

| Label | Rule | Margin | On control | Better | Worst week | Orders | Rebooked drops cost a week | Late after a drop 8-24 h before |
|---|---|---|---|---|---|---|---|---|
| `sl-dr24@909fb25` | `drop_restart=24` | €108,429 | **+€2,388** | 8/10 | 97.0% | 3,412 | €441 (control €702) | 5.2% (control 4.0%) |
| `sl-dr8@909fb25` | `drop_restart=8` | €107,942 | +€1,900 | 8/10 | 94.2% (dev-01) | 3,408 | €274 | 6.6% |

The 24-hour rule keeps what it should: after an early drop the next driver takes 1.01 typical fees instead of 1.19, 5.5
hours after the drop instead of 2.1, and 0.9% of those orders are late (0.8%). The 8-hour rule saves more fees and earns
less: a gig dropped 8 to 24 hours before its last pickup waits 7.2 hours instead of 5.1, 0.3 a week are never rebooked
(0.1), and dev-01 falls from 96.6% to 94.2% on time. `drop_restart=24` on the combination (S11) is
`sl-wkahdr24@04accd7`, branch `sunday-combo-drop`.

**S11. The parts add: weekend fees, ahead_from and cheaper long lanes together** (`sl-wkah@f7ebca4`, branch
`sunday-combo`: 3a2dce2 + the fee thread's `weekend` (cda2f14) + `ahead_from` (2bba163, 74cc5a7); the Sunday flags with
`long_markup=1.05 weekend=true ahead_from=10`). Frozen by the integrator as aeb03ea.

| Weeks | Margin | On `ltd3h8cr@95326e6` | Better | Ranked | Worst week | Played by |
|---|---|---|---|---|---|---|
| dev-01..10 | €117,203 | **+€11,161** | 10/10 | 10/10 | 95.9% (dev-07) | this thread, t3 |
| t2-fresh-01..20 | €247,113 | **+€21,273** | 17/20 | 20/20 | 91.0% (fresh-08) | t3 (06-08), t4 (the rest) |
| holdout | | +€10,594 | 9/10 | | | the integrator |
| orch-01..10 | €126,644 | +€12,586 | 10/10 | 10/10 | 93.4% (orch-08) | the integrator |

`ahead_from` alone (`sl-ah10@2bba163`) is +€7,131 on dev (9/10) and +€13,069 on fresh (18/20, worst 90.9%); the
combination adds €4,031 to it on dev (8/10) and €8,204 on fresh. Over the first 8 fresh weeks the three parts alone sum
to +€1,832 and the combination is +€2,240, so they neither overlap nor fight.

ahead_from's moved cars are not the late ones (`aheadday.py`, 30 dev and fresh weeks, the 105 moved orders a week that
the control also won): late 3.2% in the control and 2.4% moved, at 0.98 typical fees instead of 1.10, €707 a week. A
car moved from a Friday saves the most (37 a week, 1.13 to 0.98).

**S12. Cheap long lanes earn in ordinary weeks and lose in crowded ones** (`longfee.py`, `longcrowd.py`, `feeread.py`,
`longday.py`). Margin and on-time share on the three crowded fresh weeks:

| Label | fresh-06 | fresh-07 | fresh-08 | Sum | On control |
|---|---|---|---|---|---|
| `ltd3h8cr@95326e6` | €10,515, 92.2% | €11,267, 94.4% | €11,382, 92.1% | €33,164 | |
| `wk@cda2f14` (weekend) | €10,571, 92.2% | €11,593, 94.4% | €11,282, 91.1% | €33,446 | +€282 |
| `vol-sun-lm105@3c1eb0c` (long_markup 1.05) | €9,713, 91.6% | €9,580, 94.3% | €7,970, 90.4% | €27,262 | −€5,902 |
| `sl-ah10@2bba163` | €9,710, 90.9% | €13,445, 96.7% | €13,018, 93.0% | €36,172 | +€3,008 |
| `sl-wka@f7ebca4` (weekend + ahead_from, long_markup 1.15) | €9,707, 90.1% | €13,856, 95.9% | €11,792, 91.8% | €35,355 | +€2,191 |
| `sl-wkah@f7ebca4` (the same + long_markup 1.05) | €9,518, 91.2% | €12,311, 94.8% | €9,702, 91.0% | €31,532 | −€1,632 |

long_markup=1.05 alone is −€4,990 over fresh-01..08 and +€10,856 over fresh-09..20. The integrator kept it: it gains on
holdout and orch, and the floor is the same with and without it (91.0% and 90.1%, on different weeks).

Long orders (a drive over 300 minutes) over 30 dev and fresh weeks: at 1.05 the desk wins 23.4 a week at €81 net each,
10.3% late (2.4 a week); at 1.15, 11.6 a week at €115 each, 8.0% late (0.9 a week). So the cheap lanes earn €573 a
week directly and add 1.5 late orders a week. No reading by Wednesday night marks a crowded week: fees booked so far
over typical, drops per booking and deadline warnings per order all overlap with ordinary weeks (`feeread.py`). What
does track a long order's lateness is what drivers cost in the 24 hours before it was won (`sl-wkah@f7ebca4`, single-car
bookings, ten or more):

| Fees of the last 24 h over typical | Long orders a week | Net an order | Late | The three crowded weeks: a week | Net an order | Late |
|---|---|---|---|---|---|---|
| under 0.95 | 9.4 | €97 | 5.3% | 4.0 | €72 | 16.7% |
| 0.95 to 1.00 | 5.3 | €84 | 8.2% | 6.7 | €41 | 10.0% |
| 1.00 to 1.03 | 3.1 | €92 | 12.0% | 4.7 | €86 | 7.1% |
| 1.03 to 1.06 | 2.6 | €52 | 26.9% | 11.3 | −€7 | 41.2% |
| 1.06 to 1.10 | 1.8 | €69 | 12.7% | 4.0 | €54 | 16.7% |
| 1.10 or more | 0.2 | €40 | 33.3% | 0 | | |

Other orders do not show it (1.4% to 3.8% late in every class). With ahead_from the fees run lower, so a threshold of
1.10, read from the build without it, would stop 0.2 orders a week; 1.03 stops 4.6 a week (€270 a week, 1.0 late order
a week) and 15.3 a week in the crowded weeks (€144 a week, 5.3 late orders a week). `long_fees=<x>` (branch
`sunday-brake`, 928f4bc, on aeb03ea; 19 lines in `dispatch/intake.py`, the volume thread's part, one test) takes no long
lane while those bookings went above x typical fees. Playing: `sl-lf103@928f4bc` and `sl-lf100@928f4bc` on fresh-06/07/08.

## What failed

- **Warm direct offers** (`chain=true`, `dispatch/chain.py`). In `simple-t45`, 2,958 of 3,271 orders had one of our drivers ending a gig near the pickup in time, yet the same driver did both only 70 times. `ChainFees` offers an open gig to a driver of ours who ends within 20 km of its pickup, at 0.8 × typical, when they book, when they deliver, and when the gig is posted. `dn19ch80@5fd681f` €79,879 against `dn19@2c73800` €79,624: +€255, noise. Of 5,254 offers 52 were accepted, 2,033 declined and 3,169 expired unread. A driver who reads an offer wants more than 0.8 × typical; most do not read it. Cold offers failed the same way in the fees track (9 of 1,635).
- **`ramp` as a cure for the slack rule's lateness**: see finding 3.
- `simple-t50@1cb3c0c` and `dc2sl@8b26548` failed every week on the team's world limit (a stray world held a slot). They were dropped, not replayed.
- **The slack rule on unseen weeks**, with or without Friday, the flu switch or caps per driver: see finding 7.
- **`redrop=60`** (urgent fees at once for a gig dropped on the day of its last pickup): −€4,946 alone, −€7,952 on top of the slack rule, and dev-10 gets worse. See finding 5.
- **The slack rule only after the flu night is seen.** Not built. In `nssl` the flu night shows as 9 to 32 drops between 00:00 and 03:00, but those are mostly the slack orders' own gigs: in the control, 7 of the 10 weeks show at most 5 drops in any weekday night (`.amp/in/nights.py`), so a desk that waits for the flu cannot see it. An offline split (`.amp/in/afterflu.py`) also puts only 48% of the slack orders' net after the burst night.
- **A cap on the slack rule by the day's book** (`.amp/in/cap.py`, offline): cutting 502 slack orders (about −€15,000) still leaves dev-10 at 92.5%. Not built. The estimate removes orders and their own lateness only; it cannot see the room they would leave for other orders.
- **`reach_notice=2880`** (`sl-rn48@2ad92ae`, an option with 48 hours or more to its deadline passes the reach gates, S2): dev +€5,478 (8/10), holdout +€1,886, orch-01..10 +€100 (5/10). It shrank out of sample and was dropped.
- **`load=0.12` and `load=0.10` on the simple bot**: no value ranks t2-fresh-06, -07 and -08 together. See finding 1.
