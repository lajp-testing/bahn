# Track 2: switching prices

## For other tracks

In one no-wins level 8 week, the first-option switching ratio varies markedly by day and by pickup, delivery and dealer; straight-line distance and hour alone explain little. These are in-sample associations, not independent effects or evidence across worlds. We do not yet know how early the world level can be learned reliably. Some second options cannot win even at one cent when quoted alone.

## Findings

| Measurement | Result | Scope |
|---|---|---|
| Method: `t2-scan-check` | 0/31 repeat mismatches at 1.4; 0/31 monotonicity violations across 0.8–2.0 | First option, first 31 requests, one level 8 world; not proof for all prices or requests |
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

This is not realised margin or an end-to-end comparison: it ignores how our wins change the competitor, dealer trust and satisfaction, actual driver fees, cancellations and on-time performance. It also ignores choices among multiple quoted options. It is a single-world lead, not an improvement claim.

## Cost and failures

The first 31-request method check took 797 HTTP calls. Before the week, a rough nine-copy, 1,000-request estimate was 30,000 calls and 510 seconds at 17 ms per call, excluding server processing and additional options. The all-option week actually took approximately 57,000 calls and 27 minutes across the initial run and resume; copied event histories and later-day processing made the latency estimate optimistic. Its initial run stopped at request R00604 because the next-day one-cent quote lost. The targeted probe established this was a repeatable zero-positive-price case rather than a failed action. The script was fixed to represent it, and resumed with already saved option rows skipped. An initial launch also failed due to Python's script import path and another due to a zero-cent quote; both were corrected.

## Stint 1, condensed

One first-option fork probe was fixed and monotone across eight trials. A random-price grid found full-Monday midpoint estimates 1.648 (`t2-study-1`) and 1.459 (`dev-01`); estimates from the first 20–50 quotes were within about 0.05 of the same Monday fit, in sample. `t2-learning-v2` on ten dev weeks yielded −€204,983.18 and 61.9% weighted on time, 0/10 ranked, with starter intake; it does not isolate quote quality. The existing `LearningQuoter` is experimental and cannot rebuild its pending quotes from event-only replay. It has not been made production-ready by this scan.
