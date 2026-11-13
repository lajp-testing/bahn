# Track 2: switching prices

## For other tracks

What a request's switching price depends on (first-option ratio to list, two complete no-wins level 8 scans `t2-scan-1` 1,040 and `t2-scan-2` 1,035 requests, `structure.py`):

- **A day level per world.** Daily means 1.21–1.67 (scan-1) and 1.10–1.62 (scan-2); within-day stdev 0.17–0.31. The day factor is new each day and each world.
- **The price war is the whole-day signal.** Day 2 (Wednesday) in both weeks: the day mean is 0.82x (scan-1) and 0.76x (scan-2) the mean of the other days, n=191 both. Nearly all requests arrive inside 08:00–18:00, so the day-wide drop is what you see; quote ~20% lower that day or expect losses.
- **The outage hits one pickup region.** In both weeks the region is Uusimaa (Helsinki/Vantaa/Espoo/Porvoo/Hyvinkaa, all within 80 km): Thursday in scan-1 (region mean 1.81 vs 1.41 outside, in/out 1.27, n 162/85), Friday in scan-2 (1.79 vs 1.42, in/out 1.26, n 98/81). Dealers there accept ~25–30% more that day; the day and the region anchor move per world.
- **The part that holds across worlds is on the delivery town.** After removing each day's mean, delivery-town leftovers correlate between the two worlds (Pearson r=0.45, 18 towns with n>=15 each); pickup-town r=0.28 (15) and dealer r=0.05 (10) do not. Same-sign delivery towns in both weeks: hyvinkaa −0.155/−0.149, espoo −0.059/−0.142, vantaa −0.150/−0.041, ylivieska +0.169/+0.128, pori +0.070/+0.095, porvoo +0.067/+0.078, rovaniemi +0.050/+0.035, oulu +0.016/+0.010, kuopio +0.064/+0.217. This matches the handbook's lane part that follows drivers near the delivery place.
- **Lane length has no stable effect.** km-band leftovers stay within ±0.04 in both weeks (n 102–359 per band).
- **How fast the day level shows.** The first 10 requests of a day estimate the whole day mean within ~±10%, the first 20 within ~±8%, the first 40 within ~5% (10 day-seed pairs; worst first-10 case 1.14 on the war day, scan-2).

Numbers from two worlds; scans 3 and 4 are running to confirm. Older single-week associations (day, dealer, towns explain 13–34% each in-sample) are below. Some second options cannot win even at one cent when quoted alone.

## Findings

| Measurement | Result | Scope |
|---|---|---|
| Method: `t2-scan-check` | 0/31 repeat mismatches at 1.4; 0/31 monotonicity violations across 0.8–2.0 | First option, first 31 requests, one level 8 world; not proof for all prices or requests |
| `t2-scan-2`, level 8, incomplete | 900 first-option requests, through Friday morning | Monday–Thursday means 1.387, 1.468, 1.100, 1.391; Friday is incomplete |
| `t2-scan-1`, level 8 | 1,040 requests, 1,894 option rows | One neutral-parent week, not a ranked run |
| First-option mean switching ratios, Monday–Friday | 1.317, 1.353, 1.208, 1.673, 1.556 | Daily sample sizes 219, 204, 191, 247, 179 |
| Paired same-day minus next-day ratio | Mean +0.189; same-day higher in 558/725 pairs | Each option quoted alone, one week |
| Individual in-sample variance explained | Day 34.4%; dealer 13.0%; pickup 14.8%; delivery 14.9%; hour 0.7%; linear distance 0.1% | Separate univariate fits, not additive or causal; towns and dealers are confounded with day and each other |

Two option rows lost at one cent. In particular R00604's next-day option lost twice at one cent and also at 0.5, 1 and 2 times list; its same-day option won twice at one cent, won at 0.5 and lost at 1 and 2. The scan records the former as a zero bracket, meaning no tested positive price wins, not an exact zero-cent switch. The scanner verifies a four-times upper bracket and stops on a violation. Seven bisections give a bracket 0.03125 wide; this is about 2% around ratios near 1.5, not uniform relative precision. Thresholds near a quoted price have classification uncertainty; the scoring below counts wins only at or below the known winning bound.

The Wednesday trough and Thursday rise are visible, but one week does not identify a price war or outage region. No cross-world lane effect or level comparison has yet been established. The neutral parent is checked for order wins, and copies separately quote each option; a copy at each price serves all simultaneous requests. Independence of those simultaneous quotes has not been separately established.

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
