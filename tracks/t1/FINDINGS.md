# Track 1: Intake and on-time

**Question.** How many cars, and which, can the drivers of a level 8 week move on time?

## Findings

All runs: level 8, the 10 dev seeds, practice worlds on the test team's key, code `32d79b0` (policy `reach`).
`reach` declines requests whose leg drives over 300 road minutes or whose pickup has fewer than 3 drivers
living within 60 km, leaves out `same_day`, and quotes every other option at list × markup.

| Label | Weeks | Margin | Orders | On time (all / worst week) | Ranked | What it shows |
|---|---|---|---|---|---|---|
| `reach@32d79b0` (markup 1.5, fees open 1.0 ×) | 10 | €49,761 | 2,343 | 97.4% / 95.0% | 10/10 | The baseline: car choice alone keeps every week above 90% |
| `reach-m1.4@32d79b0` | 10 | €37,612 | 3,075 | 96.3% / 94.0% | 10/10 | −€12,149; better on 2 of 10. More orders, less margin each |
| `reach-m1.6@32d79b0` | 10 | €46,578 | 1,583 | 97.2% / 95.6% | 10/10 | −€3,183; better on 3 of 10. A third fewer orders |
| `reach-open0.85@32d79b0` (markup 1.5, fees open 0.85 ×) | 10 | **€63,783** | 2,292 | 96.6% / 94.1% | 10/10 | **+€14,022 (+28%); better on 10 of 10** |

The same `reach` weeks on the main team's key gave the same numbers to the cent: a seed plays the same week on any key.

### Opening fee, played on ankka (code `5827f42`, same policy code as `32d79b0`)

`reach-open0.85@5827f42` reproduced the orb's `reach-open0.85@32d79b0` rows byte for byte.

| Opening fee | Dev total (10) | vs 0.85 | Better on | Dev worst week | Holdout total (10) | vs 0.85 | Holdout worst week | Ranked |
|---|---|---|---|---|---|---|---|---|
| 1.0 × (`reach`) | €49,761 | −€14,022 | | 95.0% | €50,969 | −€10,574 | 95.8% | 20/20 |
| **0.85 ×** | **€63,783** | | | **94.1%** | **€61,543** | | **95.3%** | **20/20** |
| 0.75 × | €65,345 | +€1,562 | 5 of 10 | 94.5% | not run | | | 10/10 |
| 0.7 × | €67,621 | +€3,839 | 7 of 10 | 93.3% | €63,477 | +€1,934 (7 of 10) | 93.9% | 20/20 |

**Decision: keep 0.85 ×.** 0.7 × adds about €190 to €380 a week (3–6%), but its worst week drops by 0.8 points on dev and 1.4 points on holdout. The final is one week and a week under 90% scores nothing, so the cushion is worth more than the margin. Revisit 0.7 × once an on-time controller (late budget or λ) can protect it.

Across the 20 weeks of each label, 26–92 actions were refused: mostly withdraws of gigs that were no longer open, plus 1–5 posts whose window had already ended. They cost nothing, but they point at a desk bookkeeping gap.

## Switches of e7bf4da (dev on 7 slots, holdout on orch; every label adds `open=0.85`)

`ctl@e7bf4da` (no switch) matches `reach-open0.85@0ce6b0a` row for row on dev, so the switches are off by default.

| Variant | Dev total | vs ctl | Better on | Dev worst week | Late orders | Holdout total | vs 0ce6b0a | Holdout worst week |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ctl | €63,285 | | | 94.1% | 77 | (€61,837) | | (94.4%) |
| **`future_same_day=true`** | **€69,264** | **+€5,979** | **7 of 10** | **94.0%** | 100 | **€66,153** | **+€4,315, 6 of 10** | **95.5%** |
| + `late_budget=0.05` | €67,362 | +€4,077 | 7 of 10 | 94.0% | 92 | €66,153 (row for row = fr) | +€4,315 | 95.5% |
| + `late_budget=0.04` | €67,154 | +€3,869 | 7 of 10 | 94.9% | 91 | not run | | |
| `late_budget=0.05` | €62,858 | −€427 | 0 of 10 | 94.1% | 79 | not run | | |
| `density=true` | €62,275 | −€1,010 | 3 of 10 | 92.9% | 115 | not run | | |
| `density=true dense=10` | €60,500 | −€2,785 | 2 of 10 | 89.7%, 9/10 ranked | 150 | not run | | |
| all three, `late_budget=0.05` | €68,216 | +€4,931 | 8 of 10 | 91.9% | 123 | not run | | |

**Decision: freeze `future_same_day=true` for ranking runs.** The late budget never binds on holdout (late share near 3%) and costs €1,902 on dev; the density fees lose margin and on-time share at level 8.

## Volume: the classes `reach` declines, each with a brake (on fr, `base@f5a6b3b`)

Every label adds `open=0.85 future_same_day=true`; the control is `base@f5a6b3b`, €69,264, worst week 94.0%.
Scripts in `.amp/in/scripts` of the runner (`declined.py`, `ordermargin.py`, `laterate*.py`) read the saved weeks.

**What reach declines.** Not batches, notes or private addresses as classes: only legs over 300 minutes (138 requests a
week, about €24k list), pickups with fewer than 3 drivers near (50, €4.5k) and same_day on a car ready today (79, €5.2k).
**What the quoted classes earn.** Private-address orders: 24 a week, €0 margin, 3.0 late. Trade-ins: 3.3 a week, €143,
1.5 late. Together 4.5 of the 10 late orders a week, and each late order halves its dealer's trust count.

| Variant | Dev total | vs base | Better on | Worst week | What it shows |
| --- | --- | --- | --- | --- | --- |
| `private_slots` | €70,907 | +€1,642 | 7 of 10 | 93.3% | Private requests reach declines, quoted only through the gate. Holdout €68,147, +€1,994, worst 95.0% |
| `trade_ins` | €69,497 | +€233 | 4 of 10 | 93.3% | Noise |
| `noted_slots` | €69,738 | +€473 | 5 of 10 | 91.3% | Fails the 93% line |
| `batch_slots` | €68,429 | −€836 | 3 of 10 | 92.7% | |
| `long_lanes` | €68,096 | −€1,168 | 4 of 10 | 89.2%, 9/10 ranked | Long gigs pull drivers off short lanes (`max_drive=360`: long orders +€564 a week, short ones −€603) |
| `no_private no_trade_ins` | €70,012 | +€748 | 3 of 10 | 95.3% | On time 97.8% against 96.0% with 10% fewer orders |
| `no_private no_trade_ins private_slots` | €73,345 | +€4,081 | 8 of 10 | 92.9% | Private only through the gate |
| + `thin_drivers=20 thin_both` | €72,354 | +€3,089 | 7 of 10 | 94.7% | Few drivers near both ends: three days only. dev-10 92.9% → 95.1% |
| + `near_km=80` | €75,806 | +€6,542 | 9 of 10 | 93.1% | |
| + `min_drivers=2` | €73,982 | +€4,718 | 9 of 10 | 91.3% | |
| + `open=0.7` | €78,100 | +€8,836 | 10 of 10 | 92.0% | dev-10 fails 93% |
| `thin_drivers=20` (long legs from thin pickups) | €65,502 | −€3,762 | | 97.5% | Those legs earn €38 an order: too dear a brake |

### On the dial quoter with night fees (e113e30; control `dn19@2c73800`, €79,624, worst week 94.0%)

The dial wins about 350 orders a week, so drivers are nearer their limit and lateness binds sooner. It prices private
addresses at a profit (€286 a week), so `no_private` and `private_slots` stop paying. Its cost model makes long lanes pay.

| Variant | Dev total | vs dn19 | Better on | Worst week | What it shows |
| --- | --- | --- | --- | --- | --- |
| `private_slots` | €78,335 | −€1,289 | 5 of 10 | 91.1% | |
| `thin_drivers=20 thin_both` | €80,128 | +€504 | 5 of 10 | 93.0% | |
| + `near_km=80` | €83,007 | +€3,383 | 7 of 10 | 92.9% | |
| `max_drive=360` | €79,967 | +€343 | | 94.0% | |
| `long_lanes` (gate, up to 600 min) | €82,091 | +€2,467 | 7 of 10 | 90.6% | Over 420 min loses money; short lanes get later |
| + `long_max=420` | €86,242 | +€6,618 | 9 of 10 | 90.7% | |
| + `long_markup=1.15` | €87,066 | +€7,442 | 9 of 10 | 90.7% | 1.15 × the dial's price, set in the intake: the dial does not learn from these |
| + `long_markup=1.25` | €85,001 | +€5,377 | 10 of 10 | 92.2% | |
| **`long_lanes long_markup=1.15 thin_both thin_drivers=20`** (0da56fb) | **€90,496** | **+€10,872** | **8 of 10** | **94.1%** | Thin ends get three days only, long lanes too |
| + `long_same_day=false` | €87,796 | +€8,172 | 9 of 10 | 90.7% | |
| + `long_same_day=false expand_brake=0.04` | €87,483 | +€7,859 | 9 of 10 | 90.9% | |

dev-10 decides every variant: a Salo bulk order on Thursday and the Oulu lanes. Near-identical variants land between
90.7% and 94.1% there, so the margin gain is solid and the worst-week pass is thin. Holdout decides.

Holdout of `vol-dn-ll+mk115+tb20@0da56fb` (orchestrator): €101,468 against dn19's €86,962, +€14,506, 9 of 10, worst week 96.3%.

### With the note reader (7b87294; control `rd@bc3b064`, €85,983, worst week 94.3%), frozen at 67faf35

| Variant | Dev total | vs control | Better on | Worst week | Holdout |
| --- | --- | --- | --- | --- | --- |
| **`long_lanes long_markup=1.15 thin_both thin_drivers=20`** (e9f4286) | **€94,765** | **+€8,782** | **9 of 10** | **94.1%** | **€104,325 against €92,091, +€12,234, 10 of 10, worst 94.8%. Frozen** |
| **+ `long_same_day=false`** | **€95,969** | **+€9,986** | **8 of 10** | **95.2%** | **€105,811, +€13,720 on rd (+€1,486 on the above, 3 of 10), worst 97.2%. Frozen at 327f4ce** |

Against the frozen build (`vol-rd-ll+mk115+tb20@e9f4286`, €94,765):

| Variant | Dev total | vs frozen | Better on | Worst week | What it shows |
| --- | --- | --- | --- | --- | --- |
| `long_markup=1.1` | €96,139 | +€1,374 | 4 of 10 | 92.9% | 1.15 stays |
| `near_km=80` | €94,036 | −€729 | | 96.5% all | |
| `private_slots` | €95,485 | +€720 | 4 of 10 | 91.9% | |
| the gate reads notes with the reader (edc1eb4) | €96,172 | +€1,407 | 4 of 10 | 93.5% | The note filter was the gate's largest decline (26 long requests a week); reading them adds little |
| `min_drivers=2` | €93,759 | −€1,006 | | 97.1% all | |
| `long_max=720` | €94,765 | ±0 | | 94.1% | Identical to the cent: nothing over 600 minutes passes the gate |
| `expand_brake=0.1` | €94,765 | ±0 | | 94.1% | Identical to the cent: the 6% brake never binds |
| `thin_drivers=15` | €96,053 | +€1,288 | 3 of 10 | 92.5% | |
| `thin_drivers=15` with `long_same_day=false`, against the 327f4ce flags | €95,714 | −€255 | 2 of 10 | 93.9% | 20 stays |

Where long lanes stand in the frozen build: of about 138 long requests a week, the gate declines about 70 (a note,
26; fewer than 6 qualified drivers near the pickup, 23; a private address, 14); the rest are quoted at about 1.8 × list
and win 22% (300-420 min) or 15% (over 420). The 14 long orders a week earn €44 an order, 3.6% late.

### Long-lane pricing, thin pickups and on-time brakes (327f4ce flags; branches volume-long, volume-combo, volume-area)

Control: `vol-rd-ll+mk115+tb20+nosd@e9f4286` (€95,969, worst 95.2%), then the frozen gate `vol-lp-readgate@edc1eb4`
(€96,887, worst 94.4%; holdout €110,970, +€5,159 on the nosd freeze, worst 95.9%, frozen at 3ea3f7f).

| Variant | Dev vs control | Better on | Worst week | What it shows |
| --- | --- | --- | --- | --- |
| `long_dial` target 0.30, open 1.0 | −€1,050 | 5 of 10 | 93.4% | Long quotes fall to 1.65 × list and win 37%; long margin +€200 a week, short lanes −€390, private −€200 |
| + `long_drive=300 long_fee_step=0.15` | −€2,186 | | | A faster long-leg fee climb costs |
| `long_dial` target 0.22, open 1.15 | +€974 | 5 of 10 | 94.6% | Holdout €105,924 against €105,811: flat. The dev gain was noise |
| `thin_gate=3` (fewer than 6 qualified drivers, three days only) | ±0 | | | Only about 1 such long request a week offers within_3_days |
| `thin_gate=1 thin_days=false thin_markup=1.15` | +€58 | | | thin_both still holds them back: both ends are thin |
| `gate_drivers=4` | ±0 to the cent | | | The driver count is not the binding limit |
| `queue_div=2` | −€1,401 | | | |
| `late_budget=0.03` | −€1,564 | 0 of 10 | | t2-study-12 91.6% → 94.0% |
| the gate reads notes (edc1eb4) | +€918 | 7 of 10 | 94.4% | **Frozen** |
| readgate + `long_dial` 0.22 | +€2,991 on the frozen gate | 9 of 10 | 92.97% | t2-study-12 93.3% (frozen gate 92.2%) |
| + `late_budget` 0.04 / 0.05 | | | 92.9% | Worse: the whole-week brake keeps only dense southern lanes, the ones a flu day makes late |
| + `area_brake=20` | +€33 on the frozen gate | 6 of 10 | 94.6% | On time 97.4% against 96.8%; t2-study-12 93.9%. On orch |
| `area_brake` 10 / 20 on the frozen gate alone | −€2,511 / −€3,632 | 3 of 10 | 94.4% / 94.1% | |

**t2-study-12, the frozen build's worst unseen week (91.6%).** 30 of 33 late orders had the deadline warning with no
driver booked: short southern lanes (Hyvinkää, Vantaa, Espoo, Lempäälä) on Wednesday and Thursday, no drops, no no-shows.
The bulk order (Porvoo, Friday, 26 won) had none late. It reads as a flu day. `area_brake=k` gives the three-day option
only where the unbooked work near a pickup on its ready day reaches one driver-day per k drivers within 60 km.

**Long lanes are priced about right.** A cheaper long price wins more long cars but they take drivers from short lanes,
and a fixed 1.15 does as well as a learned level on holdout.

**Ruled out.** Same-day on a car ready today: in `sd@f5a6b3b` even short lanes from pickups with 20 or more drivers
within 30 km and 6 hours of slack were late 25% of the time, at €16 an order.

### Same-day slack with a brake, and the lanes combination (branches volume-slack, volume-lanes)

`same_day_slack=1440` (815c5f4) earns about +€11k on dev, but plain it plays t2-study-12 at 89.8% and dev-10 at 91.6%,
and on lanes it plays t2-fresh-04 at 89.8% and -08 at 87.0%. Its extra late orders are Friday short lanes.

| Label (control) | Dev | Worst week | Unseen weeks |
|---|---|---|---|
| `vol-sl+d22+ab20@2d00aba` (rg-sl@7caf8ff, €108,026) | −€30, 5 of 10 | 93.5% (dev-10; 91.6%) | study-12 92.5%. Holdout €121,224, +€10,254 on readgate, worst 95.6% |
| `vol-sl+ab10` / `+ab20` / `slack_load=20` / `slack_risk` 4, 8 / `slack_window=600` | −€466 to +€588 | 91.6–92.5% | |
| `vol-sl1800+ab10@be4a14a` | −€6,147 | 93.6% | |
| `vol-ln-nfl+d22+ab20@7488efd` (rg-nfl@7507a3c, €106,642), on ec29ab2 with lanes=1 and slack_friday=false | +€2,322, 6 of 10 | 95.6% (94.2%) | fresh-04 / 06 / 07 / 08: 90.8 / 84.2 / 90.4 / 92.8% (rg-nfl 88.5 / 82.9 / 86.4 / 90.3%); study-12 93.1% |

### The flu Friday (t2-fresh-06, dev-10) and caps per deadline day (branches volume-batchcap, volume-daycap2)

**It is the flu, not the bulk order.** Drops between 00:00 and 06:00: 21 on fresh-06's Friday and 28 on dev-10's, and 11 or fewer
on every other weekday (the handbook: drops at night are rare). All 52 late Friday orders of fresh-06 were won on
Wednesday or Thursday; 16 lost their booking at Friday 00:17–00:59, and the rest were never booked. Friday 06–18 had 35
bookings against 60–75 on other days, the gigs expired at 18:00 when pickup closed, and were booked 10–40 minutes later
for Saturday. The real bulk orders that week (Pori ×30, Porvoo ×25) were not late. Intake cannot react once the
flu shows, because the day's work is already sold, so a cap must act on what is due on a day before it comes.

On e33175a with lanes=1, against `rg-lanes1@90a19a6` (dev €98,847; fresh-04 / 06 / 07 / 08 at 96.6 / 82.6 / 92.1 / 90.1%):

| Switch | Dev | fresh-04 / 06 / 07 / 08 |
|---|---|---|
| `batch_cap=2` (cars of one batch due on one day) | −€4,474, 4 of 10 | 95.8 / 87.5 / – / 91.5% |
| `batch_cap=2 due_cap=12 due_min=20` | −€11,419, 1 of 10 | 95.2 / 91.8 / 93.8 / 92.7% |
| `batch_cap=3` | −€888 (9 weeks) | – / 84.3 / 92.4 / 91.3% |
| `due_cap` 5 / 8 / 20 (orders due per area per driver nearby) | +€55 / −€1,489 (9 weeks) / – | 84.6 / 88.6 / 89.7% on fresh-06 |
| `day_cap=0.12` (orders due on a working day per driver of the week, not the last Monday; 9297e41) | +€712, binds only on dev-10 (94.7%) | 96.7 / 88.1 / 92.2 / 90.2% |
| `day_cap=0.10` | **+€1,126**, binds only on dev-10 (97.1%), worst week 96.1% | 96.7 / **90.2** / 92.2 / 90.2% |
| `day_cap=0.09` | +€103 over 9 weeks, binds only on dev-10 (96.2%) | 96.7 / **91.4** / 92.2 / 90.2% |
| `day_cap=0.13 batch_cap=2` | | 95.8 / 88.1 / 91.7 / 91.5% |
| `day_cap=0.12` + `batch_cap` 2 / 3 only on a day with 0.08 / 0.06 due per driver (`batch_load`) | | 96.7 / 88.6–89.0 / 89.5–89.8 / 90.0–90.2% |

A cap on batches is too blunt: it drops batch cars on calm days too. A cap on what is due that day costs nothing on
dev, but counting only undelivered orders lets fresh-06's Friday fill before it binds.

### On top of the quoter's crowd (round-crowd 1199df8, `crowd=0.1 room=8`; control `lcr10r8@95326e6`, dev €98,059)

| Label (bahn-vcrowd 2c3e268, bahn-vcslack af6a6af) | Dev | fresh-04 / 06 / 07 / 08 |
|---|---|---|
| crowd alone | | 98.3 / 93.5 / 94.4 / 92.2% |
| `vol-cr8+dy10@2c3e268` (+ `day_cap=0.10`) | dev-10 +€11 | 98.4 / 93.2 / 94.5 / 92.2%: crowd already prices the full day, so the cap does not bind |
| `vol-cr8-nfl+d22+ab20@af6a6af` (+ Friday-less slack, long dial 0.22, `area_brake=20`) | **+€6,277**, 7 of 10, worst week 95.1% | 95.2 / 92.1 / 91.9 / 92.4% |
| `vol-cr8-sl+d22+ab20@af6a6af` (the same with slack on Fridays) | | 95.5 / 90.8 / 92.6 / **89.3%** (not ranked) |
| `vol-cr8-nfl@af6a6af` (crowd + Friday-less slack only) | **+€8,338**, 8 of 10, worst week 94.9% | 94.1 / 91.2 / 90.2 / 92.0% |
| `vol-cr8-nfl+ab20@af6a6af` | +€7,118, 9 of 10, worst week 96.0% | 96.4 / 90.6 / 90.4 / 91.4% |

All 20 t2-fresh weeks: `vol-cr8-nfl+d22+ab20` €233,838, worst 91.9%, 20 of 20 ranked; `vol-cr8-nfl` €229,602, worst 90.2%,
20 of 20; against `ltd1cr@95326e6` (crowd + today_days) €220,773, worst 93.2%, and `lcr10r10@95326e6` €218,603, worst 90.1%.
Both slack builds beat ltd1cr on 15 of 20 weeks, and both fall under 93% on the same three weeks, fresh-06, 07 and 08,
the crowded ones. Their extra margin is real, but the floor is thinner.

`today_days=1 same_up=0.15` (ltd1cr's two switches) on top of `vol-cr8-nfl+d22+ab20`: dev €102,461, +€725 on ltd1cr but
−€1,876 on the slack build; fresh-04 / 06 / 07 / 08 at 97.6 / 90.9 / 93.6 / 93.4%. today_days and slack go after the same
orders, so they do not stack.

`far_lead=30` (875cdd1, after track 3's finding on ltd1cr: no next_day on a lane of 500 road minutes or more whose last
pickup that still meets the deadline is under 30 hours after the answer). On `vol-cr8-nfl+d22+ab20`: dev +€585, 7 of 10,
worst week 95.9%; fresh-04 / 06 / 07 / 08 at 94.7 / 92.1 / 91.9 / 92.9% (+€1,003 on the four). On `vol-cr8-nfl`: dev +€85,
fresh unchanged except fresh-08 at 91.6%. All 20 fresh weeks on the full build: €234,157, +€319 on af6a6af, worst 91.9%,
20 of 20 ranked. A small, safe gain: the class is about one order a week.

### On the Sunday build (3a2dce2, ltd3h8cr's flags; control `ltd3h8cr@95326e6`, dev €106,041; branch volume-sunday)

| Change | Dev | Notes |
|---|---|---|
| `same_day_slack=1440 slack_friday=false` | +€294, 2 of 10 | 6 weeks identical to the cent: today_days=3 already takes the same orders |
| + long dial, `area_brake=20`, `far_lead=30` | −€928 (9 weeks) | 145 fewer orders |
| `private_slots=true` | −€867 | worst 95.0% |
| `trade_ins=true` | −€20 (8 weeks) | |
| `long_sd_days=3` (same_day on long lanes for Mon–Wed deadlines) | −€504 (8 weeks), 0 of 8 | |
| `min_drivers=2` | +€821, 4 of 10 | worst 95.1% |
| `near_markup=1.0` (lanes under 420 min at 1.0, the rest at 1.15) | +€919 (9 weeks) | fresh-06 / 07 / 08 at 90.1 / 93.2 / 90.8% (ltd3h8cr 92.2 / 94.4 / 92.0%), −€4,730 |
| **`long_markup=1.05`** | **+€1,373, 7 of 10, worst 95.3%** | fresh and study playing |

**long_markup=1.05 passed holdout and orch** (integrator): holdout €122,045 (+€5,869 on ltd3h8cr, 10 of 10, worst 94.6%),
orch-01..10 €120,259 (+€6,201, 8 of 10, worst 93.3%), all 20 fresh ranked (+€5,866), but fresh-08 at 90.4% (92.1%).
fresh-08's extra late orders are long next_day runs north: long next_day 16 late of 30 (ltd3h8cr 8 of 13), espoo→oulu
(405 min) ×9; short orders are no worse (22 of 380 against 24 of 393). **`far_lead=48 far_drive=400`** (no next_day on a
lane of 400+ minutes whose last pickup is under 48 hours after the answer) cuts that class to 6 late of 18: fresh-08 92.8%
(+€3,028), dev €107,559 (+€1,518 on ltd3h8cr), fresh-06/07 unchanged. `far_lead=30 far_drive=400` is −€507 on lm105.
**But fl48 fails orch** (integrator, vol-sun-lm105+fl48d400@3c1eb0c): orch-01..10 €118,579, −€1,680 on lm105, 3 of 10,
orch-08 92.4% (lm105 93.3%); holdout −€920, 5 of 10. The guard buys fresh floor with orch floor and margin: dropped.
`trade_ins=true trade_hour=true` on fl48 (7a310c1): dev +€1,736, fresh +€356, trade-ins still 29% late: no holdout.

**ahead_from moves (sl-wkah@f7ebca4, sl-ah10@2bba163, 70 weeks).** A move earns €30–41 an order. Moves onto Friday are
late 5–8% on fresh and orch, 2–3% on dev and holdout: a weekday guard would give up €500–650 a week. By the load of the
target day at the move (won orders due that day per 100 drivers): under 8, 1.7–3.2% late; 8 or more, 5.6–7.5% (about
4 moves a week, mostly onto Friday). `ahead_full=8` (950f1ce, branch volume-ahead) leaves those cars on today's work.

**The bulk order** (72 weeks of ltd3h8cr): every week, 30–40 cars from one yard. We quote all of them and win 13 a week
(37%), 1.8% late, about €415 a week (€32 a car, a normal margin). From far-north yards the dial quotes 4–6× list and
wins none. Winning the rest is worth at most about €700 a week.

**Long lanes at long_markup=1.0** (holdout, g-lm100@3a2dce2): long orders go from 15 to 38 a week, from €128 to €75 an
order, +€970 a week. 300–420 minutes: 5.6% late at €84; 420–600: 18.8% late at €48.

## What failed

- A markup away from 1.5 in either direction loses margin: 1.4 wins more cars at a thinner margin and gets closer to the
  90% line; 1.6 loses too many cars. 1.55 and 1.45 are not tested.
- Markup 1.7 was dropped after 1.6 lost.

## Next

- Make `open=0.85` the default of `reach`.
- An on-time controller that tightens intake when the predicted on-time share falls, so a cheaper opening fee can be used safely.
