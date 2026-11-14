# Plan: a learned cost model for quotes and fees

Status: proposal, 14 November 2026, 11:30 UTC. Not started. A side thread is to do this work; this thread keeps running the experiments.

## Why

Our margin is limited by delivery capacity, not by quotes. The top 10 teams move about 40% more cars per week than we do, at the same margin per car and better on-time share (`tracks/t2/FINDINGS.md`, "Where our delivery capacity goes"). Every attempt to win more orders with a fixed rule (lower prices, higher limits, fractional queue places) won cars that were expensive or late, and lowered the worst week. The one that worked best this morning, pricing a car lower when it can join an open gig (`pair`, +€13–15k over 30 weeks), works because it prices one cost factor better.

So the lever is a better answer to one question that the quoter asks for every request: **what will this car cost us to deliver, and how likely is it to be late?** Today that answer is fee model 2 (`dispatch/fees.py`, `MODEL2_EXPECTED` and `MODEL2_LATE`). It is a hand-fit linear formula: a base multiple of the typical fee, plus fixed amounts for 9 yes/no facts (lead time bands, time of day, private address, a lane over 500 km, drivers near the pickup and the delivery). A model that learns from all our weeks can see interactions this formula cannot, such as a long lane that is cheap because it ends where drivers live, or a short one that is dear on a Friday afternoon.

## The data we have

- **Saved weeks:** 4,371 weeks with about 1.09 million won orders, across 55 seeds (dev-01..10, hold-01..10, rob-01..20 and the tracks' own study seeds) and many policies. Each week's folder under `data/runs/` holds:
  - `events.jsonl.gz`: every request, win, booking (with the fee), drop, no-show, delivery and ledger line;
  - `actions.jsonl.gz`: every quote and every gig posted or repriced, with its stops and fee schedule;
  - `reveal.json.gz`: each request's outcome; each car's real ready time, opening hours and pickup and delivery minutes; each gig view with the fee the driver saw;
  - `roster.json.gz`: the drivers with their home places.
- **The map:** `data/map.json`, the same in every world, with road minutes and km. `dispatch/context.py` reads it.
- **Selection:** we only see costs for orders we won and posted, under the fee schedules our policies used. Many policies with different schedules make the data richer than one policy's would be, but cars we always declined (some private addresses, some same-day options) are thin.
- **Drift:** the world's lane factors are partly redrawn per world, and the driver shortage per town is redrawn per world. A learned model can only learn what holds across worlds. Within a week the quoter's own learned level and the dealers' trust handle the rest; the cost model need not.

## What to learn

One row per **won car** (a leg of a won order), with features known **at quote time**, and three targets:

| Target | Definition | Use |
|---|---|---|
| `fee` | total driver fee paid for the car, over its typical fee (for a car in a bundle, its share of the gig's fee) | the quoter's expected cost (`Fees.expected`) |
| `late` | 1 when the order was delivered after its deadline or not at all | the quoter's late risk (`Fees.late_risk`) |
| `refund` | late refund plus undelivered penalty, over the order's price | a check on `late`; may replace it |

Features (all from the request, the map, the roster and the clock; nothing from after the quote):
- **Lane:** pickup and delivery town, road km and minutes, straight km, drivers living within 30 and 80 km of the pickup and of the delivery, the delivery town's lane part (`dispatch/towns.py`).
- **Time:** weekday, minute of the day the request arrives, lead time to the earliest pickup, slack between the option's latest delivery and the drive, whether the window crosses a night or a weekend.
- **The car and the note:** private address at either end, electric with low charge, premium, manual gearbox, plates, a stated ready time or tighter deadline (from `dispatch/reader.py` and `ReadNotes.facts`).
- **Option:** same day, next day, within 3 days.
- **Our own state at quote time:** orders without a driver, open gigs that the car could join (`Bundles.fits`), how many of our drivers finish near the pickup in the next hours. These are what make a car cheap or dear for us in particular. They are policy-dependent, so check that the model's use of them holds on policies it was not trained on.
- **Not allowed:** anything that happens after the quote: the booking minute, drops, the fee schedule actually used (the model must predict the cost under our mainline schedule; restrict training rows to labels whose fee schedule is the mainline's or close to it, or add the schedule's opening and cap as features and set them to the mainline's at use).

## Model

- **Gradient-boosted trees** (LightGBM or scikit-learn's `HistGradientBoostingRegressor`), one per target; Poisson or Tweedie loss for `fee`, log loss for `late`. A few hundred trees of depth 4 to 6.
- **No GPU:** this is tabular data with about a million rows and about 40 features. It trains in minutes on 8 CPUs (the Stockholm practice machine) or on the laptop. The Verda credits are not needed.
- **Baselines to beat:** fee model 1 (default before today), fee model 2 (now the mainline), and a constant. Report each on the same test rows.

## Validation

1. **Split by world, never by row:** train on rows from the dev, rob and study seeds; test on the holdout seeds `hold-01..10` (never trained on). Rows of one world must not be on both sides, because a world's driver shortage and lane factors are shared by all its cars.
2. **Offline metrics:** mean absolute error of `fee` over typical, against fee model 2; log loss and calibration of `late` by decile; and the one that matters for quoting: on the test rows, rank cars by predicted cost per euro of list price and check that the cheapest fifth really cost less and was late less often than fee model 2's cheapest fifth.
3. **Online:** put the model behind a switch (`--set fee_model=3`), check that `main` with the switch off is unchanged to the cent, then play the 30 weeks (dev + rob-01..20) paired with the current mainline, then the 10 holdout weeks. Adopt only if the 40-week total margin is higher and the three lowest on-time weeks do not fall.

## Running it inside the dispatcher

The practice machine and the live runner use **Python's standard library only**. So the trained model is exported as plain Python:
- trees written out as nested `if` statements in a generated module `dispatch/learned.py` (a few hundred kB is fine), or
- a lookup table if a simpler model does as well.

The generator script lives under `tracks/ml/`. `Fees.expected` and `Fees.late_risk` call `dispatch.learned` when `model == 3`. The features must be computed by the same code at training and at quote time; write one `features(request, desk)` function in `dispatch/` and use it for both, with the training script replaying saved weeks through a desk to get the at-quote-time state.

Speed: a quote must be answered within 15 world minutes, which is 4.5 real seconds in the final; the slowest decision batch today takes 121 ms. A few hundred trees of depth 6 in plain Python cost well under a millisecond per request.

## Steps and time box

| Step | What | Done when | Time |
|---|---|---|---|
| 1 | `features(request, desk)` and a replay script that writes one row per won car from saved weeks | a parquet or CSV of about a million rows, with the targets | 1.5 h |
| 2 | Train the three models; compare with fee models 1 and 2 on the holdout rows | an offline table: MAE, log loss, calibration, cheapest-fifth check | 1 h |
| 3 | Export to `dispatch/learned.py`; `fee_model=3`; offline tests; switch-off check | `main` unchanged to the cent; a smoke week runs | 1 h |
| 4 | Hand back to this thread for the 30 + 10 week measurement | paired result against the mainline | 30 min of play |

The code freeze is about 02:00 UTC on Sunday 15 November. If the model does not beat the mainline on the 40 weeks by about 22:00 UTC on Saturday, it stays out of the final.

## Risks

- **Policy dependence:** costs depend on our own fee schedule and intake. A model trained on many policies may learn costs that no longer hold under the mainline; restrict or condition on the schedule (above).
- **Feedback:** a better cost model changes which cars we win, which changes our driver load and so the costs. The online measurement catches this; the offline metrics cannot.
- **Overfitting to the 55 seeds:** world-level effects dominate. Keep the trees shallow, and judge on the holdout worlds only.
- **The final is one week:** a model that adds margin on average but has a worse worst week is not worth it (see the evidence rule in `HANDOFF.md`).
