# The demo — a dispatcher's week in Finland

A static, offline browser demo that shows peer reviewers what our team built for
**Spread**, Bahn Express's challenge at Junction 2026: the challenge explained for
newcomers, and our system shown on a real week — the organiser's 18:00 test final of
14 November 2026, which we finished **5th of 75 ranked teams (€17,442.75, 356 orders,
97.2% on time, nothing undelivered)**.

No build step, no network, no JS libraries. Everything is served from `demo/`.
The visual design follows `DESIGN.md` — a Finnish road map after dark, with the map
as the one loud element. Screenshots of every view are in `screenshots/`
(`screenshots/before/` holds the first build for comparison).

## Run it

Any static file server, from this folder:

```sh
cd demo
python3 -m http.server 8000
# open http://localhost:8000/
```

Opening `index.html` over `file://` does not work (the page fetches its JSON, which
browsers block on `file://`); the page replaces itself with a message saying so if any
asset fails to load. Every view deep-links: `#week@3720` opens the map at world minute
3720, `#decision/R00683` the inspector for that request; the hash is written as you
switch tabs, pick a request or pause, and Back works. Table rows, feed lines and map
rings are keyboard-reachable (Tab, then Enter).

The map sizes itself to the viewport, so the timeline stays on screen at 1280×800.
The page opens on **The week** at Monday 09:30, with a dismissible hint. Keyboard,
on the week tab: `←`/`→` step one event, `shift`+`←`/`→` one hour, `ctrl`/`alt`+`←`/`→`
one day, `space` plays or pauses.

## The five views

1. **The week** — the test final replayed on a night map of Finland. The towns and
   road distances are the world's real map; the border is real too — Natural Earth
   via `datasets/geo-countries` (public domain, `assets/finland.geojson`), simplified
   by `prepare.py` and drawn with the same projection as the towns; only the
   graticule is drawn for the demo. Requests pulse at their pickup town, won orders wear a ring until
   collected, cars travel the fastest road route (Dijkstra over the map's minutes),
   late cars leave a red scar. The right rail is a running manifest; the strip under
   the map is the whole week at a glance — day ticks, an hourly activity sparkline
   (requests and wins), amber markers for the story moments (the Wednesday price
   war, the bulk order, each late car) — drag it, click a marker, click a day.
   **Scrubbing is first-class**: every view is a pure function of the minute, so
   stepping, jumping and dragging backwards render the exact state. The map opens
   framed on southern and central Finland, where the week's work is; **Fit** shows
   the whole country, and the wheel or buttons zoom, drag pans. Town labels are
   ranked (big cities, then busyness) and any label that would overlap a
   higher-ranked one at the current zoom hides, so the busy south stays legible.
   The **guided tour** walks eight annotated moments — each one pans and zooms the
   map to its place and highlights the lanes it talks about — from the first
   request to the final score.
2. **The challenge** — the game in five steps, the road a request travels, the
   vocabulary, and the 90% rule.
3. **Inspect a decision** — every one of the 1,030 requests, filterable (won,
   lost, declined by our intake, late, with a note, moved in a bundle), each followed
   down the desk's spine:
   the note reader's facts → the intake (slack, queue fill) → the learned cost model
   (expected fee as a multiple of the typical fee, late risk, cost tilt) → the quoter
   (market level, dealer trust, win chance at our price) → the outcome → the gig
   (the fee schedule, the whole gig history: every post, reprice, refusal, drop and
   booking) → the money (price − fee − refund − other costs = margin, as a bar with a
   legend). Requests link both ways: click a ring or a feed line on the map to open
   one here; **Show on the map** jumps the week to its minute and highlights its lane.
4. **How it works** — the system **as it is now** (the eight parts, each with its
   reason and measured effect; how we decided; each adopted step as a measured bar —
   model 5's bar is deliberately neutral: money-neutral on unseen worlds, kept for
   the safer weakest weeks; a table of rejected ideas). The week, by contrast, was
   played by the Saturday 18:00 version — both tabs say so.
5. **The race** — the live leaderboard feed, us against the top team, margin and
   orders over the week, with the week's story annotated. No other team is named.

## What is exact and what is approximate

The week's ledger in `assets/week.json` sums to **€17,442.75 — the official result
to the cent** — and the race feed's end state matches the recorded 356 vs 469 orders.

The inspector's internals come from `prepare.py`, which **replays the whole week
through the real desk and parts** (`dispatch/desk.py`, `dispatch/policies/main.py`),
feeding the recorded events and journal actions in minute order and recomputing each
quote at its recorded minute — with **the settings that actually played the week**
(commit `fc3e132`: fee model 4, cost tilt ×1.1 on every lane, flat-fee floors
0.85/1.15, intake 35/45 with safe cars to 80, same-day at 8 h slack) and **the
world's own driver list** (`roster.json.gz`, 859 drivers, fetched after the end).

| Number | Status |
|---|---|
| Requests, options, list prices, typical fees, notes | exact (recorded events) |
| Our quotes, outcomes, order prices, deadlines | exact (recorded actions + events) |
| Gig fee schedules, bookings, drivers, pickup/delivery times | exact (recorded) |
| Money per order (price, fees, refunds, waiting and other costs, margin) | exact from the ledger; a bundle gig's fee splits evenly across its cars when the ledger line names no order, and prepare.py asserts the per-order nets plus unattributed lines sum to the whole account (€17,442.75) |
| On-time and late | exact: an order is late exactly when the account refunded it (a `late_refund` or `undelivered_penalty` line), so the rail ends at the same 97.2% and 10 late as the header |
| Market level, dealer trust counts, queue fill, slack, win chance at our price | exact (replayed through the real desk) |
| The note reader's facts | exact (the same reader, the same notes) |
| **Expected fee, late risk, cost tilt (the cost model's outputs)** | **exact where the replay reproduces the request's quote to the cent — 737 of 1,030 requests (72%); marked `exact` in green. On the rest (marked `≈` in amber) the replay's recomputed quote differs** — by ≤1% on 173 of them, 1–5% on 115, 5–20% on 5 — from replay state the desk held in memory (held bundle posts, drops) that the recording does not preserve. |

The as-played settings and the match rate are shown in the inspector's header, and
live in `assets/settings.json`.

## Regenerating the data

From the repo root (standard library only):

```sh
python3 demo/prepare.py
```

It reads only files on disk — no server, no key:

- `tracks/orch/finals/testfinal-20261114-1800/` — the test final's events, action
  journal, reveal, leaderboard feed and the world's driver list;
- `/home/agent/.t3/projects/bahn/data/map.json` — the 30 places and 900 roads;
- `demo/assets/story.json` is hand-written (the explainer, the parts, the measured
  effects from `docs/jury.md` and the tracks' findings); `prepare.py` does not
  regenerate it.

and writes `demo/assets/{map,week,decisions,race,settings}.json` (~0.8 MB total).

## Files

| Path | What it is |
|---|---|
| `index.html` | the page shell and the five views |
| `demo.js` | all logic: projection, zoom/pan, replay state, scrubbing, timeline, tour, views (plain JS) |
| `style.css` | the design system (tokens in `:root`) |
| `fonts/` | Fraunces (display), IBM Plex Sans (UI), IBM Plex Mono (numbers) — vendored woff2, loaded offline |
| `prepare.py` | regenerates `assets/*.json` from the saved week |
| `assets/map.json` | places, roads, and Finland's real border (rings of lat/lon points) |
| `assets/week.json` | the week as absolute-time arrays (requests, decisions, gigs, bookings, car moves with road paths, ledger) |
| `assets/decisions.json` | per-request internals from the desk replay |
| `assets/settings.json` | the as-played settings, fee floors and the exact-match rate |
| `assets/race.json` | the leaderboard race, us vs the top team |
| `assets/story.json` | hand-written explainer and system content |
| `DESIGN.md` | the design plan and its review against the generic defaults |
| `screenshots/` | browser captures: the five views plus the tour at 1440×900, and the week at 1280×800 (`before/` = the first build) |

## Known limitations

- 28% of the inspector's cost-model stages carry the `≈` mark (see the table); the
  sent quote, the outcome and the money are exact everywhere.
- Per-order money is the account's attribution: €153.91 of driver fees belong to gigs
  whose posts were refused or withdrawn and are split across their cars; the assert in
  prepare.py keeps the sum honest to the cent.
- Car animation interpolates uniformly along the fastest road route between the
  recorded pickup and delivery minutes; the world's actual driving time varies
  around the map's minutes, so a car's position between those two moments is
  illustrative.
- The border is Natural Earth 1:10m data (public domain, via `datasets/geo-countries`):\  
  generalised at source and lightly simplified by `prepare.py`, so at deep zoom the coast
  is smoother than a survey map; the towns, roads and distances are the challenge's real map.
- A bundle gig's fee divides evenly across its cars; the world charges one fee per gig.
- The event feed shows the eleven most recent request/win/loss/gig/booking/move
  events, not every ledger line.
