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

**Ruled out.** Same-day on a car ready today: in `sd@f5a6b3b` even short lanes from pickups with 20 or more drivers
within 30 km and 6 hours of slack were late 25% of the time, at €16 an order.

## What failed

- A markup away from 1.5 in either direction loses margin: 1.4 wins more cars at a thinner margin and gets closer to the
  90% line; 1.6 loses too many cars. 1.55 and 1.45 are not tested.
- Markup 1.7 was dropped after 1.6 lost.

## Next

- Make `open=0.85` the default of `reach`.
- An on-time controller that tightens intake when the predicted on-time share falls, so a cheaper opening fee can be used safely.
