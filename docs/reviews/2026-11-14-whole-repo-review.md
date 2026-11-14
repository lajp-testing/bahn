# Whole-repository review, 14 November 2026

Scope: `dispatch/`, `harness/`, `bin/`, `tracks/` and the findings files, read against `docs/kit/`. No weeks were played and no code was changed.

**Data used.** This checkout has no `data/runs/`. The evidence below comes from what is here:

- five ranking weeks of season 3 (`data/board/season-3-level-8/`, 5,176 requests, 749 orders, played with the mainline of Friday evening);
- the six no-win scans (`tracks/t2/scan-*.jsonl`, 6,139 switching prices);
- the direct-offer study files (`tracks/t5/*.jsonl`).

The board weeks are an older policy, so their counts are leads. Each mechanism below is checked against the current code.

## Summary

| # | Finding | Kind | Evidence |
|---|---|---|---|
| 1 | A gig that expires is posted again with the pickup window that just ended, the world refuses it, and the order is never posted again | bug | One order in 749: undelivered, −€729.60, 21% of that week's margin. Reproduced on the current code |
| 2 | A refused post of a single car has no fallback | bug | Same order; `read_results` handles bundles and withdrawals only |
| 3 | After `lastPickupAt` a gig cannot be booked, and the desk waits hours for `gig_expired` | missed | 3 of 4 such cars booked 7 to 32 minutes after the late repost, at 1.5 to 1.75 times typical, having found nobody at up to 2.5 times |
| 4 | A dropped gig comes back at the top of its fee ladder | missed | 74 of 76 rebooked drops paid the top step: 1.40 times typical against 1.19 before the drop |
| 5 | Every `deadline_close` restarts the urgent ladder at 1.5 times, also after `fee_early` has raised it | bug | Code; 5 of 6 warned orders got a second warning. It confounds the `fee_early` results |
| 6 | Direct offers were written off with offers below any fee the gigs booked at | missed | Offers at 0.5 to 1.0 times typical; the same gigs booked at 1.20 to 1.75 |
| 7 | The intake counts every quote awaiting a decision as a won order | missed | Median 5 to 6 requests pending, 10 to 12 at the 90th percentile, against a limit of 25; about 28% win |
| 8 | The price curve peaks at far more orders than the mainline wins | missed | Scans: a flat 1.4 times list wins 331 to 489 orders a week; the mainline wins about 270 to 290 |
| 9 | The final depends on hand-typed flags | robustness | `dispatch.live` defaults to the kit starter; `main` defaults to no bundles and fee model 1 |
| 10 | Trust investment (`invest`) is in the code and was never measured | missed | D01 sends 25 to 32% of requests and reached a count of 25 on Wednesday at the earliest |

## 1. An expired gig is posted again with an ended window, then never again

`dispatch/notes.py:205`, `dispatch/desk.py:361`, `dispatch/desk.py:202`

When a note gives a later ready time, `ReadNotes.plan` gives the pickup the window `{from: ready, to: the order's pickup window end}`. When that gig expires at the window's end, `repost` calls `again`, which plans the same window. `without_windows` drops a window only when `to < now`, and here `to == now`. The world refuses a gig with an ended window.

Board run 4, order R00324 (Espoo to Rovaniemi, €364.80, note "Voi noutaa huomenna klo 12.00 alkaen"):

- posted Tuesday 15:04 with the pickup window 3600 to 5520, viewed 209 times, never booked;
- `gig_expired` at 5520, and the week holds no second gig for the order;
- `undelivered_penalty` of −€729.60 at the end.

All nine other expired gigs in the five weeks were posted again. This was the only one with a ready-time window that ends at the order's window. Feeding the same request, win and expiry to the current `main` desk gives a repost with `"window": {"from": 3600, "to": 5520}` at minute 5520.

34 of 758 gigs (4.5%) have this window shape. One such order costs about three times its price and counts as late.

Fix: drop a window when `to <= now`, and in `plan` give no ready-time window that has ended.

## 2. A refused post of one car leaves the order without a gig

`dispatch/desk.py:323`

`read_results` records a refusal, and acts only on a refused bundle and a refused withdrawal. A refused post of one car is forgotten. `raise_fees` then finds no gig, and only `rejoin` posts orders without a gig. Finding 1 is one way in; any other refusal ends the same way.

Fix: in `tick`, post without windows every undelivered order that has no gig and no post in the outbox.

## 3. A car that is certainly late waits for the world to expire its gig

`dispatch/desk.py:147`

RULES.md: a driver books only when they can reach every stop inside its window, so "a gig can get no driver before any of its windows ends". It also says a post without stop windows runs to the end of the world once no driver can be on time. So from `lastPickupAt` to the window's end the open gig is dead, and a new post would not be. The desk posts again only on `gig_expired`.

| Order | `lastPickupAt` | Expired | Dead time | After the repost |
|---|---|---|---|---|
| R00316 | Wed 13:35 | Wed 18:00 | 4.4 h | booked in 32 min at 1.75; 25% back |
| R00786 | Fri 13:22 | Fri 20:00 | 6.6 h | booked in 7 min at 1.50; 50% back |
| R00508 | Thu 13:35 | Thu 18:00 | 4.4 h | booked in 25 min at 1.50; 27.5 h late, 50% back |
| R00708 | Fri 10:34 | Fri 18:00 | 7.4 h | booked the next Monday at 2.50; 50% back |

Three of the four had found nobody at up to 2.5 times typical before the expiry. The four refunds were €515 in a week that made €9,486. R00508 was 3.5 hours over the 24-hour line, after 4.4 dead hours: an earlier repost could have halved its refund. The two Friday cars arrived on Monday.

The on-time share does not change. The refund tier can, and the dead gig holds a place in the intake's queue for those hours. HANDOFF.md says about half of the late orders never had a driver before the warning, so this path is the common one.

Fix: in `tick`, when an order's gig is unbooked and `now > lastPickupAt`, withdraw it and post it without windows.

## 4. A dropped gig comes back at the top of its ladder

`dispatch/desk.py:153`

The desk answers `gig_dropped` by forgetting the booking. The world reopens the gig with its old schedule, whose steps have all started.

- 79 drops on 750 gigs (10.5%); 76 were booked again.
- 74 of the 76 were rebooked at the top step of the gig's schedule, 12 of them in the minute of the drop.
- Mean fee 1.188 times typical before the drop, 1.403 after; 72% paid more.
- Median 420 minutes held before the drop, 30.5 minutes to the next booking. 23 of 76 drops came in the hour after midnight.

That is about 0.2 times typical for each drop, roughly €2 a gig on these weeks. The current ladder runs from 0.75 or 0.90 to 1.5, so the jump is larger now. Track 3 reports 0.10 drops per booking on the current mainline.

Part of the rise is needed: less time is left, and the driver who dropped wants more. The untested option is to reprice a dropped gig to the fee it booked at plus one step, and let it rise again.

## 5. Each deadline warning restarts the urgent ladder

`dispatch/desk.py:149`, `dispatch/desk.py:204`

`raise_fees` reprices with a schedule that starts at 1.5 times typical now. The world sends `deadline_close` again when an order loses its driver or its gig is posted again; 5 of the 6 warned orders in the board weeks got two or more.

With `fee_early`, `tick` starts the urgent ladder early, and it reaches 2.5 times in two hours. The world's own warning then arrives 3 hours before the last pickup and resets the fee to 1.5. With `fee_early=300` the reset comes exactly when the ladder tops out; with 480 the fee has stood at 2.5 for three hours.

So `b18`, `b21` and `b22` measured "raise early, then cut the fee at the warning", not earlier urgent fees. The mixed result (+€3,166 with a worst week of 91.67% at 300, −€3,556 at 480) does not settle the idea.

Fix: an order already urgent keeps its ladder (`resume`), and a new warning does not lower the fee.

## 6. The direct-offer study could not have found an acceptance

`tracks/t5/offers.py:68`, `tracks/t5/FINDINGS.md`

The study sampled gigs still open 30 minutes after posting, and offered them at 0.5, 0.7, 0.9 and 1.0 times typical. The 56 recorded bookings of those gigs in the app were at 1.20 to 1.75 times typical, median 1.35, a median 52 minutes later. Every offer was below the lowest fee at which any sampled gig booked.

"0 of about 580 accepted" therefore says nothing about offers at a fee a driver takes. The rules say where an offer pays: a driver who waits for a raise in the app takes less directly, and an offer reaches a driver whom no notification reaches. Neither was tested. The same script also takes its copies with `track='orch'`, against rule 2 of CLAUDE.md.

Check: offer at the app's current fee and one step above it, on gigs that are urgent or dropped, to drivers who finish near the pickup.

## 7. The intake limit is spent on quotes that mostly lose

`dispatch/intake.py:86`

The intake declines when `unbooked + len(pending) >= limit`. In the five weeks, a new request found a median of 5 to 6 earlier requests still awaiting their dealer, 8 to 9 at the 75th percentile and 10 to 12 at the 90th. About three quarters of requests get a real quote, and about 28% of those win.

So a typical request finds 4 of the 25 places held by quotes of which one will win. In a burst most of the room goes: 11 to 24% of requests arrive with 10 or more pending. The limit follows the arrival pattern as much as the driver load, and the quoter's queue charge (`waiting`) ignores pending quotes altogether.

Check: count each pending quote by its chance to win, and set the limit again on the same seeds.

## 8. The mainline sits to the right of the margin peak

`dispatch/policies/main.py:31`

From the scans, with a fee cost of 1.08 times typical and no trust:

| Flat price, times list | Orders a week | Margin a week | Per order |
|---|---|---|---|
| 1.3 | 498 to 643 | €12,000 to €16,300 | €21 to €27 |
| 1.4 | 331 to 489 | €11,200 to €16,700 | €28 to €38 |
| 1.5 | 204 to 363 | €8,300 to €14,600 | €35 to €51 |

The peak is at 1.3 to 1.4 with 330 to 640 orders. The mainline wins about 270 to 290, and the leaders deliver 410 to 450 at about €40. The slack rules are not the cause: 86.6% of requests have a later option with 12 hours of slack. The limit and the cost terms in the price are.

This matches the measured gain from `limit=35 morning_limit=45` (+€11,300 over 30 weeks). Each order of on-time capacity is worth about €35. Findings 3, 4, 6 and 7 are ways to get capacity without lowering the worst week.

## 9. The final runs on flags typed by hand

`dispatch/live.py:165`, `dispatch/policies/main.py:31`

`python -m dispatch.live` without `--policy` plays `base`, the kit starter, which is not ranked on any dev week. `main` without `--set` plays no bundles and fee model 1. HANDOFF.md lists the change of defaults as open.

Fix before the freeze: make the chosen setting the default of `main`, and `main` the default of `dispatch.live`.

## 10. Trust investment was never measured

`dispatch/pricing.py:46`

D01 sends 25 to 32% of all requests (260 to 330 a week). In the board weeks its count reached 10 on Tuesday afternoon at the earliest and 25 on Wednesday or Thursday, or never. Track 2's own bands agree: 37% of D01's quotes went out at a count under 10 and 30% at 25. For all other dealers 1% of quotes went out at 25.

An on-time D01 order on Monday raises every later D01 price by 1% until the count is full, which is worth about as much as the order's own margin. `invest` prices that in, defaults to 0, and no label in any findings file or commit message tests it.

## Smaller points

- `dispatch/notes.py:198`: a car under 30% charge always gets a charging stop. Rule 3 asks for one only over 200 km. 114 of 199 such requests (2.2% of all) are shorter; the stop costs the driver 40 minutes.
- `Notes.risk`, `Facts.sure`, `Facts.summer_tyres` and the `forecast` event are computed or received and used nowhere. In the board weeks, orders touched by forecast snow were late 2.0% (n=102) against 1.9%, so this sample shows no effect.
- `harness/slots.py:123`: an exception in a ranking run deletes the world, which ends the run at once with the desk gone. `harness.play` does not retry a single timeout.
- `harness/run.py:63`: with `--label`, weeks already in the index are reused after a code change.

## What I did not check

- The current mainline's saved weeks: the counts for findings 3, 4 and 7 should be redone on `b22-baseline` (`actions.jsonl.gz` shows refused posts directly).
- The offline tests: `pytest` is not installed here.
