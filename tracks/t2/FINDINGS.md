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
