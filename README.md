<img src="assets/icon.svg" width="64" height="64" alt="">

# bahn

A dispatcher for [Spread](https://spread.bahnexpress.com/llms.txt), Bahn's challenge at Junction 2026: it quotes car dealers and pays freelance drivers for one simulated week in Finland.

- `CLAUDE.md`: how the code is laid out and how to run practice weeks.
- `PLAN.md`: the approaches under test and the schedule.
- `docs/kit/`: the challenge's handbook, rules and API reference.

```sh
nix develop                                        # Python, numpy, pandas, pytest, ruff; loads the team key from .env
SPREAD_TRACK=orch python -m harness.run --policy base --seed spread-1
python -m pytest -q tests
```

## How it works

One desk plays the week. It keeps the books (requests, quotes, orders, gigs, drivers) and asks four small parts for every decision:

| Part | File | Decides |
|---|---|---|
| quoter | `dispatch/quote.py`, `dispatch/places.py` | the price of each option; the dial quoter prices for the best expected margin, moves with the dealers' answers, and reads a table of the competitor's price per pickup place |
| intake | `dispatch/intake.py` | which requests to take; the long-lane gate takes a long lane only when drivers can reach it |
| fees | `dispatch/fees.py` | a gig's fee schedule; the fee climb pauses at night (19:00–06:00), when drivers sleep anyway |
| notes | `dispatch/notes.py`, `dispatch/reader.py` | what a dealer's note means for the deadline and the price |

A policy (`dispatch/policies/`) is one choice of the four parts. `base` is the kit starter; `reach` is ours, with every idea behind a switch that is off by default, so each one has its own measured effect.

**Restart.** The desk is event-sourced: `Desk.rejoin` rebuilds it from the world's snapshot and events, then resends what was lost (open quotes first, then urgent reprices, then posts). A drill on ankka played practice weeks in real time through the live path: without restarts it matched `harness.run` to the cent, and with 7 kills and restarts it posted nothing twice, sent no quote late and stayed ranked.

**Ranking runs.** `harness.ranked` is the only way to a ranking run. It uses the test team's key only, plays the frozen policy, needs a one-use approval token, refuses while another world is open, and never deletes a ranking run.

## Continuous integration

`.github/workflows/tests.yml` runs the offline tests (`python -m pytest -q tests`) on a [CRACI](https://craci.com) runner (`runs-on: craci`). The tests need no server and no key. The job's network policy allows only GitHub (checkout) and PyPI (pytest), so a test that tried to reach the Spread API would fail in CI instead of spending a world. CRACI records every package the job pulls in as an SBOM: for this repository that is pytest and its four dependencies, because the dispatcher uses only Python's standard library.
