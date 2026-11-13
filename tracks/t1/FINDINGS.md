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

## What failed

- A markup away from 1.5 in either direction loses margin: 1.4 wins more cars at a thinner margin and gets closer to the
  90% line; 1.6 loses too many cars. 1.55 and 1.45 are not tested.
- Markup 1.7 was dropped after 1.6 lost.

## Next

- Fees: try 0.75 × and 0.7 × openings; watch the worst week's on-time share (94.1% at 0.85 ×).
- Confirm `open=0.85` on the holdout seeds (orchestrator).
