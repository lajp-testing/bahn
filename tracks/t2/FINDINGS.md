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
