# Track 1: Intake and on-time

The best third-stint candidate is opt-in: `--set slack=1440 --set private=true --set queue_price=true --set win_price=true`. The main defaults are unchanged. The rules are: offer options with at least 24 hours of note-adjusted slack after driving; raise prices as unbooked work fills the queue; and adjust prices gently toward a 40% recent quote win rate.

| Third-stint version | Margin | On time | Orders | Worst week | Ranked |
|---|---:|---:|---:|---:|---:|
| `t1-stint3-baseline` | €43,815 | 98.0% | 1,107 | 95.9% | 10/10 |
| `t1-stint3-slack24-private` | €44,639 | 97.4% | 1,114 | 95.1% | 10/10 |
| `t1-stint3-slack24-no-private` | €43,212 | 99.1% | 1,029 | 96.8% | 10/10 |
| `t1-stint3-slack24-private72` | €42,827 | 98.3% | 1,062 | 95.1% | 10/10 |
| `t1-stint3-queue-price` | €47,493 | 97.4% | 1,284 | 95.6% | 10/10 |
| `t1-stint3-win-price` | €52,838 | 98.0% | 1,611 | 94.9% | 10/10 |
| `t1-stint3-regional` | €40,634 | 96.9% | 1,290 | 92.6% | 10/10 |

Regional compares against queue-price, not win-price; private72 compares against slack24-private. All are ten dev weeks. Restart loses the win-rate estimate, so the live runner should be checked for recovery behavior; the sample supports an improvement on dev seeds, not guaranteed performance on unseen weeks. Next investigate first-leg versus trade-in slack, weather disruptions, and restart-safe learning on independent study weeks. Offline checks: 21 passed. Changes outside the intake and policy are this findings file, its analysis script, and focused offline tests.

The intake limits unbooked orders plus quotes awaiting a decision to 15, and declines private-address requests and same-day options. It uses markup 1.7, all later options, opening fee 1.3 and six fee steps of 0.1 every 60 minutes. The limit is a conservative initial rule, not a measured capacity model.

| Label | Dev weeks | Margin | On time | Ranked |
|---|---:|---:|---:|---:|
| `t1-stint3-win-price` | 10 | €52,838 | 98.0% | 10/10 |
| `t1-stint3-queue-price` | 10 | €47,493 | 97.4% | 10/10 |
| `t1-stint3-regional` | 10 | €40,634 | 96.9% | 10/10 |
| `t1-stint3-baseline` | 10 | €43,815 | 98.0% | 10/10 |
| `t1-stint3-slack24-private` | 10 | €44,639 | 97.4% | 10/10 |
| `t1-stint3-slack24-private72` | 10 | €42,827 | 98.3% | 10/10 |
| `t1-stint3-slack24-no-private` | 10 | €43,212 | 99.1% | 10/10 |
| `t1-limit15-later-price16-fee11` | 10 | €37,221 | 95.3% | 9/10 |
| `t1-limit15-later-price16-fee13` | 10 | €12,114 | 96.2% | 10/10 |
| `t1-stint2-limit25-fee13` | 10 | €4,141 | 94.6% | 9/10 |
| `t1-stint2-limit15-sameday-fee13` | 10 | €22,092 | 90.8% | 7/10 |
| `t1-stint2-unlimited-later-fee13` | 10 | −€10,423 | 92.4% | 8/10 |
| `t1-stint2-no-private-fee13` | 10 | €15,455 | 97.9% | 10/10 |
| `t1-stint2-no-private-urgent25` | 10 | €11,889 | 97.9% | 10/10 |
| `t1-stint2-no-private-limit25` | 10 | €10,310 | 96.8% | 10/10 |
| `t1-stint2-no-private-markup18` | 10 | €19,787 | 98.2% | 10/10 |
| `t1-stint2-no-private-markup17` | 10 | €21,279 | 97.6% | 10/10 |
| `base` | 10 | −€689,088 | 45.1% | 0/10 |
| `t1-limit15-later-price16-fee15` | 10 | −€31,979 | 96.0% | 10/10 |
| `t1-price16-fee15` | 4 | −€16,953 | 86.2% | 1/4 |
| `t1-limit15-later-price16-fee15` (same four) | 4 | −€11,352 | 96.1% | 4/4 |

The full comparison against base improves margin by €657,109 and ranks every week, but still loses money. Minimum on-time share was 93.4%. The four-week price-only test failed to rank three weeks; it is only a lead. The queue and later-options changes were tested together, so their individual effects are unknown.

In progress: `t1-limit15-later-price16-fee11`, same policy with opening fee 1.1 and 0.1 steps every 60 minutes. This tests whether lower fees preserve on-time performance and improve margin.

The completed lower-fee comparison `t1-limit15-later-price16-fee11` made **€37,221**, 95.3% on time, but ranked **9/10**; dev-10 reached only 89.8%, and dev-07 92.7%. Against fee15 it gained €69,200 but lost one ranked week, so it is not kept. The intermediate fee test `t1-limit15-later-price16-fee13` is in progress: opening 1.3, step 0.1 every 60 minutes, six steps.

Stopped the intermediate-fee run at the 30-minute stint limit after three completed weeks; cleaned up both track slots. On the paired dev-01 through dev-03, fee13 made €3,863 at 96.3% on time, 3/3 ranked; fee15 lost €7,434 at 96.5%, 3/3 ranked. This is a lead only. Resume the same label for the remaining seven weeks before deciding whether to keep it. No changes outside intake and policy assembly were made.

## Third stint: saved-week evidence and experiments

The main default control `t1-stint3-baseline` made €43,815.45, 1,107 orders, 98.0% on time, worst 95.9%, ranked 10/10. The first test, `t1-stint3-slack24-private`, replaces the same-day ban with a 24-hour note-adjusted slack minimum and permits private addresses; it made €44,639.05, 1,114 orders, 97.4% on time, worst 95.1%, 10/10 ranked: +€823.60 over control, meeting the 93% floor. Kept as an opt-in candidate (`slack=1440 private=true`), because the shared main defaults are owned by the orchestrator. `t1-stint3-slack24-no-private` tests the same slack rule without private addresses: €43,212.02, 1,029 orders, 99.1% on time, worst 96.8%, 10/10 ranked; rejected because margin fell €603.43 against baseline. `t1-stint3-slack24-private72` with a 72-hour minimum for private requests made €42,827.23, 1,062 orders, 98.3% on time, worst 95.1%, 10/10 ranked; rejected versus the less restrictive candidate. `t1-stint3-queue-price` scales prices from 0.9 to 1.1 of the original markup as the queue fills: €47,493.18, 1,284 orders, 97.4% on time, worst 95.6%, 10/10 ranked. Kept as an opt-in candidate; it gained €2,854.13 over slack24-private. `t1-stint3-win-price` adds a smoothed recent win-rate adjustment around a 40% target: €52,837.55, 1,611 orders, 98.0% on time, worst 94.9%, 10/10 ranked, +€5,344.37; kept as opt-in. The win-rate state resets after a desk restart because quote actions are not in event history. `t1-stint3-regional` replaces national queue pressure with the number of unbooked orders and pending quotes within 30 km relative to the share of drivers living there, retaining the national hard limit: €40,633.63, 1,290 orders, 96.9% on time, worst 92.6%, 10/10 ranked. Rejected: below both the candidate margin and the 93% floor.

On 1,588 non-cancelled fee11 orders from the previous stint, computed retrospectively using the reader and response deadline as the decision time, on-time shares by slack were: under 12h 14/14 (100%, small sample), 12–24h 107/133 (80.5%), 24–48h 669/693 (96.5%), 48–72h 73/78 (93.6%), 72h+ 661/670 (98.7%). By first-leg drive: under 2h 605/612 (98.9%), 2–4h 429/443 (96.8%), 4–6h 319/333 (95.8%), 6h+ 171/200 (85.5%). Private orders were 160/189 (84.7%) versus 1,364/1,399 (97.5%) otherwise. Private orders with 72h+ slack were 71/71 on time, but this selected historical sample is not causal. The notes reader was not active in these weeks. Run `python3 -m tracks.t1.slack_analysis` to reproduce.

## Second stint: saved order analysis

For the ten fee11 weeks, the final snapshots contain 1,588 non-cancelled orders: 64 late, none undelivered, and 1,524 on time. Private pickup or delivery appears in 29/64 late orders versus 160/1,524 on-time orders; trade-ins in 7/64 versus 15/1,524; a note in 29/64 versus 681/1,524. Pickup towns with no resident driver account for 5/64 late versus 60/1,524 on time. A recorded failed visit occurred for 4/64 late versus 25/1,524 on time. These are associations, not proof of cause.

Dev-10 had 18 late of 177, seven with private addresses; its late pickup towns included Oulu and Kokkola (three each). Dev-07 had 13 late of 179, three with private addresses, including four pickups in Oulu. This suggests different failure modes; avoiding all private addresses alone cannot explain either week. Further investigation of booking drops, distance, deadline slack and daily conditions remains necessary.

The desk handles `deadline_close` by repricing open gigs with the urgent fee schedule, currently opening at 1.5 times typical and rising by 0.25 every 30 minutes to 2.5. It does not release booked drivers. A stronger schedule still needs a paired experiment.

Using each request's response deadline as the win time, median deadline slack was 1,875 minutes for late orders versus 4,460 for on-time orders. Eleven late orders and 96 on-time orders had a booking dropped; 43 late and 20 on-time orders received a deadline warning. Orders won Thursday contributed 26 late out of 488; Wednesday 17 out of 321. These days are not evidence of flu or snow without further event analysis. The warning is strongly associated with lateness but arrives after the intake decision.

Fee13 completed: €12,113.94, 1,648 orders, 96.2% on time, worst dev-07 93.2%, 10/10 ranked and all at least 92%. Kept as policy defaults against fee15, improving margin by €44,093 while meeting the floor.

Limit 25 at fee13: 1,831 orders, €4,141, 94.6% on time; worst dev-10 88.8%, 9/10 ranked. Rejected: more orders but lower margin and below the 92% floor.

Road distance, summing the legs, had median 519 km for late orders versus 235 km for on-time orders; 51/64 late and 572/1,524 on-time orders covered at least 300 km. Long lanes, private addresses and short slack overlap and need controlled tests before declining any of them.

Offering same-day with limit 15: €22,092, 2,259 orders, 90.8% on time, worst dev-10 87.1%, 7/10 ranked. Rejected: higher margin but misses the floor on multiple weeks.

Removing the limit while still declining same-day: −€10,423, 2,080 orders, 92.4% on time, worst dev-07 82.1%, 8/10 ranked. Rejected.

Declining private-address requests: €15,455, 1,573 orders, 97.9% on time, worst dev-07 95.0%, 10/10 ranked. Kept: +€3,341 over fee13 with every week above 92%.

Urgent opening 2.5 instead of 1.5 with no private orders: €11,889, 1,576 orders, 97.9% on time, worst dev-07 95.0%, 10/10 ranked. Rejected: margin fell €3,566 without improving the worst week.

No private orders, limit 25: €10,310, 1,716 orders, 96.8% on time, worst dev-10 92.1%, 10/10 ranked. Rejected: margin fell €5,145.

No private orders, markup 1.8: €19,787, 707 orders, 98.2% on time, worst dev-10 95.3%, 10/10 ranked. Kept: +€4,332 despite substantially fewer orders; this is a margin comparison, not an inference that higher prices always win.

No private orders, markup 1.7: €21,279, 1,099 orders, 97.6% on time, worst dev-07 95.2%, 10/10 ranked. Kept: +€1,492 over markup 1.8.

Remaining work: complete the limit and markup sweeps and the fee comparison under the kept policy; test dynamic, regional and selective same-day intake on all ten seeds. Further investigate snow, flu and the two difficult weeks. The current rule is a measured candidate, not a completed search for the maximum.

## Fourth stint: admission against the current mainline

`t1s4-base` reproduces €73,495.20 margin, 1,873 orders, 98.1% on time, worst 96.9%, 10/10 ranked. The order allocation report totals €74,163 because it excludes some account lines; use the runner's account score for comparisons. Of 1,873 orders, 36 were late or undelivered; those averaged −€4.6, while 91 lanes of at least 500 km averaged €114.8 despite 87.9% on time. Private orders averaged €58 across 68 orders, with 88.2% on time. These descriptive groups are not causal. The world runs until the following Wednesday 22:00; Friday is not the end of the world. Selective same-day and slack tests are in progress.

`t1s4-same360-30` admits same-day with at least 360 minutes after driving and 30 resident drivers within 30 km of pickup. It made €81,048.30, 2,177 orders, 96.6% on time, worst 92.4%, 10/10 ranked. Rejected against the 93% floor despite a €7,553 gain. The slack sweep is running.

`t1s4-slack720` made €76,581.20, 1,946 orders, 98.2% on time, worst 96.8%, 10/10 ranked. It gains €3,086 over baseline and wins 8/10 paired weeks, meeting the 93% floor. This is a candidate; 1080 and 2160 are in progress.

`t1s4-slack1080` made €74,881.59, 1,906 orders, 98.1% on time, worst 97.0%, 10/10 ranked. It gains €1,386 over baseline in 6/10 weeks, but trails slack720.

`t1s4-slack2160` made €46,763.52, 1,213 orders, 99.7% on time, worst 98.3%, 10/10 ranked. Rejected: too restrictive, €26,732 below baseline.

Baseline reveals contain 2,402 same-day options quoted at five times list, average list €74.32, and 1,219 next-day options at that decline price, average list €99.48. Reveal does not show competitor prices, so it cannot directly identify what those dealers would have paid. Three selective same-day variants are in progress.

`t1s4-same480-30` combines slack720 with same-day slack480 and at least 30 drivers near pickup. It made €80,187.99, 2,151 orders, 97.0% on time, worst 95.8%, 10/10 ranked; +€6,693 over baseline, higher in 8/10 weeks. It is the leading qualifying candidate. The combination changes both general and same-day slack; the margin gain cannot be attributed solely to same-day admission.

`t1s4-same360-80` combines slack720, same-day slack360 and 80 drivers within 30 km. It made €83,222.74, 2,201 orders, 97.6% on time, worst 94.5%, 10/10 ranked. It gains €9,728 over baseline and improves 9/10 weeks, but loses €2,329 on dev-07. This is the highest-margin qualifying candidate so far.

`t1s4-same480-80` made €81,361.49, 2,175 orders, 97.7% on time, worst 96.1%, 10/10 ranked. It gains €7,866 over baseline in 6/10 weeks, less margin but a higher worst week than same360-80.

Among baseline orders, 100 had negative allocated margin, totaling −€1,349.23; 23 were late or undelivered, 96 non-private, 99 next-day. This does not isolate a clean group to decline; allocation excludes some account lines.

`t1s4-morning20` adds a limit of 20 before noon to same360-80: €84,248.20, 2,211 orders, 97.6% on time, worst 95.7%, 10/10 ranked. Against same360-80 it gains €1,025 but improves only 5/10 weeks, so the incremental benefit is uncertain. `t1s4-morning10` makes €76,321.73, 2,066 orders, 97.9% on time, worst 96.5%, 10/10 ranked; rejected against same360-80.

`t1s4-long1440` raises minimum slack for non-same-day options on first-leg lanes of 500 km or more to 1,440 minutes, keeping same360-80 otherwise: €83,434.25, 2,209 orders, 97.5% on time, worst 94.2%, 10/10 ranked. Its €212 gain over same360-80 appears in only 4/10 weeks, so is noise; rejected as an additional rule. Long2160 is running.

`t1s4-long2160` made €80,931.29, 2,231 orders, 97.5% on time, worst 95.5%, 10/10 ranked. Rejected against same360-80. Both long-lane experimental parameters were removed after testing; the evidence does not justify an extra part.

`t1s4-same240-80` makes €81,040.06, 2,221 orders, 96.4% on time, worst 94.3%, 10/10 ranked. It falls €2,183 below same360-80 and is rejected in favor of that rule.

`t1s4-same360-150` makes €80,210.98, 2,157 orders, 97.4% on time, worst 94.5%, 10/10 ranked. It falls €3,012 below same360-80 with no worst-week improvement; rejected. Morning25 is in progress.

`t1s4-morning25` sets the morning limit to 25 on same360-80: €86,852.03, 2,257 orders, 97.3% on time, worst 95.7%, 10/10 ranked. It gains €13,356.83 over baseline and €2,603.83 over morning20, with 7 higher, 1 lower, 2 identical weeks. It is the highest-margin qualifying combination. Morning30 is in progress to check whether further increases help.

`t1s4-morning30` made €84,313.41, 2,228 orders, 96.9% on time, worst 92.6%, 10/10 ranked. Rejected: below the 93% floor and €2,539 below morning25. The best command is `SPREAD_TRACK=t1 bin/vps python3 -m harness.run --policy main --seeds dev --label t1s4-morning25 --set slack=720 --set same_day_slack=360 --set same_day_drivers=80 --set morning_limit=25`. The 25 threshold is a dev-set selection, not independent validation; the orchestrator should check holdouts. Next test rules using driver supply and time rather than a fixed morning limit, and assess robustness on independent study weeks. No ranking or holdout worlds were played.

## Fifth stint: shortage governor (in progress)

The five lowest `b9-same-rob` seeds are rob-18 90.1%, rob-17 92.4%, rob-14 93.2%, rob-11 96.2%, rob-10 96.5%. On Friday these first three have respectively 34, 30 and 18 `deadline_close` events and 12, 15 and 8 `gig_expired` events; rob-04, at 98.9%, has three warnings and one expiration on Friday. Warnings can repeat for an order and are symptoms, not independent late orders. The Thursday win cohort can already be exposed before Friday warnings. Flu and outage are unannounced, so this does not establish their cause; rob-18's snow forecast was for Tuesday, not Friday. The outage concerns competitor availability, not driver availability.

Started paired `t1s5-base` and `t1s5-warn3` on the 10 dev and five seeds above. The latter opts into declining private and same-day options after three deadline warnings in the preceding six hours. Results pending. Offline suite: 22 passed.

Completed paired results, margins in euros. The five on-time shares are rob-18, rob-17, rob-14, rob-11, rob-10 in that order.

| Label | Dev margin | Five margin | Worst of 15 | Five shares |
|---|---:|---:|---:|---|
| `t1s5-base` | 102,227.33 | 40,888.01 | 90.06% | 90.06, 92.43, 93.22, 96.20, 96.53% |
| `t1s5-warn3` | 99,912.81 | 39,373.81 | 92.24% | 93.99, 92.77, 92.24, 96.58, 96.53% |

The warning rule fails the 94% floor and the exploratory 92.5% tolerance on rob-14, despite helping rob-18. `t1s5-warn2` tests an earlier threshold; `t1s5-best-rob` checks the three-warning rule on all 20 rob seeds. Both are running.

Further tests in progress: `t1s5-warn2` reaches only 89.0% on rob-17 (not ranked), despite 94.0% on rob-18. `t1s5-drop3` uses three `gig_dropped` events in six hours instead of warnings, with the same restrictions; it reproduces rob-18 at 90.1% and thus fails there. Both still need complete paired totals. These deterministic changes alter subsequent driver decisions; the apparent threshold response is not monotonic.

| Label | Dev margin | Five margin | Worst of 15 | rob-18, rob-17, rob-14, rob-11, rob-10 |
|---|---:|---:|---:|---|
| `t1s5-warn2` | 97,221.91 | 39,446.78 | 88.98% | 93.99, 88.98, 93.10, 96.54, 97.67% |
| `t1s5-drop3` | 101,227.69 | 40,135.54 | 90.06% | 90.06, 94.26, 91.91, 96.65, 96.24% |

Both rejected: warn2 does not rank rob-17; drop3 misses the floor on rob-18 and rob-14. `t1s5-late5` is in progress: after 30 orders, use a 5% observed late share, including orders past deadline, to trigger the same restrictions. Offline checks 22 passed.

`t1s5-best-rob` (warn3) completed 20 rob weeks: €196,236.83, 5,258 orders, 97.0% aggregate on time, 20/20 ranked. Sorted shares: rob-14 92.24%, rob-17 92.77%, rob-18 93.99%, rob-05 96.25%, rob-10 96.53%, rob-11 96.58%, rob-12 96.76%, rob-08 97.05%, rob-06 97.40%, rob-13 97.40%, rob-20 97.45%, rob-19 97.60%, rob-07 97.62%, rob-09 97.77%, rob-02 97.78%, rob-16 98.26%, rob-15 98.40%, rob-01 98.54%, rob-03 98.68%, rob-04 98.95%. These include the five selected for testing, so the sample is not independent.

`t1s5-afternoon` declines requests after 15:00 when ready within three hours. It reached 94.4% on rob-18 but only 89.5% on rob-17, not ranked; complete totals pending. `t1s5-warn3-limit10` tests a queue limit of 10 while the warning rule is active; in progress.

| Label | Dev margin | Five margin | Worst of 15 | rob-18, rob-17, rob-14, rob-11, rob-10 |
|---|---:|---:|---:|---|
| `t1s5-afternoon` | 97,071.36 | 39,028.91 | 89.52% | 94.44, 89.52, 93.78, 97.14, 97.50% |

Rejected: it loses €5,155.97 on dev and fails to rank rob-17.

| Label | Dev margin | Five margin | Worst of 15 | rob-18, rob-17, rob-14, rob-11, rob-10 |
|---|---:|---:|---:|---|
| `t1s5-late5` | 102,643.57 | 41,115.72 | 91.98% | 91.98, 92.43, 93.22, 96.20, 96.53% |

The late-share governor adds €416.24 on dev and lifts rob-18, but leaves rob-17 and rob-14 unchanged. It fails the 94% target, as does dev-07 at 93.3%. Its signal often arrives after the vulnerable intake decisions.

| Label | Dev margin | Five margin | Worst of 15 | rob-18, rob-17, rob-14, rob-11, rob-10 |
|---|---:|---:|---:|---|
| `t1s5-warn3-limit10` | 91,491.72 | 36,941.40 | 89.47% | 93.59, 89.47, 95.15, 95.91, 98.68% |

Rejected: dev margin falls €10,735.61, and rob-17 does not rank. `t1s5-late3` tests the late-share trigger at 3%; pending.

| Label | Dev margin | Five margin | Worst of 15 | rob-18, rob-17, rob-14, rob-11, rob-10 |
|---|---:|---:|---:|---|
| `t1s5-late3` | 101,970.80 | 40,901.20 | 92.43% | 93.05, 92.43, 93.22, 96.20, 96.53% |

The 3% late-share rule has the highest minimum of the completed candidates but misses 94%; dev margin is €256.53 below baseline. Its late count uses the order deadline and timestamps, not ledger refunds, so private booked-hour deadlines may be missed. The 20-week check `t1s5-late3-rob` was started after this result, later than planned; the earlier `t1s5-best-rob` checked the then-leading warning rule.

`t1s5-late3-rob`: €199,499.83, 5,309 orders, 96.8% aggregate, 20/20 ranked. Sorted: rob-17 92.43%, rob-18 93.05%, rob-14 93.22%, rob-05 95.40%, rob-11 96.20%, rob-10 96.53%, rob-08 96.74%, rob-09 97.12%, rob-12 97.25%, rob-03 97.39%, rob-20 97.41%, rob-13 97.47%, rob-19 97.61%, rob-07 97.62%, rob-16 97.74%, rob-06 97.81%, rob-01 98.13%, rob-02 98.14%, rob-15 98.14%, rob-04 98.95%. The five shaped-on weeks are included; no candidate meets 94%. Next measure posting-to-booking delay and unbooked gig age before the Thursday cohort's decisions, and reconstruct late share from ledger refunds including private deadlines. No inference of flu or outage cause is established.

## More orders, same worst week, 14 Nov

Stint of 30 minutes (cut from 75). Baseline `b26-fix-wo` (mainline: limit 35, 45 before noon, patience 120).

**Where the week breaks.** `duedays.py` on `b26-fix-wo` (40 weeks): orders due Monday 5.5% late (127 orders), Tuesday 2.4%, Wednesday 2.8%, Thursday 2.4%, **Friday 4.7% (3,042 orders, the busiest day)**, after the week 2.1%. Friday collects Tuesday's within-3-days, Thursday's next-day and Friday's same-day options; Wednesday's within-3-days fall due after the weekend, so Saturday and Sunday hold almost nothing. `b27-limit40` raises Friday to 5.1% late and dev-07 to 90.8%: extra volume lands where it hurts.

**Peak load per due day** (`tracks/t1/dayload.py`, the most undelivered orders due on one day at any moment): Friday's peak ranges 20 to 89 orders a week, median about 52. It does **not** predict the bad weeks well: dev-07 (93.7%) peaks at 58, while dev-03 peaks at 89 with 96.2% and dev-05 at 72 with 98.5%. So a day cap alone is not a safety rule. It may still let a higher total limit add volume on the other days while holding Friday where the baseline keeps it.

**Switch `day_limit=<n>`** (off by default, `dispatch/intake.py` `LimitedIntake.room_on_day`, wired in `main.py`): an option is quoted only while its due day holds fewer than n undelivered orders. A quote awaiting its dealer counts as one order shared among the due days it was quoted for. Reason in one sentence: the drivers of one day can move only so many cars, so take the option that falls due on a day with room. With the switch off, `main` must equal `b26-fix-wo` (check `t1s9-off`, dev-01).

**Measured.** `t1s9-off` (switch off, dev-01): €8,742.09, 245 orders, 97.6%, equal to `b26-fix-wo` to the cent. `t1s9-l45-day60` on dev-07 only (the weakest dev week, a lead and not a finding): €10,704.07, 318 orders, 91.8% on time, against `b26-fix-wo` €11,396.91 / 301 / 93.7% and limit 45 without the cap (`b25-limit45-patience120`) €11,831.21 / 324 / 92.3%.

Why it did not help: on dev-07 Friday's peak stays at 56 to 58 undelivered orders under every setting, so a cap of 60 never bites on Friday; it bit only on orders due after the week. Orders due / late by due day on dev-07: baseline Fri 91/11, after the week 84/3; limit 45 Fri 93/10, after 103/6, Thu 47/5, Wed 50/2; limit 45 + cap after 97/7. **The extra volume from a higher limit lands mostly after the week and on Wednesday and Thursday, not on Friday, yet late orders rise on those days.** Friday's lateness is already there at limit 35 (11 of 91). So the weak week is a shortage of the shared driver pool, not one day being overfull, and a cap per due day is the wrong lever. Not adopted; the switch stays off.

Not played (stint cut to 30 minutes): `limit=45 day_limit=60`, `limit=40 day_limit=60`, `limit=35 day_limit=60` (what the cap costs on its own), each over 30 weeks paired with `b26-fix-wo`.

## Does booking slow down before the late orders? No usable early signal, 14 Nov

Stint of 30 minutes, offline only (no weeks played). Checks the previous stint's proposal: let the total limit follow driver supply, rising while new gigs book quickly and falling when booking slows. Script `tracks/t1/bookdelay.py` reads the 30 saved `b26-fix-wo` weeks (dev-01..10, rob-01..20) and gives, for each 12-hour block Monday to Friday: the median minutes from posting to booking of gigs booked in the block, the open gigs older than 2 hours at the block's end ("backlog"), and late orders by the block of their deadline.

**The median delay does not warn.** Correlation of its highest value up to Thursday noon with the week's on-time share: -0.16. dev-07 (93.7%) has medians of 7 to 37 minutes on Thursday and Friday; good weeks such as dev-04 (96.6%), dev-06 (97.2%), rob-04 (99.6%) have blocks of 600 to 880 minutes. Most gigs book quickly in every week; the median sees only them.

**The backlog warns weakly, and often too late or wrongly.** Correlation with on-time share: -0.26 for the highest backlog up to Thursday noon, -0.52 over the whole week (but that includes Friday, when the late orders are already happening). Of the three weakest weeks: rob-14 has a backlog of 23 by Tuesday night (an early warning); dev-07 climbs to 22 only on Thursday afternoon, the same block as its first late orders and half a day before Friday's 15; rob-08 never goes above 12. False alarms: dev-03 (22, 96.2%), rob-06 (20, 97.5%), dev-02 (15, 97.5%), rob-04 (12, 99.6%). Weeks 4 and 5 from the bottom (rob-17 94.9%, rob-10 95.0%) peak at 5 and 10, like good weeks. So a brake on the backlog would fire in good weeks and miss most bad ones, and a rise on a low backlog would raise the limit in rob-08, rob-17 and rob-10, weeks that are already short. Together with the fifth stint's shortage governor (warnings and drops), which also did not help, this says the week's shortage cannot be read early enough from booking speed. **Not built; step 2 skipped as the brief asked.**

**Where the late orders come from.** The orders that end up late, in the 7 weeks below 95.5% (117 late orders) against the other 23 (187): median minutes from the order's first post to its final booking 594 against 187; median minutes from that booking to the deadline 119 against 1,598; posted more than once (dropped or withdrawn, then reposted) 75% against 53%; booked with under 4 hours to the deadline 51% against 30%. In the weak weeks the late orders are a tail of single gigs that do not find a driver until the last two hours, often after a drop, while the median gig books as fast as in good weeks. That is a question for the fee schedule and the repairs (track 3: how fast a gig's fee rises as its deadline nears, and what happens after a drop), not for how much work the intake takes.
