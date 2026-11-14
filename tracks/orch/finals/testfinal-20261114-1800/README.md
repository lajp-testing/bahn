# Test final, Saturday 14 November 2026, 18:00 UTC (world f53b4661bfe50ae2e4c23)

Our live runner played `--policy main --set fee_model=4` (commit fc3e132: learned cost model 4, car 1.1, same_day 480, flat fees, safe-car limit). Result: 5th of 75 ranked teams, €17,442.75, 356 orders, 97.2% on time, nothing undelivered.

| File | What it is |
|---|---|
| `leaderboard-feed.sse.gz` | The public leaderboard feed (`GET /v1/leaderboard`, server-sent events every 2 s), recorded from world minute 2271 (Tuesday 13:51) to the end. Every team: marginCents, revenueCents, wonOrders, onTimeShare, undeliveredShare, ranked. Read it with `python3 tracks/orch/final_feed.py <file>` (also `--by day`, `--by hour`, `--team <id>`). |
| `events-*.jsonl.gz` | Every event of our world, as the live runner saw it. |
| `reveal.json.gz` | The reveal after the end: our quotes and their outcomes, the truth of the cars we won, the gig views. |
| `roster.json.gz` | The world's 859 drivers (homes and profiles), fetched after the end with `tracks/orch/fetch_roster.py`. |
| `journal.jsonl.gz` | Every action our desk sent, with the minute and the world's answer. |

The same world fetched again after the end (events, reveal, snapshot as plain JSON) is in `tracks/t2/final-1800/`, with the analysis in `tracks/t2/FINDINGS.md` ("Test final 18:00: which requests we lost").
