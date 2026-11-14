# Instructions for an agent analysing the 18:00 test final

You are helping the bahn team (Junction 2026, Bahn's "Spread" challenge) prepare for the real final on **Sunday 15 November 2026 at 06:00 UTC**. This folder holds everything we recorded from the second (last) test final. Your job is analysis: find what the best teams do that we do not, and turn it into concrete, testable changes to our dispatcher.

## Read first (about 15 minutes)

1. `CLAUDE.md` in the repo root: what the project is, how the code is laid out, the rules for tracks.
2. `docs/kit/HANDBOOK.md` and `docs/kit/RULES.md`: how dealers choose quotes, how drivers choose gigs, fees, deadlines, the 90% on-time rule. In particular: "Dealers compare prices", "The cost of a gig depends on where the driver is", "Drivers see a gig, then decide", "Direct offers".
3. `README.md` in this folder: what each file is.
4. `tracks/orch/FINDINGS.md`, the last sections (from "13:40" on): what our mainline is and what we already tried today, with numbers. Do not re-propose something listed there as tried unless you have a new reason.
5. `tracks/t2/FINDINGS.md`, section "Test final 18:00: which requests we lost": our win rate by price band, distance, option and weekday in this world.

## The game in five lines

A team runs a car-transport desk for one simulated week. Dealers send price requests (one or more cars, each with options `same_day`, `next_day`, `within_3_days`); we quote a price per option and compete with a house competitor priced 26–54% above the public list price. Won orders must be moved by freelance drivers whom we pay through gigs (a fee schedule that can rise; one gig can carry up to 3 cars). Margin = revenue minus driver fees, late refunds and penalties. A team is ranked only if at least 90% of its orders arrive on time; the 10 ranked teams with the highest margin go to the jury.

## What happened

Every team played its own copy of the same world. Our live runner played `--policy main --set fee_model=4` (learned cost model 4, cost tilt `car=1.1`, same_day quoted when 8 h of slack remain, flat driver fees, a safe-car queue limit).

| | Orders | Revenue/order | Margin/order | Margin | On time |
|---|---|---|---|---|---|
| 1 Juhus | 469 | €102.5 | €41.8 | €19,592 | 97.7% |
| 2 MathNet1 | 500 | €105.1 | €37.2 | €18,599 | 95.8% |
| 3 Progresful | 442 | €98.7 | €40.2 | €17,755 | 98.9% |
| 4 source-exp | 485 | €96.1 | €36.3 | €17,606 | 97.1% |
| **5 us (pelaaja-juhlii)** | **356** | **€119.7** | **€49.0** | **€17,443** | 97.2% |

What we already see:
- Our margin share (40.9%) is the best of the top group, and across the top 30 revenue per order and cost per order correlate at 0.91, so we do not overpay drivers. **The gap is volume**: 356 orders against 440–500.
- We win the middle (100–300 km, €58–122 list, 44–46%) and lose short/cheap requests (<100 km: 24%) and long ones (>500 km: 17%). Above 2× list we won 2 of 151 requests. 327 of 664 same_day options got no quote.
- We keep pace in quiet windows and fall behind in busy ones (Wednesday 16–20h world time: we won 22 new orders, the top teams 43–56). Hypothesis being tested now: when our queue of orders without a booked driver fills, the quoter's queue charge (`queue * waiting^2` in `dispatch/pricing.py`) and the intake limit (`dispatch/intake.py`) price us out exactly when demand peaks.

## The data

| File | Format | Notes |
|---|---|---|
| `leaderboard-feed.sse.gz` | gzip text; lines `data: {json}` every 2 s | Each JSON: `status` (`running`/`ended`), `now` (world minute from Monday 00:00), `endsAt`, `teams`: list of `{rank, team, name, marginCents, revenueCents, marginShare, wonOrders, onTimeShare, undeliveredShare, ranked}` for every team. Recorded from minute 2271 (Tuesday 13:51) to 14280. Many frames repeat the same `now`; keep one per minute. Revenue and margin are booked when cars are delivered, orders when won. |
| `events-*.jsonl.gz` | one JSON event per line | 14,776 events of our world: `price_request` (1,030, with the request: legs, options with list prices and deadlines, dealer, note), `order_won` (362), `order_lost` (668), `gig_booked`, `gig_dropped`, `gig_viewed` (10,554), `picked_up`, `delivered`, `deadline_close`, `ledger` (money lines), `order_changed`, `order_cancelled`, ... Field `at` is the world minute. |
| `reveal.json.gz` | JSON | `requests` (1,030: `request`, our `quote`, `outcome`, `option`), `orders` (362: the truth about each car we won), `views` (10,554: which driver saw which gig at which fee). |
| `journal.jsonl.gz` | one JSON per line | 1,695 actions our desk sent: `{at, action, result}`; types `quote` (1,030), `post` (482 gigs), `withdraw` (173), `reprice` (10). |
| `../../final_feed.py` | script | `python3 tracks/orch/final_feed.py tracks/orch/finals/testfinal-20261114-1800/leaderboard-feed.sse.gz [--by day|hour] [--team juhus] [--top N]`. |

`tracks/t2/final-1800/` has the same world fetched again after the end as plain JSON (`events.json`, `reveal.json`, `snapshot.json`), and `tracks/t2/` has the scripts that produced the loss analysis.

## What to find out

Answer with numbers from the data, and say how sure you are.

1. **Over the week, how did the top teams' orders, revenue and margin grow compared with ours?** Per world day and per 4 hours: where exactly do they get their extra ~100 orders? Which windows, and is it steady or in bursts?
2. **What can the feed tell us about their strategy?** For example: revenue per order over time (do they price lower at peaks, or win cheaper/shorter orders?), when their margin arrives relative to their orders (delivery speed), their on-time share over the week (do they take more risk early and less late?), teams with very different shapes (high volume/low margin vs. ours).
3. **Our side of the same windows:** from our events, journal and reveal, what did we quote in the windows where we fell behind? How full was our queue, how high were our quotes relative to list, how many options did we skip?
4. **Ideas.** For each idea: one sentence of reason, the evidence, the change in our code it implies (file and parameter or a small new rule), and how to test it (`--set ...` on `--policy main`). Rank them by expected gain. Ideas that are cheap to test with existing switches are worth more tonight than big rewrites.

## Rules

- **Analysis only.** Do not play practice weeks, ranking runs or the final, and do not touch the practice machine. The orchestrator runs all experiments; it will test your ideas.
- Never read, print or commit the team key (`.env`).
- Write your results to `tracks/orch/finals/testfinal-20261114-1800/ANALYSIS.md` (tables, then the ranked ideas). Commit it on a branch, with a short message; do not merge into `main` unless the team asks you to.
- Use the challenge's words: dealer, request, quote, order, gig, fee, typical fee, deadline. Times are world minutes from Monday 00:00; money is in euros or whole cents.
