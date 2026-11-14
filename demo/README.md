# The demo — a dispatcher's week in Finland

A static, offline browser demo that shows peer reviewers what our team built for
**Spread**, Bahn Express's challenge at Junction 2026: the challenge explained for
newcomers, and our system shown on a real week — the organiser's 18:00 test final of
14 November 2026, which we finished **5th of 75 ranked teams (€17,442.75, 356 orders,
97.2% on time, nothing undelivered)**.

No build step, no network, no JS libraries. Everything is served from `demo/assets/`.

## Run it

Any static file server, from this folder:

```sh
cd demo
python3 -m http.server 8000
# open http://localhost:8000/
```

Opening `index.html` directly over `file://` does not work (the page fetches its JSON
with `fetch`, which browsers block on `file://`). Tabs can be linked directly with a
hash: `index.html#week`, `#decision`, `#system`, `#race`, and `#week@3720` opens the
map at world minute 3720 (Wednesday 14:00).

## The five views

1. **The challenge** — the game in five steps and a flow diagram, the vocabulary
   (dealer, request, option, list price, quote, order, gig, fee, typical fee, deadline),
   and the 90% on-time rule that shapes every decision.
2. **The week** — the test final replayed on a map of Finland (towns and road distances
   are the world's real map; the outline is a hand-drawn simplification). Requests pulse
   at their pickup town, won orders show a ring until collected, cars travel along the
   actual fastest road route (Dijkstra over the map's road minutes) from pickup to
   delivery, late cars leave a red scar. Counters, the on-time share against the 90%
   line and a live event feed show the exact state at the chosen minute.
   **Scrubbing is first-class**: play/pause at four speeds, step one event forward or
   back, jump an hour or a day, click a day, or drag the slider to any minute — the
   map, counters and feed re-render the exact state at that minute, backwards included
   (every view is a pure function of the minute, not an incremental log).
3. **Inspect a decision** — every one of the 1,030 requests, filterable (won, lost,
   late, with a note, moved in a bundle), with a per-request pipeline: the note reader's
   facts → the intake (slack per option, queue fill) → the learned cost model (expected
   fee as a multiple of the typical fee, late risk, cost tilt) → the quoter (market
   level, dealer trust, win chance at our price) → the outcome → the gig (fee schedule,
   floor, who booked, when, after how many views) → the money (price − fee − refund =
   margin). Win rate by lane length sits above the list.
4. **How it works** — the eight parts as cards, each with its one-sentence reason and
   its measured effect; how we decided (switches, paired weeks, the worst-week rule);
   each adopted step as a measured bar; a table of ideas we tried and rejected.
5. **The race** — the live leaderboard feed of the test final (recorded every 2 s):
   us against the top team, margin and orders over the week, with the week's story
   (price war, bulk order, dealer trust) annotated. Only "us" and "the top team" are
   shown; no other team is named.

## What is exact and what is approximate

The week's ledger in `assets/week.json` sums to **€17,442.75 — the official result to the
cent** — and the race feed's end state matches the recorded 356 vs 469 orders.

| Number | Status |
|---|---|
| Requests, options, list prices, typical fees, notes | exact (recorded events) |
| Our quotes, outcomes, order prices, deadlines | exact (recorded actions + events) |
| Gig fee schedules, bookings, drivers, pickup/delivery times | exact (recorded) |
| Money per order (price, fees, refunds, margin) | exact from the ledger; a gig's fee is split evenly across its cars when the ledger line names no order |
| Market level at quote time, dealer trust counts, queue fill, slack, win chance at our price | exact: replayed through the real desk and parts, feeding the recorded events and actions |
| Note reader's facts | exact (the same reader ran on the same notes) |
| **Expected fee, late risk, cost tilt (the learned model's outputs)** | **approximate** — the final world's own driver list was not saved, so the replay uses a stand-in level-8 roster from a saved practice week for the model's driver-supply inputs (level-8 driver shortage is drawn per town, per world). Marked with a yellow **≈** in the UI. |

The replay itself is verified: it reproduces the whole week through `dispatch/desk.py`
and the parts of `dispatch/policies/main.py`, feeding the recorded events and journal
actions in minute order, and recomputes each quote at the recorded minute. The
recomputed prices match the sent quote on ~7% of requests to the cent; the rest differ
by the roster-driven inputs above (typically a few percent of price).

## Regenerating the data

From the repo root (standard library only):

```sh
python3 demo/prepare.py
```

It reads only files on disk — no server, no key:

- `tracks/orch/finals/testfinal-20261114-1800/` — the test final's events, action
  journal, reveal and leaderboard feed (`.jsonl.gz` / `.json.gz` / `.sse.gz`);
- `/home/agent/.t3/projects/bahn/assets/map.json` — the 30 places and 900 roads;
- the most recent saved level-8 `roster.json.gz` under `data/runs/` — the stand-in
  driver list (see the table above);
- `demo/assets/story.json` is hand-written (the explainer, the parts, the measured
  effects from `docs/jury.md` and the tracks' findings); `prepare.py` does not
  regenerate it.

and writes `demo/assets/{map,week,decisions,race}.json` (about 0.75 MB in total).

## Files

| Path | What it is |
|---|---|
| `index.html` | the page shell and the five views |
| `demo.js` | all logic: projection, replay state, scrubbing, views (plain JS) |
| `style.css` | styling |
| `prepare.py` | regenerates `assets/*.json` from the saved week |
| `assets/map.json` | places, roads, a hand-drawn outline of Finland |
| `assets/week.json` | the week as absolute-time arrays (requests, decisions, gigs, bookings, car moves with road paths, ledger) |
| `assets/decisions.json` | per-request internals from the desk replay |
| `assets/race.json` | the leaderboard race, us vs the top team |
| `assets/story.json` | hand-written explainer and system content |
| `screenshots/` | headless-Chromium captures of the five views |

## Known limitations

- The cost model's driver-supply inputs are approximated (see the table); everything
  the UI shows from them is marked **≈**.
- Car animation interpolates uniformly along the fastest road route between pickup and
  delivery; the world's actual driving time varies around the map's minutes, so a car's
  position between its recorded pickup and delivery minutes is illustrative.
- The map's Finland outline is a coarse hand-drawn polygon, not survey data; the towns
  and road distances are the challenge's real map.
- The fee split for a bundle gig divides the recorded fee evenly across its cars; the
  world charges one fee per gig.
- The event feed shows the twelve most recent request/win/loss/gig/booking/move events,
  not every ledger line.
