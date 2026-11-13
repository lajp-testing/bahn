# Track 2: Quotes

**Question.** At what price against the list price do quotes start to lose, by lane, dealer, day and hour?

## Findings

Nothing measured yet.

| Label | Weeks | Margin | On time | Ranked | What it shows |
|---|---|---|---|---|---|

## What failed

Nothing yet.

## Stint 1: first-option grid

`t2-grid-v1` hashes the request ID to 21 prices from 1.00 to 2.00 times list, and quotes only the first option. Two level 8 weeks: t2-study-1 margin −€3,135.01, 86.0% on time (479 orders); dev-01 −€5,420.64, 75.2% on time (427 orders). Neither ranked. Monday at 1.40 won 8/9 and 6/11 respectively; at 1.50, 9/10 and 4/12; at 1.60, 5/14 and 3/16. Samples per cell are small. Later results are confounded by war, trust, late deliveries and competitor response; do not treat them as a stationary curve. Run `python3 -m tracks.t2.curve t2-grid-v1` for all counts.

## Fork probe

`python3 -m tracks.t2.fork_test`: one request in t2-fork-1, first option only. 1.0 won, 1.2–1.8 lost; repeated 1.2, 1.4 and 1.6 all lost again. This is consistent with fixed, monotone outcomes for this request only, not proof across requests or options. Eight sequential copies and setup/cleanup cost 37 HTTP requests; each additional fork probe costs approximately four, excluding retries. The switch is bracketed between 1.0 and 1.2, not yet binary searched to the cent.

## Failures and limitations

The first grid launches failed before play because the research quoter did not inherit Part; fixed and rerun. The first fork launch failed because advance-until needs a maximum minute; fixed. Option, lane, dealer, hour, learning speed, war and outage effects remain unmeasured. Two weeks are a lead, not a 10-seed comparison.

The grid reveal has 483/1,033 won requests in t2-study-1 and 433/1,035 in dev-01 (including later-cancelled orders). Mean quoted revenue per won request was €105.21 and €89.54; the sum of quote minus one typical fee was €12,897.81 and €10,332.85. These are quote proxies, not realised revenue or margin.

A provisional `LearningQuoter` uses one shared logistic curve, optimises each option's expected quote less `cost_factor` times typical fee, and updates the midpoint from wins and losses. It approximates a multi-option outcome using the lowest quote/list ratio; the curve, fixed slope and initial midpoint are not yet validated. It cannot reconstruct past quotes from event-only replay, and intake changes to quotes only reach learning via accepted action results. Do not use it in the final without addressing replay, option-choice confounding, and validation. `t2-learning-v1` ran an earlier version which only learned from single-option quotes; `t2-learning-v2` is the multi-option approximation.

`t2-learning-v1` pilot: dev-01 margin −€9,673.54, 64.3% on time (610 orders); dev-02 −€14,808.18, 72.8% on time (591 orders). Total −€24,481.72, 68.4% weighted on time, 0/2 ranked. It used the earlier single-option-only update, so does not measure the updated approximation. No paired 10-week conclusion is justified.

Monday quotes between 1.30 inclusive and 1.60 exclusive (pooled across prices, so not controlled for price mix): in t2-study-1, same_day won 18/18 and next_day 39/45; in dev-01 same_day won 32/57 and next_day 7/14. These counts are too small and confounded to infer an option effect. For v1, mean quoted revenue per won request was €85.35 on dev-01 and €107.36 on dev-02; sum of quote minus typical fee was €15,740.60 and €19,714.95. For v2, the respective values were €86.52 and €103.11; €15,800.82 and €19,315.90. Reveal wins include cancellations; realised orders in the score exclude them.

Exploratory prefix fit (`python3 -m tracks.t2.learning t2-grid-v1`): fitting a fixed 0.10 logistic scale to randomized Monday outcomes, midpoint estimates at 20/50/100/all quotes were 1.660/1.595/1.647/1.648 for t2-study-1 (219 quotes), and 1.462/1.433/1.475/1.459 for dev-01 (254 quotes). This compares prefixes to the same Monday's full fit, not to true competitor prices or out-of-sample performance; two worlds do not establish a sample requirement. It does not establish detection of a war or outage.
