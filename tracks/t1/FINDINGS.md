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

## Far orders hold less of the queue (`queue_hours`), 14 Nov

Stint of 30 minutes. Track 3 found that keeping gigs open longer costs orders through the intake limit. The other way round: an order whose last pickup is far away is not yet a risk.

**Switch `queue_hours=<h>`, `queue_far=<f>`** (off by default; `dispatch/intake.py` `unbooked`, used by `LimitedIntake.admit` and `ProfitQuoter.waiting`, wired in `main.py`). Rule in one sentence: an unbooked order whose last pickup is more than h hours away holds only f of a place in the queue (default f = 0). Hours are clock hours from now to the order's `lastPickupAt`. At winning, the time to last pickup is 22 h at the 10th percentile, 32 h median, 55 h at the 75th (one `b26` week, 176 orders).

**Baseline** `t1s11-base` (current mainline, repairs windows+orphans+calm), 30 weeks dev + rob-01..20: €371,614.02, 8,420 orders, 96.97% on time, 30/30 ranked; lowest dev-07 93.7%, rob-08 94.8%, rob-17 94.9%. `t1s11-off` (switch off, dev-01): €8,764.79, 246 orders, 97.6%, equal to the baseline to the cent.

**`t1s11-q36`** (`queue_hours=36`): €372,777.62 (**+€1,163.60**), 8,762 orders (+342, +4%), **96.37%** on time, 30/30 ranked, 14/30 weeks higher; lowest dev-07 **91.0%**, rob-18 91.8%, rob-17 92.6%. The intake takes the extra orders, but they cost about as much in late refunds and higher fees as they earn, and they push the weak weeks toward the 90% line. Same pattern as raising the limit (`b27-limit40`): more volume, about the same margin, a thinner worst week. Not adopted.

**`t1s11-q48`** (`queue_hours=48`): €373,119.48 (**+€1,505.46**), 8,728 orders (+308), **96.37%** on time, 30/30 ranked, 15/30 weeks higher; lowest rob-18 **91.8%**, dev-07 91.9%, rob-17 92.0%. Milder than 36 h in orders but the same loss of on-time share; the gain is 0.4% of margin, within the spread of a coin flip (15/30 weeks higher).

**Verdict.** Not adopted; the switch stays off. The limit binds on volume the drivers cannot move on time even when the pickup is two days away: the extra orders land in the same short driver pool (see "More orders, same worst week"). Every lever that adds volume so far (limit 40/45, day cap, now far orders) buys about +€1-2k over 30 weeks at the price of 2 points in the weakest week. Untested: a fraction (`queue_far=0.5`), and pairing `queue_hours` with a lower limit (e.g. `limit=32 queue_hours=48`) to keep total volume equal and only shift its mix toward far orders.

## The ceiling, 14 Nov

Stint of 30 minutes. Question: is our limit our delivery or our caution? Make the system win far more orders and see where it breaks. Dev seeds only, so this is a screen, not a finding. Group tables: `python3 tracks/t1/ceiling.py <label> ...` (new script; the groups come from `harness.orders` plus bundled or alone).

| label | settings | orders | margin | on time | ranked | lowest weeks |
|---|---|---|---|---|---|---|
| `t1s11-base` | mainline (limit 35, 45 before noon, car 1.1) | 2,879 | €127,567 | 96.8% | 10/10 | dev-07 93.7% |
| `t1s13-wide` | limit 55, morning 65, car 0.95 | 3,673 (+28%) | €124,922 | 94.8% | 9/10 | dev-07 **87.5%**, dev-10 91.6%, dev-08 94.1% |
| `t1s13-flood` | limit 80, morning 90, car 0.8 | 4,453 (+55%) | €103,440 | 91.8% | 8/10 | dev-07 **83.4%**, dev-10 **86.6%**, dev-03 92.5% |

**The orders are there.** Flood wins 370 to 506 a week (median about 450), which is the top teams' volume. So intake caution, not demand, keeps us at 300. Note that a flood week at 92.5 to 93.8% on time with 450 orders is what the board shows as about 97% for the top teams. They deliver it; we do not.

**Where the money goes in the flood** (€ per order, base → flood): price/list 1.55 → 1.41 (the cheaper quote), fee/typical 1.02 → **1.09** (the same driver pool, asked for more, costs more), refunds €1.8 → **€6.8**. Margin per order €44.3 → €23.4. The loss is spread across every group, so about half of it is price and fee, not lateness alone.

**What breaks, by group** (on time and total margin, base → flood):

- Lane length: under 100 km 98.1% → 94.6%, €21.3k → €18.3k; 100-200 km 97.2 → 95.3%, €31.2k → €31.4k; 200-300 km 96.8 → 94.3%, €22.8k → €23.2k; **300-500 km 96.1 → 88.2%, €35.6k → €28.2k; 500 km and more 88.2 → 72.3%, €16.8k → €3.0k** (refunds €51 per order).
- **Private address**: 81.1 → 75.9%, €6.0k → €3.1k (refund €24 per order, fee 1.44 times typical).
- Drivers living near the pickup or the delivery: little difference. P+D+ 93.0%, P-D+ 94.3%, P+D- 91.0%, P-D- 89.7%. Few drivers near the delivery (under 10) is the weakest (89.1%), but not enough to build a rule on.
- Option: same day 92.0%, next day 91.3%, within 3 days 98.0% (205 orders, €35.5 each: the safest and best-paid car in the flood).
- Day the request arrived: Monday holds up (1,122 orders, 93.6%, the same €28k as base from 675 orders); Wednesday to Friday fall to 90-91%.
- Bundled or alone: about the same (92.2% / 91.4%). Bundling rises from 49% to 56% of cars, on its own.
- Why late (`latecause.py`): in the flood 199 of 356 late orders had **no driver until the deadline warning**. The pool runs out.

`t1s13-wide` shows the same shape, milder. Lanes under 300 km stay 96-97% on time and add €2.9k; 300-500 km fall to 92.5% and over 500 km to 79.2% (−€4.0k); private addresses 77.6%.

**Reading.** Both limits bind. Caution (the intake cap) holds back about 50% more orders that dealers will give us. Delivery breaks first on long lanes (300 km and more) and on private addresses: those cars use a whole driver-day, find a driver late, and pay refunds. Short lanes without a private address stay cheap and on time even in a flood.

**Rule, built behind a switch** (`safe_limit=<n>`, off by default; `LimitedIntake.safe` in `dispatch/intake.py`, wired in `main.py`). Past the usual limit and up to n waiting orders, quote only a car with no private address, a lane under `safe_km` (300) and at least `safe_near` drivers living near the pickup (0 here, since the screen shows that this hardly matters). Reason in one sentence: the drivers can take many more short cars, but not more long ones. Prices stay at car 1.1, so only volume changes.

**Screens of the rule** (10 dev weeks, against `t1s11-base` €127,567 / 2,879 / 96.8% / 10 of 10):

- `t1s13-off` (switch off, dev-01): €8,764.79, 246 orders, 97.6%, the same as the baseline to the cent.
- `t1s13-safe80` (`safe_limit=80 safe_km=300 safe_near=0`): €126,673.66, 2,889 orders, 97.0%, 10 of 10 ranked, 1 of 10 weeks higher. **The room hardly fills.** The quoter's queue charge (`ProfitQuoter.prices`: 0.3 list prices times fullness², fullness = unbooked / `limit`) is at its full 0.3 by the time the intake limit binds. So a safe car past the limit gets a quote 0.3 list prices higher and loses. *Finding: much of our caution is the queue charge, not the intake cap.* That is why `wide` and `flood`, which raise the quoter's `limit` too, won far more.
- `t1s13-safe80q` (the same, plus a safe car's charge reads its fullness against `safe_limit` instead of `limit`; `dispatch/pricing.py`, only when the switch is on): **€129,101.16 (+€1,534), 2,989 orders (+110), 97.0% on time, 10 of 10 ranked, 5 of 10 weeks higher; lowest dev-07 94.3% (base 93.7%).** By group: lanes under 300 km +€4.0k (+130 orders, 97.3 to 97.8% on time), lanes of 300 km and more −€1.8k (−20 orders, which the short cars push out of the queue). A lead, not a finding: +1.2% of margin, 5 of 10 weeks.

- `t1s13-safe80q-car95` (the same plus `car=0.95` for every car): €128,473.04 (+€906), **3,640 orders (+26%)**, 95.5% on time, 10 of 10 ranked; lowest dev-08 93.3%, dev-10 93.6%, dev-07 93.9%. It has about the volume of `wide` (3,673) at €3.5k more margin, and it keeps all 10 weeks ranked where `wide` loses dev-07 (87.5%). The cheaper price is spent on every lane, so long lanes come back: over 500 km 201 orders at 83.1%, private addresses 147 at 76.9%. The next step is therefore car 0.95 for safe cars only.

(Group totals from `ceiling.py` differ a little from the runner's totals, because `harness.orders` drops cancelled orders.)

**Next.** (1) Play `safe80q` on the 20 rob seeds against `t1s11-base` before anyone adopts it. (2) Volume is still about 300 a week: the brake is price (car 1.1 plus the queue charge), not room. The next lever is pricing safe cars like the flood (car 0.8 to 0.95 for safe cars only) and quoting long lanes and private addresses higher (or not at all) once the queue holds 35. That keeps the flood's short-lane volume (95% on time) without its 72% long lanes. (3) Over 500 km is 88% on time even in the baseline, with €13 of refunds per order. A separate stricter limit for those lanes is worth a screen.

## Pricing the late allowance, 14 Nov

Stint of 30 minutes. Question: can prices, not a hard queue limit, decide how much work to take?

**Rule** (`barrier=<euros>`, off by default; `ProfitQuoter.room` in `dispatch/pricing.py`, wired in `dispatch/policies/main.py`). Reason in one sentence: *a car should pay for the room it uses under the 90% on-time minimum and for the drivers it takes from the cars already waiting.* With the switch on, a car's cost in the quoter is its expected fee, plus its own late cost (`late * late_risk`, as before), plus two prices that replace the queue charge `queue * waiting²`:

- the **late allowance**: `barrier * (late_share / allowance)^4` euros. `late_share` = (orders late so far + the expected late among the open orders, from `fees.late_risk`) / max(orders, `floor_orders` = 100); `allowance` = 6%. It costs nothing while the week is far below the line and climbs steeply near it: at a 3% share it is 1/16 of `barrier`, at 6% the whole `barrier`.
- the **crowd**: `crowd` (€0.50) times the number of orders without a booked driver. This is the marginal harm of one more car when the total harm grows with the square of the queue, like the old charge, but in euros, not as a fraction of the list price, and with no cap.

The intake's hard limit goes up to `barrier_limit` (120, morning too), so the prices decide volume and the limit only stops a runaway. The rule keeps no state of its own: it reads the desk's orders after a restart (late risks are cached only to save time).

**Screens** (10 dev weeks, level 8):

| label | settings | orders/week | €/car | margin | on time | ranked | lowest weeks |
|---|---|---|---|---|---|---|---|
| `t1s11-base` | mainline | 288 | 44.1 | €126,921.82 | 96.8% | 10/10 | dev-07 93.7%, dev-10 95.3%, dev-08 96.0% |
| `t1s13-safe80q-car95` | safe_limit 80, car 0.95 | 364 | 35.3 | €128,473.04 | 95.5% | 10/10 | dev-08 93.3%, dev-10 93.6%, dev-07 93.9% |
| `t1s14-b150` | barrier 150, crowd 0.5 | 256 | 48.0 | €122,869.13 | 96.7% | 10/10 | dev-07 **90.8%**, dev-10 95.2%, dev-08 95.5% |
| `t1s14-b300` | barrier 300, crowd 0.5 | 220 | 49.7 | €109,619.64 | 96.1% | **9/10** | dev-07 **89.4%**, dev-10 94.7%, dev-03 95.0% |
| `t1s14-b150-c02` | barrier 150, crowd 0.2 | 271 | 45.6 | €123,479.65 | 96.6% | 10/10 | dev-07 94.3%, dev-08 95.0%, dev-10 95.9% |

`t1s14-off` (switch off, dev-01): €8,764.79, 246 orders, 97.6%, the same as the baseline to the cent.

**Result: worse on every count. Prices built this way take less work, not more.** All three settings win fewer orders than the base (256, 220 and 271 a week against 288) at a higher margin per car, and lose €3.4k to €17.3k in total. A higher barrier cuts volume further and still does not protect dev-07 (89.4%, unranked at 300).

**Why** (groups from `ceiling.py`, `b150` against the base):

- **The flat price falls on the wrong cars.** Lanes under 100 km lose 223 of 1,031 orders (−€1.8k); lanes of 300 km and more hold (650 → 645) and get later (over 500 km 88.2% → 84.2%). A price in euros per car is a large share of a cheap short car's price and a small share of a long one's, which is the opposite of what the ceiling screen found: short lanes are the safe volume.
- **The allowance price, not the crowd, binds.** Lowering `crowd` from 0.5 to 0.2 adds only 15 orders a week (dev-01: 220 → 219). The late share counts every open order at its `late_risk`, and that sum sits near the 6% allowance for much of the week, so the price is often near its full value long before any real lateness.
- **It reacts too late where it matters.** On dev-07 the week's lateness shows only once deadlines pass, by which time the cars are sold. A price on the realised share cannot protect a week whose pool runs out on Thursday.

**Reading.** The idea of a price for room is sound, but the price must be per unit of risk, not per car: a car should pay `room_price × its own late_risk`, so that a short lane with no private address (risk about 2%) pays almost nothing and a lane of 500 km with a private address pays its full share. That is the same split the `safe_limit` rule makes by hand, written as a price. The allowance share should count realised lateness only (or the open orders' risk discounted heavily), because the risk model is a prior, not a forecast for this week.

**Next.** (1) Scale the allowance price by the car's own `late_risk` (one line in `ProfitQuoter.room`: return the barrier part separately and multiply it by `risk / mean_risk`), and count only realised late plus open orders past their warning. Screen `barrier=150` and `barrier=400` against `t1s13-safe80q-car95`. (2) If that still fails to beat `safe80q-car95`, keep the hand rule: it reads the week through the queue and the lane, and it wins.

## The bad week, 14 Nov

Stint of 30 minutes. Question: why did `t1s13-safe80q-car95` lose two rob weeks, and what rule would have kept them ranked? Script: `python3 tracks/t1/badweek.py <seed> <label> ...` (new; per seed: late cars by lane, private address, option, day won, unbooked queue at the win, late cause, due day, queue at 12:00 and 18:00).

**The bad weeks.** **rob-18**: 83.6% on time, 269 orders, 44 late (base `t1s11-base`: 95.1%, 184 orders, 9 late). **rob-17**: 90.7%, 355 orders, 33 late (base 94.9%, 293, 15 late).

**What broke them: Friday, not the safe room.**

- **The queue never passed 35** in either week (the most unbooked cars at any win was 34). The safe cars past the limit did not cause it. The extra volume came from the cheaper price (`car=0.95`), on every day.
- **41 of 44 late cars in rob-18 were due on Friday** (rob-17: 28 of 33). Short lanes went late too (under 100 km: 24 of 92 late), so lane length and private address do not explain it (6 private cars, 2 late).
- **A wave of drops at Friday 00:00 to 02:00.** In rob-18, 20 Friday gigs booked on Thursday afternoon and evening were given back between 00:02 and 00:50 (base: 10). rob-17: 20 (base 19); rob-14 also shows a wave (11; base 8). The rest of the week sees 0 to 3 night drops. No forecast announces it, and the drivers do not book other gigs (it is not a better offer, and the dropped gigs' fees, 0.95 times typical, are like the kept ones). No driver reads the re-posted gig before 07:00, so a car due Friday loses half its last day. Late causes in rob-18: dropped 24, no driver until the warning 18, driven late 2.
- **Why the base survives:** it holds fewer Friday cars overnight (74 due Friday against 98), so the same wave hits fewer of them.

**Rules screened** (on top of `t1s13-safe80q-car95`; rob-17, rob-18 and the 10 dev seeds):

| label | rule | dev margin | dev orders | dev on time | rob-18 | rob-17 |
|---|---|---|---|---|---|---|
| `t1s13-safe80q-car95` | (reference) | €128,473.04 | 3,640 | 95.5% | 83.6%, €7,373 **unranked** | 90.7%, €10,766 |
| `t1s15-day70` | `day_limit=70` (existing switch, first play) | €125,862.82 | 3,595 | 95.7% | 83.6%, €7,373 (never binds) | 92.2%, €10,333 |
| `t1s15-day55` | `day_limit=55` (rob only) | | | | 88.6%, €7,236 | 93.6%, €10,224 |
| `t1s15-end110` | **`end_car=1.1`** | €126,099.65 | 3,522 | 96.0% | **93.5%, €8,024** | 92.0%, €11,693 |
| `t1s15-end102` | `end_car=1.02` | €125,619.32 | 3,572 | 95.5% | 90.7%, €8,391 | 92.7%, €12,026 |

`t1s15-off` (switch off, dev-01): €8,764.79, 246 orders, 97.6%, the same as `t1s11-base`. All dev weeks are ranked in every row.

**New switch `end_car=<x>`** (off by default; `ProfitQuoter.prices` in `dispatch/pricing.py`, `PROFIT` in `main.py`). An option due on Friday is priced with fee multiplier `end_car` instead of `car`. Reason in one sentence: *a car due Friday has no working day after it to recover a drop, and Friday is when the drops come.* Prices for other days stay at `car=0.95`, so the volume stays (3,522 against 3,640 orders on dev).

**Reading.**

- A per-day cap (`day_limit`) is the wrong tool. No fixed count separates the weeks (rob-18 peaks at 68 undelivered orders due on one day at 84%, rob-03 at 68 at 99%), and 55 removed only 5 orders from rob-18 yet moved it 5 points: **the week is fragile**, decided by which gigs the drivers hold overnight before the wave.
- `end_car=1.1` keeps both bad weeks ranked and earns more on them (+€651, +€927). On the dev weeks it costs €2,373 (−1.8%). The 12-week total is €795 lower, for an unranked week turned into a ranked one.
- **Caution: the dev differences are within noise.** `end102` sits closer to the reference than `end110` but loses more on dev (−€2,854). A re-priced week replays differently, so ±€2.5k over 10 weeks is not a finding. The gain on rob-18 and rob-17 is two weeks: a lead.

**Next.** (1) Play `end_car=1.1` on the other 18 rob seeds against `t1s13-safe80q-car95` (30 weeks in all, about 9 minutes on two slots). Adopt it only if no week drops out and the 30-week total stays within about €1.5k. (2) A cheaper fix belongs to fees and the desk, not intake: from Thursday evening, book Friday gigs with drivers of few drops, or re-raise dropped Friday gigs at 07:00 sharp, so that the morning's first look sees a fee that books. (3) The risk-weighted room price was not built: the bad week's late cars were short, safe lanes, so a price per unit of lane risk would not have caught them.

## The floor under the learned cost model, 14 Nov (t1s16)

Stint of 30 minutes on mainline `b37-fee3` (fee_model=3, flat fees, safe_limit=80, car=0.95). New scripts: `tracks/t1/timeline.py <seed> <label>` (each late car's story: posts, bookings, drops, views, reprices) and `tracks/t1/dropwait.py <label>` (dropped cars: late or not, last day or earlier, views while open after the drop).

**The lowest weeks are no longer a Friday wave.** rob-18 (92.0%, 21 late): 17 late cars due Friday, 14 of them won on Thursday; causes dropped 10, no driver until the warning 8, driven late 3. dev-01 (94.0%, 21 late): 18 of the 21 late cars were due on **Wednesday**; causes dropped 9, no driver until the warning 11. The queue never passed 35 in either week.

**Mechanism: a dropped flat-fee gig is stuck at its booked fee.** The mainline has no `drops` repair, so a dropped gig comes back with its old schedule, whose steps have all started: under flat fees that is the fee it was booked at, with no later steps. A car dropped inside its last day has no flat look-again step ahead, so it waits at that fee until the deadline warning (3 hours before its last pickup) starts the urgent ladder. Example, dev-01 R00383 (369 km, last pickup Wed): booked Tue 15:30, dropped Wed 00:30, then **viewed 50 times from 07:12 to 10:20 at the old fee and never booked**, urgent at 10:27, late.

Over the 30 dev and rob weeks of `b37-fee3`: 358 late cars, 103 of them dropped (29%). 94 were dropped in their last 24 hours, with **87 views each** while open after the drop. Dropped cars that still arrived on time had 12 views each (lastday 848 cars) and 15 (earlier). The drivers look at the gig and pass on it, so the fee is too low.

**Rule `fee_flat_drop=1`** (off by default; new `Desk.last_day_drop` on `gig_dropped`, parameter in `MeasuredFees`, `FEES` in `main.py`; 17 lines of `desk.py`, a small change to the desk): a car dropped inside its last `flat_last` minutes (24 h) comes back at the top of the fee schedule a new post would get (the model's fee plus one `flat_step`), not at the booked fee. Reason in one sentence: *a car dropped in its last day has no look-again step left, so it gets that step at once instead of at the warning.*

**Checks.** Switch off: `t1s16-off2` dev-01 €9,956.48, 352 orders, 94.0%, the same as `b37-fee3` to the cent. (A first try, `t1s16-drop`, hooked the rule into `after_drop`, which the mainline never calls because it has no `drops` repair. It reproduced `b37-fee3` exactly and was stopped after 2 weeks.)

**Screen** `t1s16-drop2` (`fee_flat_drop=1`) against `b37-fee3`, 10 dev seeds plus rob-17 and rob-18:

| | margin (12 weeks) | orders/week | 3 lowest weeks |
|---|---|---|---|
| `b37-fee3` | €167,106.65 | 377.3 | rob-18 92.0%, dev-01 94.0%, dev-09 95.2% |
| `t1s16-drop2` | €169,861.46 | 380.0 | rob-18 91.5%, dev-01 94.4%, dev-09 95.7% |

**+€2,754.81 over 12 weeks (dev only +€2,687.83), 10 of 12 weeks ahead**, all ranked, 4,560 orders against 4,527. dev-05 95.3% → 97.2%, rob-17 95.4% → 96.3%. Behind: dev-03 −€398 and rob-18 −€158 (92.0% → 91.5%, 22 late against 21).

**What it did to the drops** (`dropwait.py`, the same 12 seeds): late cars dropped in their last day 56 → 52, views per such car 90 → 79. The rule helps a little, but the drivers still look and pass: one flat step does not book a car that has been dropped. **The floor did not rise.** rob-18's late cars are still Friday cars (18 of 22) dropped on Friday itself, for example R00524 (64 km, dropped Fri 13:59, warned at 16:14) and R00662 (dropped Fri 00:54).

**Reading.** A small, consistent gain in money and volume. That is a lead (12 weeks), not a floor fix. The floor needs a stronger answer for a drop inside the last day than one more flat step, such as the urgent ladder at once (treat a last-day drop like a deadline warning) or a direct offer (`offers=drops`).

**The other 18 rob seeds** (same label `t1s16-drop2`): all ranked. Paired with `b37-fee3` on the 29 weeks both labels hold (10 dev and 19 rob; one rob seed is missing from `b37-fee3`'s index): **+€2,462.11 (€432,598.79 against €430,136.68), 18 of 29 weeks ahead, 392.4 against 391.5 orders/week**. The rob weeks alone come to −€225.72. The 3 lowest weeks: `b37-fee3` rob-18 92.0%, dev-01 94.0%, rob-04 94.7%; `t1s16-drop2` rob-18 91.5%, dev-01 94.4%, rob-04 94.7%.

**Verdict: neutral.** About +€85 a week, which is noise; no change in volume; the floor did not move. Not recommended for the mainline. Keep the switch for the next step: on a last-day drop, start the urgent ladder at once (`raise_fees` at the drop) instead of one flat step, since 79 to 90 looks per dropped late car say the fee is far below what that driver pool takes.

## Stronger answers to a last-day drop, 14 Nov (t1s17)

Stint of 30 minutes on `b37-fee3`. Two more values of the same switch (`fee_flat_drop`, off by default; `Desk.last_day_drop`, plus a few lines in `Desk.raise_fees` so the later deadline warning never lowers a fee a drop already set: a small desk change):

- **A, `fee_flat_drop=2`**: a car dropped in its last 24 h gets the urgent ladder at once (1.5× typical, +0.25× every 30 min, up to 2.5×), the ladder the deadline warning would give it 3 h before its last pickup.
- **B, `fee_flat_drop=3`**: one fee on the urgent ladder's range, set by the time left: 1.5× typical with 24 h left, up to 2.5× at the last pickup.

**Off check.** `main[fee_flat_drop=0]@d7b9ffa` dev-01 €9,956.48, 352 orders, 94.0%: the same as `b37-fee3` to the cent.

**Screen**, 10 dev seeds plus rob-04, rob-17 and rob-18, paired with `b37-fee3`:

| label | margin (13 weeks) | Δ vs b37-fee3 | weeks ahead | orders/week | 3 lowest weeks | late cars dropped in last day |
|---|---|---|---|---|---|---|
| `b37-fee3` | €179,916 | – | – | 377.2 | rob-18 92.0%, dev-01 94.0%, rob-04 94.7% | 57 (181 late in all) |
| `main[fee_flat_drop=2]@d7b9ffa` (A) | €173,944 | **−€5,973** | 3/13 | 378.5 | rob-18 93.4%, dev-01 93.8%, rob-04 94.7% | 42 (177) |
| `main[fee_flat_drop=3]@d7b9ffa` (B) | €175,030 | **−€4,887** | 2/13 | 379.2 | rob-18 93.0%, dev-01 94.0%, dev-10 94.6% | 51 (174) |

All weeks ranked. Views per late last-day-drop car: 91 (b37-fee3), 77 (A), 79 (B).

**Reading.** A higher fee for a last-day drop works in the expected direction: A cuts the late dropped cars by a quarter (57 → 42) and lifts the lowest week, rob-18, from 92.0% to 93.4%. But it costs more than it earns. About €450 a week goes on the fees of the roughly 30 dropped cars a week that would have booked anyway (on-time last-day drops are 28 a week), and saving about one late car a week returns far less. B is cheaper on the fees but saves fewer late cars. Neither moved total late cars by much (181 → 177 / 174), because the drop cars that A saves are partly replaced by others.

**Verdict: neither is recommended.** The floor rises by 1 to 1.5 points only on rob-18 and costs €375 to €460 a week. A last-day drop is better left to the deadline warning under the mainline. Variant 1 (one flat step, t1s16) is still the only even-money version. A next step, if any: raise only the drops that drivers keep passing on (for example after N views without a booking), not every last-day drop. The view count tells late cars (87 views) from on-time cars (12) apart.
