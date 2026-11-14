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

Both rows play the weeks that the table was fitted on. Holdout is the first unseen test (`nsd-lanes1@4f287d9`).

### 4. A request that offers only `same_day` (`only_same`, 4f287d9)

For a car that is ready on a later day, a dealer who offers `same_day` alone accepts about 17% more than one who
offers a later option beside it (dev 0.19, study 0.16, the long-lane base's weeks 0.18; `fit10.py`, `fit11.py`). The
dial quotes these at 1.33 × and wins 78% of them, against 43% elsewhere. About 37 orders a week.

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

Also ruled out, in the replay or in the earlier lab weeks: cold direct offers, rationing drivers, a late budget, fees by
driver density, and absolute lane prices.

## Tools

- `lab.py`: saved weeks to one row per request. `fitlib.py`: the logistic fit of the limit.
- `prep.py`, `sim.py`: a replay of the dev weeks' requests against a quoter, offline. It ranks variants; its euros are
  an estimate, and the played weeks decide.
- `places.py`: writes `dispatch/places.py`.
