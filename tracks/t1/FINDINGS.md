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

## What failed

- A markup away from 1.5 in either direction loses margin: 1.4 wins more cars at a thinner margin and gets closer to the
  90% line; 1.6 loses too many cars. 1.55 and 1.45 are not tested.
- Markup 1.7 was dropped after 1.6 lost.

## Next

- Make `open=0.85` the default of `reach`.
- An on-time controller that tightens intake when the predicted on-time share falls, so a cheaper opening fee can be used safely.
