# Track 2: switching prices

## For other tracks

What a request's switching price depends on (first-option ratio to list; four complete no-wins level 8 scans: `t2-scan-1` 1,040, `t2-scan-2` 1,035, `t2-scan-3` 1,039, `t2-scan-4` 1,031 requests; `tracks/t2/structure.py`):

- **A day level per world.** Daily means 1.21–1.67, 1.10–1.62, 1.13–1.42, 1.19–1.52 across the four weeks; within-day stdev 0.14–0.31. The day factor is new each day and each world.
- **The price war is a whole-day drop, on a different day each world.** Day 2 in scans 1–2 (0.82x and 0.76x the mean of the other days, n=191 each), day 1 in scan-3 (0.83x, n=204), day 3 in scan-4 (0.82x, n=238). Nearly all requests arrive inside 08:00–18:00, so the day-wide drop is what you see; quote about 20% lower that day or expect losses. A day mean near 0.8x the running week mean is the signature.
- **The outage hits one pickup region, about +25–40% there.** Scan-1: Uusimaa pickups (Helsinki/Vantaa/Espoo/Porvoo/Hyvinkaa, all within 80 km) on Thursday, region mean 1.81 vs 1.41 outside (in/out 1.27, n 162/85). Scan-2: the same region on Friday (1.79 vs 1.42, in/out 1.26, n 98/81). Scan-3: Oulu pickups on Wednesday, 1.90 that day vs 1.33 for Oulu pickups on other days (+43%, n 16 vs 42). Scan-4: cannot tell — the best candidates (north on Friday: Oulu pickups +11% n=30, Ylivieska deliveries +18% n=8; southwest deliveries on Tuesday +13% n=23) are well below the handbook's ~30%, so the outage there is either in a thinly requested region or too weak to see. Day and region move per world; the visible effect is on the pickup side.
- **The part that holds across worlds is on the delivery town.** After removing each seed-day mean, delivery-town leftovers correlate between every pair of worlds (Pearson r=0.45–0.69, six pairs, 18–19 towns with n>=15 each); pickup-town r=−0.18 to +0.28 and dealer r=−0.36 to +0.32 do not. Same sign in all four weeks: hyvinkaa −0.155/−0.138/−0.185/−0.111, espoo −0.059/−0.157/−0.143/−0.069, vantaa −0.150/−0.028/−0.137/−0.175, kuopio +0.064/+0.241/+0.179/+0.167, pori +0.070/+0.078/+0.122/+0.332, rovaniemi +0.050/+0.036/+0.159/+0.220, vaasa +0.204/+0.023/+0.140/+0.051, ylivieska +0.169/+0.116/+0.335, lahti and salo positive in all four, lappeenranta and mikkeli positive in the weeks that have them. This matches the handbook's lane part that follows drivers near the delivery place: quote up for cars going north and east (pori, ylivieska, rovaniemi, kuopio, vaasa) and down for cars into hyvinkaa, vantaa and espoo.
- **Lane length has no stable effect.** km-band leftovers stay within ±0.10 and flip sign between weeks (n 102–374 per band per week).
- **How fast the day level shows.** The first 10 requests of a day estimate the whole-day mean within −12% to +14% (20 day-week pairs; worst 0.883 on scan-3's war day, 1.142 on scan-2's), the first 20 within −7% to +8%, the first 40 within −4% to +5%.

Older single-week associations (day, dealer, towns explain 13–34% each in-sample) are below. Some second options cannot win even at one cent when quoted alone.

## Findings

| Measurement | Result | Scope |
|---|---|---|
| Method: `t2-scan-check` | 0/31 repeat mismatches at 1.4; 0/31 monotonicity violations across 0.8–2.0 | First option, first 31 requests, one level 8 world; not proof for all prices or requests |
| `t2-scan-2`, level 8, complete | 1,035 first-option requests | Monday–Friday means 1.387, 1.468, 1.100, 1.391, 1.622 (n 219, 204, 191, 242, 179) |
| `t2-scan-3`, level 8, complete | 1,039 first-option requests | Monday–Friday means 1.265, 1.126, 1.419, 1.394, 1.339 (n 219, 204, 191, 246, 179) |
| `t2-scan-4`, level 8, complete | 1,031 first-option requests | Monday–Friday means 1.363, 1.494, 1.456, 1.191, 1.516 (n 219, 204, 191, 238, 179) |
| `t2-scan-1`, level 8 | 1,040 requests, 1,894 option rows | One neutral-parent week, not a ranked run |
| First-option mean switching ratios, Monday–Friday | 1.317, 1.353, 1.208, 1.673, 1.556 | Daily sample sizes 219, 204, 191, 247, 179 |
| Paired same-day minus next-day ratio | Mean +0.189; same-day higher in 558/725 pairs | Each option quoted alone, one week |
| Individual in-sample variance explained | Day 34.4%; dealer 13.0%; pickup 14.8%; delivery 14.9%; hour 0.7%; linear distance 0.1% | Separate univariate fits, not additive or causal; towns and dealers are confounded with day and each other |

Two option rows lost at one cent. In particular R00604's next-day option lost twice at one cent and also at 0.5, 1 and 2 times list; its same-day option won twice at one cent, won at 0.5 and lost at 1 and 2. The scan records the former as a zero bracket, meaning no tested positive price wins, not an exact zero-cent switch. The scanner verifies a four-times upper bracket and stops on a violation. Seven bisections give a bracket 0.03125 wide; this is about 2% around ratios near 1.5, not uniform relative precision. Thresholds near a quoted price have classification uncertainty; the scoring below counts wins only at or below the known winning bound.

The Wednesday trough and Thursday rise of scan-1 turned out to be that world's price war (Wednesday) and outage (Thursday, Uusimaa); the cross-world comparison above now establishes the stable delivery-town lane part. The neutral parent is checked for order wins, and copies separately quote each option; a copy at each price serves all simultaneous requests. Independence of those simultaneous quotes has not been separately established.

## Offline quoting proxy

First option only, on `t2-scan-1`; the learning rules see outcomes at the response deadline. The first-only learning rule applies the existing logistic optimiser and online update to one option, so it is not the current multi-option policy. Calibration explores prices 1.00–2.00 on the first 50 observed outcomes, fits the logistic midpoint, then holds it fixed and optimises the same profit objective. `python3 tracks/t2/analyse_scan.py` reproduces these figures.

| Rule | Requests won | Sum of quoted price less typical fee |
|---|---:|---:|
| Fixed 1.30 | 639/1,040 (61.4%) | €19,608.79 |
| Online learning, first option only | 710/1,040 (68.3%) | €21,523.55 |
| First 50 outcomes calibration | 679/1,040 (65.3%) | €20,132.40 |

On the incomplete 900-request second scan, the same three rules respectively won 533 (59.2%), 596 (66.2%) and 535 (59.4%), with proxy sums €15,500.47, €16,307.98 and €15,157.51. The incomplete week is not comparable as a full-week result.

This is not realised margin or an end-to-end comparison: it ignores how our wins change the competitor, dealer trust and satisfaction, actual driver fees, cancellations and on-time performance. It also ignores choices among multiple quoted options. It is a single-world lead, not an improvement claim.

## Cost and failures

The first 31-request method check took 797 HTTP calls. Before the week, a rough nine-copy, 1,000-request estimate was 30,000 calls and 510 seconds at 17 ms per call, excluding server processing and additional options. The all-option week actually took approximately 57,000 calls and 27 minutes across the initial run and resume; copied event histories and later-day processing made the latency estimate optimistic. Its initial run stopped at request R00604 because the next-day one-cent quote lost. The targeted probe established this was a repeatable zero-positive-price case rather than a failed action. The script was fixed to represent it, and resumed with already saved option rows skipped. An initial launch also failed due to Python's script import path and another due to a zero-cent quote; both were corrected.

## Stint 1, condensed

One first-option fork probe was fixed and monotone across eight trials. A random-price grid found full-Monday midpoint estimates 1.648 (`t2-study-1`) and 1.459 (`dev-01`); estimates from the first 20–50 quotes were within about 0.05 of the same Monday fit, in sample. `t2-learning-v2` on ten dev weeks yielded −€204,983.18 and 61.9% weighted on time, 0/10 ranked, with starter intake; it does not isolate quote quality. The existing `LearningQuoter` is experimental and cannot rebuild its pending quotes from event-only replay. It has not been made production-ready by this scan.

Offline tests: the prescribed command produced 5 passes and one failure because the existing remote-only guard rejects the temporary slot test. Setting `SPREAD_ON_VPS=1` for this isolated offline test gives 6 passes; no worlds were played by the test.

## Stint 4: lane offsets in the live quoter

**Baseline.** `t2s4-base` (`--policy main`, defaults, current code): EUR 73,495 margin over the 10 dev weeks, 1,873 orders, 98.1% on time, 10/10 ranked, worst week 96.9%. This matches the mainline's known numbers.

**The delivery-town table.** `tracks/t2/towns.py` reads all six scans, takes each first-option request's switching ratio minus its world-and-day mean (as `structure.py`), and shrinks each delivery town's mean leftover by `n / (n + 30)`. The result is `dispatch/towns.py` (`DELIVERY`), 30 towns, from hyvinkaa −0.136 and vantaa −0.111 to ylivieska +0.142 and kuopio +0.102. The keys match `request["legs"][0]["delivery"]["placeId"]` in a saved events file exactly (all 30 present on both sides).

**The quoter change.** `ProfitQuoter` gained `towns` (scale for the table), `region` and `region_area` (step sizes for pickup learning, see below), all default 0 so the mainline is unchanged. `chance` takes an `offset`; the level used for a request is `self.level + offset`, where the offset is the delivery town's table entry times `towns` plus what the day has taught about the pickup. The offset used at quote time is stored with the sent ratios and the same offset feeds the learning update in `observe`.

Runs in flight: `t2s4-towns1` (towns=1), `t2s4-towns05` (towns=0.5), `t2s4-towns15` (towns=1.5).

**Option kinds win differently at the same ratio (step 3 evidence).** `tracks/t2/kinds.py` on the ten `t2s4-base` weeks: of our quoted options (declined 4x quotes excluded), `next_day` was taken 1,840/6,608 (27.8%) but `within_3_days` only 56/1,676 (3.3%). Per band (win share, n): 1.2-1.4: 31% (1,786) vs 2% (350); 1.4-1.6: 32% (2,599) vs 4% (654); 1.6-2: 23% (1,444) vs 5% (450). The dealer's switching price for a `within_3_days` option sits well below the one level the quoter keeps, so those quotes are priced too high. `kind_offset` (default 0) adds to the level of every `within_3_days` option; negative values price them down. Each option's own offset is stored with its sent ratio, so the learning update uses the same offset the price was made with.

**Results (10 dev weeks each, margin EUR vs `t2s4-base` 73,495 / 1,873 orders / 98.1% / 10/10).**

| label | change | margin EUR | orders | on time | worst | ranked |
|---|---|---:|---:|---:|---:|---|
| `t2s4-base` | none | 73,495 | 1,873 | 98.1% | 96.9% | 10/10 |
| `t2s4-towns2p0` | towns=2.0 | **75,337** | 1,913 | 98.3% | 97.1% | 10/10 |
| `t2s4-towns15` | towns=1.5 | 74,798 | 1,908 | 98.3% | 97.1% | 10/10 |
| `t2s4-towns25` | towns=2.5 | 74,341 | 1,898 | 98.4% | 96.9% | 10/10 |
| `t2s4-towns15reg01` | towns=1.5, region=0.1 | 73,857 | 1,898 | 98.3% | 97.5% | 10/10 |
| `t2s4-region01` | region=0.1 | 73,454 | 1,878 | 98.2% | 96.6% | 10/10 |
| `t2s4-towns05` | towns=0.5 | 72,513 | 1,874 | 98.2% | 95.8% | 10/10 |
| `t2s4-region005` | region=0.05 | 72,105 | 1,848 | 98.2% | 96.6% | 10/10 |
| `t2s4-kindm04` | kind_offset=−0.4 | 72,044 | 1,857 | 98.3% | 96.9% | 10/10 |
| `t2s4-region02` | region=0.2 | 72,014 | 1,837 | 98.1% | 96.0% | 10/10 |
| `t2s4-towns1` | towns=1 | 71,326 | 1,873 | 98.3% | 95.8% | 10/10 |
| `t2s4-kindm02` | kind_offset=−0.2 | 70,936 | 1,849 | 98.5% | 96.9% | 10/10 |

**The delivery-town table pays only when it is strong.** The curve is not monotonic: towns=0.5 loses 982, towns=1 loses 2,169 (worse on 7/10 weeks), towns=1.5 gains 1,302, towns=2.0 gains 1,842 (higher on 5/10 weeks, all ranked, worst week 97.1%), towns=2.5 falls back to +846. The peak is at 2.0. The mechanism shows in the volume: at 2.0 we win 1,913 orders vs 1,873 (+40), and the biggest gains are the weeks that gained the most orders (dev-04 +11 orders/+814 EUR, dev-05 +11/+711, dev-01 +4/+442). At strength 2 the big negative-leftover delivery towns (hyvinkaa −0.27, vantaa −0.22, espoo −0.14, helsinki −0.11 at that scale) are quoted low enough to win real extra volume, and that volume is on time and profitable; the positive towns quoted higher lose little. At weak strengths the same quotes move prices without crossing any dealer's switching price, so the mix just gets worse; past 2.0 the extra discount in the big towns stops paying. **Recommendation for the mainline: `towns=2`** (`bin/vps python3 -m harness.run --policy main --seeds dev --set towns=2`, label `t2s4-towns2p0`, EUR 75,337 vs 73,495). The gain is above the noise bar with every week still ranked; the weeks split 5/10, so the orchestrator should re-check it on the holdout seeds before adopting.

**Region learning on top of towns loses too.** `towns=1.5 region=0.1` gives 73,857, i.e. 941 less than towns=1.5 alone (74,798): the pickup offsets are noise that the town offsets then have to price through. Region stays default-off.

**Same-day pickup learning does not pay.** region=0.05 loses 1,390 (and 25 orders), region=0.1 is a wash (−41), region=0.2 loses 1,481 (and 36 orders). The outage-day pickup premium (+25–43% in one 80 km region, one day a week) is too rare and too thinly sampled per town to learn faster than it costs: most days the region offsets are noise around zero, and every quote pays the spread of that noise. The 80 km-area keying (`region_area`) was implemented but never run — the town-keyed version already fails, and the area key only smooths the same signal.

**Pricing `within_3_days` down does not pay either.** kind_offset=−0.2 loses 1,559 and kind_offset=−0.4 loses 1,451. The rare within_3_days wins (5.6 a week) are not worth the margin given up: the dealer who would have taken our next_day option at a good price sometimes takes the now-cheaper within_3_days option instead. The parameter stays default-off.

## Stint 5: a level per dealer

Baseline `t2s5-base` (mainline, trust on): EUR 88,588, 2,288 orders, 97.8% on time, worst week 96.4%, 10/10 ranked — matches the stated mainline exactly.

### Step 1: per-dealer win rates at the same effective ratio (`tracks/t2/dealers.py`)

7,909 really-quoted requests over the 10 dev weeks. The effective ratio is (lowest quoted price / list) / (the dealer's trust factor at that moment, rebuilt from the ledger). Six largest dealers: D01 2,319, D02 939, D03 651, D04 452, D05 415, D06 314 requests.

Share won per ratio band (n, share, mean ratio):

| dealer | <1.2 | 1.2-1.4 | 1.4-1.6 | >1.6 |
|---|---|---|---|---|
| D01 | 38.9% | 46.9% | 35.6% | 11.5% |
| D02 | 23.5% | 40.3% | 35.6% | 14.7% |
| D03 | 20.0% | 23.3% | 24.5% | 11.9% |
| D04 | 19.2% | 28.8% | 31.6% | 10.4% |
| D05 | 18.5% | 20.5% | 24.6% | 16.9% |
| D06 | 41.7% | 36.5% | 35.6% | 11.2% |
| others | 28.7% | 32.4% | 29.6% | 8.3% |

- **At the same effective ratio, dealers buy at clearly different rates.** D01 is above the pack in every band (e.g. 46.9% vs 32.4% of others at 1.2-1.4); D03 and D05 are below in every band (20-25% vs 29-32%). The ordering is the same in all four bands, so it is a level offset, not noise. D06 looks high too but is small (314 requests).
- **A dealer's share won drifts from day to day**, but the per-day mean ratio barely moves (D01: 26.4% won at ratio 1.49 on Monday vs 56.1% at 1.40 on Thursday). Part of that is the shared day level (price-war days), so the band table is the cleaner evidence.
- Caveat: the effective ratio is measured against the quoter's own level, so band win rates are not calibrated in absolute terms (the <1.2 band wins less often than 1.2-1.4, because low ratios cluster on days where the quoter's level lags the true one). The dealer comparison within a band is still apples-to-apples.

So the dealer is a real unit for the price level, as the handbook's competitor note suggests. Step 2 gives each dealer its own learned offset.

### Step 4 (early, offline): the spread fit (`tracks/t2/spread_fit.py`)

Fitting one level per day and the spread jointly by grid on the same 7,909 requests: the log-likelihood rises to spread 0.40-0.45 (LL -4502.8, day levels 1.04-1.29) and falls after 0.50. The best spread is about double the quoter's 0.2. Caveat: the effective ratio is measured against the quoter's own moving level, and a single level per day cannot track the quoter's within-day steps, so the fit inflates the spread. Worth one run at `spread=0.4`; the true switching-price stdev in the handbook is 0.2-0.35, so 0.4 is at the edge of plausible.

### Step 2: a learned offset per dealer — loses at every step size

` ProfitQuoter` gained `dealer` (step size, default 0): each dealer gets an offset to the level, learned from its own wins and losses (clamped to ±0.4, kept for the whole week); `chance` takes the offset and `observe` updates both the global level and the dealer offset with the same chance. All defaults keep the mainline unchanged; tests pass (21).

| label | change | margin EUR | orders | on time | worst | ranked |
|---|---|---:|---:|---:|---:|---|
| `t2s5-base` | none | 88,588 | 2,288 | 97.8% | 96.4% | 10/10 |
| `t2s5-dealer002` | dealer=0.02 | 87,079 | 2,264 | 97.7% | 96.1% | 10/10 |
| `t2s5-dealer005` | dealer=0.05 | 86,597 | 2,253 | 98.0% | 95.9% | 10/10 |
| `t2s5-dealer01` | dealer=0.1 | 85,503 | 2,231 | 97.8% | 93.5% | 10/10 |

All three lose margin, monotonically in the step size, and all lose orders (−24 at 0.02, −57 at 0.1). `dealer002` splits 5/10 weeks (−1,509 total): noise-level, but never positive. Why the measurement did not translate: (1) the dealer differences in step 1 are measured against the quoter's own level, and the learning rule has to find them from single win/loss bits with a moving global level — the offset noise is paid on every quote; (2) the competitor answers per dealer (handbook: where we win most it cuts its prices), so exploiting a dealer that buys easily invites the cut and the learned offset chases a level that moves away. Per-dealer offsets stay default-off (`dealer=0`).

### Step 3: the delivery-town table on the new mainline — towns=1.5 gains, peak moved left

`dispatch/towns.py` (the stint 4 `DELIVERY` table) brought over by hand and wired into the current quoter: `towns` (scale, default 0) adds `towns * DELIVERY.get(delivery placeId)` to the level offset that `chance` takes; the same offset feeds the learning update. Defaults keep the mainline unchanged; tests pass (21).

| label | change | margin EUR | orders | on time | worst | ranked |
|---|---|---:|---:|---:|---:|---|
| `t2s5-base` | none | 88,588 | 2,288 | 97.8% | 96.4% | 10/10 |
| `t2s5-towns15` | towns=1.5 | **90,156** | 2,291 | 98.3% | 96.5% | 10/10 |
| `t2s5-towns2` | towns=2 | 87,401 | 2,261 | 97.8% | 93.9% | 10/10 |

On the old mainline (stint 4) the peak was at towns=2.0 (+1,842); on the current mainline towns=2 loses (−1,187, 4/10 weeks) and towns=1.5 gains +1,568 (6/10 weeks, all ranked, on time up in 8/10 weeks, dev-08 +1,635 the largest). The gain is just above the noise threshold with 6/10 agreement, so the peak is being bracketed with towns=1 and towns=1.75 before any recommendation.

### Step 3 continued: the towns hill on the new mainline, and the spread test

| label | change | margin EUR | orders | on time | worst | ranked | weeks better than base |
|---|---|---:|---:|---:|---:|---|---:|
| `t2s5-base` | none | 88,588 | 2,288 | 97.8% | 96.4% | 10/10 | — |
| `t2s5-towns1` | towns=1 | 90,140 | 2,294 | 98.1% | 95.7% | 10/10 | 7/10 |
| `t2s5-towns15` | towns=1.5 | **90,156** | 2,291 | 98.3% | 96.5% | 10/10 | 6/10 |
| `t2s5-towns175` | towns=1.75 | 90,101 | 2,295 | 98.5% | 97.0% | 10/10 | 6/10 |
| `t2s5-towns2` | towns=2 | 87,401 | 2,261 | 97.8% | 93.9% | 10/10 | 4/10 |
| `t2s5-spread04` | spread=0.4 | 64,715 | 1,263 | 97.9% | 95.7% | 10/10 | 0/10 |

- **The delivery-town table pays on the current mainline, with a broad flat hill from 1.0 to 1.75** (+1,552, +1,568, +1,513). towns=1 passes the evidence rule outright (7/10 weeks); towns=1.5 has the highest total and the best on-time of the three. towns=2 falls off the hill (−1,187), so the optimum sits near 1.5, half of stint 4's 2.0 — the trust and limit changes moved the operating point. Recommendation for the mainline: `towns=1.5` (EUR 90,156, +1,568, 98.3% on time, worst 96.5%, 10/10).
- **spread=0.4 is a disaster**: −23,873 and half the orders (1,263 vs 2,288). A flatter chance curve moves the profit-maximising price up, so we price ourselves out of half the requests. This confirms the step 4 caveat: the offline fit's 0.40-0.45 is an artifact of measuring the ratio against the quoter's own moving level, not the dealers' true spread. The quoter's `spread=0.2` stays.

### Stint 5 bottom line

- Keep: `towns=1.5` (delivery-town lane offsets, `dispatch/towns.py`), +1,568 over the base on the dev weeks, all weeks ranked, on time up. Held out for the orchestrator's holdout check.
- Reject: per-dealer learned offsets (`dealer`), all step sizes negative; `spread=0.4`, catastrophic.
- 9 of 16 runs used.

## Stint 6: same-day options and the curve's shape

Test bed: the mainline with track 1's same-day admission (`--set same_day_slack=360 --set same_day_drivers=80`), expected about EUR 100,657. `same` (stint 6) is a level offset for a `same_day` option; `kind_offset` (within_3_days, re-added through the same code path) and `shape`/`shape_scale` (the measured curve) are default-off.

### Step 1 measurement: the same-day premium (`tracks/t2/kinds2.py`)

Leftover = an option's switching ratio minus its world-and-day mean of `next_day` rows (switch_high=0 rows skipped):

| kind | n | mean | q25 | q50 | q75 |
|---|---:|---:|---:|---:|---:|
| next_day | 2,942 | 0.000 | −0.148 | −0.001 | 0.154 |
| same_day | 3,918 | +0.008 | −0.144 | −0.007 | 0.144 |
| within_3_days | 131 | +0.048 | −0.073 | +0.077 | 0.224 |

The pooled +0.008 is an artifact of composition. Only scan-1 scanned two options of the same request; scans 2–6 scanned one option per request, and their `next_day` rows are only requests *without* a same-day option (list EUR 89.79 vs 76.93, lane 231 vs 172 km — disjoint populations). Split by world, the same_day leftover is +0.140 in scan-1 but −0.02 to −0.06 in scans 2–6, exactly where the populations are disjoint. The only within-request evidence is scan-1's 723 paired requests: same_day ratio minus next_day ratio **+0.186** (558/725 pairs higher; list +610 cents, absolute switch price +1,664 cents). The handbook fits this: the competitor's price is list × factors (the same for every option of a request), and the dealer adds the value of each option's speed. So the premium is real but measured in one world only; the `same` sweep (0.1/0.2/0.3) arbitrates on the test bed.

### Step 2 measurement: the true shape (`tracks/t2/shape.py`, `dispatch/shape.py`)

z = switching ratio minus the world-and-day mean of the same kind (same_day rows, the most common kind: 3,918 rows, 30 world-days). S(z) = share of rows with leftover above z, against the logistic the quoter assumed:

| z | −0.4 | −0.3 | −0.2 | −0.1 | 0 | +0.1 | +0.2 | +0.3 | +0.4 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| S(z) | 0.979 | 0.938 | 0.836 | 0.672 | 0.474 | 0.293 | 0.158 | 0.080 | 0.037 |
| logistic 0.2 | 0.881 | 0.818 | 0.731 | 0.622 | 0.500 | 0.378 | 0.269 | 0.182 | 0.119 |
| logistic 0.3 | 0.791 | 0.731 | 0.661 | 0.583 | 0.500 | 0.417 | 0.339 | 0.269 | 0.209 |

The true curve is **steeper in the middle** than the logistic 0.2 (S falls 0.84→0.16 over ±0.2 vs 0.73→0.27; the middle slope matches a logistic with spread ≈0.13) and **thinner in both tails** (2% of mass beyond ±0.4 vs 12%). It is not flatter, so the stint-5 spread=0.4 failure does not predict a failure for the table; a steeper curve moves the profit-maximising price *down*, towards more volume. next_day rows give nearly the same curve. The table is `dispatch/shape.py` (`SURVIVAL`), used by `shape="table"` with linear interpolation.

### Step 1 runs: the `same` sweep on the test bed

| label | change | margin EUR | orders | on time | worst | ranked | weeks better than base |
|---|---|---:|---:|---:|---:|---|---:|
| `t2s6-base` | none | 100,657 | 2,731 | 96.7% | 91.5% | 10/10 | — |
| `t2s6-same01` | same=0.1 | 99,135 | 2,670 | 96.5% | 93.2% | 10/10 | 3/10 |
| `t2s6-same02` | same=0.2 | 101,088 | 2,650 | 97.2% | 93.8% | 10/10 | 5/10 |
| `t2s6-same03` | same=0.3 | 98,049 | 2,605 | 97.2% | 95.0% | 10/10 | 3/10 |

same=0.1 loses 1,522 and 61 orders; same=0.3 loses 2,608 (3/10 weeks, though on time again better, worst 95.0%). same=0.2 gains +431 — under the noise bar with only 5/10 weeks agreeing, so not a finding by the evidence rules — but it wins fewer orders (−81) at a clearly higher EUR/order (38.1 vs 36.9) and on time improves everywhere (96.7%→97.2%, worst 91.5%→93.8%; dev-07 +1,322). The same-day premium is real but small at the operating point: the hill peaks near 0.2, and the volume the higher same-day prices give up eats most of what they earn.

### Step 2 runs: the measured curve

| label | change | margin EUR | orders | on time | worst | ranked | weeks better than base |
|---|---|---:|---:|---:|---:|---|---:|
| `t2s6-shape` | shape=table | 94,148 | 3,034 | 96.2% | 92.3% | 10/10 | 3/10 |
| `t2s6-shape-same` | shape=table, same=0.2 | 93,355 | 2,942 | 96.4% | 93.4% | 10/10 | 1/10 |
| `t2s6-shape15` | shape=table, shape_scale=1.5 | 101,854 | 2,768 | 96.7% | 93.8% | 10/10 | 6/10 |

Widening the table's z axis by 1.5 (middle slope back to about the logistic 0.2, tails still thinner) recovers the loss and lands at +1,198 over the base, 6/10 weeks better, worst week 93.8% vs the base's 91.5% (dev-07 +1,278, dev-10 +1,188, dev-08 −2,069 the drag). The gain is under the noise bar without 7/10 agreement, so the table at scale 1.5 is a lead, not a finding. `same` on top of the steep table loses more (93,355, −793 vs the table alone) — the steeper curve already prices same-day options closer to their level. On the widened table, `same=0.2` cancels the gain instead of adding to it: `t2s6-shape15-same02` 100,569 (−88 vs base, 97.2% on time, worst 94.2%).

### Step 3 runs: the town table on the test bed

| label | change | margin EUR | orders | on time | worst | ranked | weeks better than base |
|---|---|---:|---:|---:|---:|---|---:|
| `t2s6-towns15` | towns=1.5 | 99,417 | 2,739 | 96.9% | 92.9% | 10/10 | 5/10 |
| `t2s6-towns15-same` | towns=1.5, same=0.2 | 100,556 | 2,672 | 97.3% | 94.3% | 10/10 | 5/10 |
| `t2s6-shape15-same02` | shape=table, shape_scale=1.5, same=0.2 | 100,569 | 2,707 | 97.2% | 94.2% | 10/10 | |

On the old mainline towns=1.5 gained +1,568 (stint 5); on the same-day test bed it loses 1,240 (5/10 weeks) and `same` on top does not recover it either (−101 vs base, 5/10). The same-day volume moves the operating point again: the town offsets' cheap-town wins now collide with the same-day options the intake admits. `towns` stays at the mainline's default on this test bed.

### Stint 6 bottom line

- Nothing passes the evidence rules on the same-day test bed. The two leads, both under the EUR 1,500 bar: `shape=table shape_scale=1.5` (+1,198, 6/10 weeks, worst week 93.8% vs the base's 91.5%) and `same=0.2` (+431, 5/10, on time 97.2%, worst 93.8%). They do not compose (100,569, −88). `towns=1.5`, the stint 5 keep, loses 1,240 on this test bed and should be re-tuned or dropped if the mainline adopts same-day admission.
- Reject: the measured curve at its natural scale (`shape=table`, −6,509 — the table is measured around the true day mean, but the live level's own error widens the effective curve), `same` at 0.1 and 0.3, every combination with `towns=1.5`.
- Code kept, all default-off: `same`, `kind_offset` (re-added through one `kind_off` path), `shape`, `shape_scale` in `ProfitQuoter`; `PROFIT` passes them through. 22 offline tests pass.
- 10 of 16 runs used.
