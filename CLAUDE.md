# bahn: a dispatcher for Spread

Our entry for Spread, Bahn's challenge at Junction 2026. The system plays a car transport dispatcher for one simulated week: it quotes dealers and pays freelance drivers. The final is one level 8 week on Sunday 15 November 2026 at 08:00 Helsinki time.

**The goal.** Be among the 10 ranked teams with the highest margin, then convince a jury. A team is ranked only when at least 90% of its orders arrive on time. The jury judges elegant, clear, creative and robust: few parts, each with a reason and a measured effect.

## Read first

- `docs/kit/HANDBOOK.md`: the world, the API, how drivers and dealers decide.
- `docs/kit/RULES.md`: every rule. It wins where the documents differ.
- `docs/kit/API.md`: routes, events, limits, the reveal.
- `PLAN.md`: the tracks and the schedule.

## The code

| Path | What it is |
|---|---|
| `spread/` | The kit's client, unchanged. Do not edit. |
| `dispatch/desk.py` | The desk: the books and the mechanics. It asks the four parts for every decision. |
| `dispatch/quote.py` | The quoter: the price of each option. Track 2. |
| `dispatch/intake.py` | The intake: how much work to take. Track 1. |
| `dispatch/fees.py` | The fees: a gig's fee schedule. Track 3. |
| `dispatch/notes.py` | The notes: what a dealer's note means. Track 4. |
| `dispatch/policies/` | A policy is one choice of the four parts. `base` is the kit starter's behaviour. |
| `dispatch/live.py` | Plays the final from the live stream, with the same desk. The orchestrator's. |
| `harness/` | The slot broker, the runner and the compare tool. |
| `tracks/<track>/` | A track's findings and its research scripts. |

A part sees every event (`observe`), can ask for a wake-up (`desk.wake`, then `tick`), and can read the map and the driver list (`desk.ctx`). `dispatch/parts.py` says what a part can do.

## Running weeks

Run from the repo root. The key is read from the main checkout's `.env`; never print or commit it. `nix develop` gives numpy, pandas, pytest and ruff; the dispatcher itself needs only the standard library.

```sh
export SPREAD_TRACK=t1                                    # your track: t1, t2, t3 or t4
python -m harness.run --policy base --seeds dev           # the 10 dev weeks at level 8
python -m harness.run --policy base --set markup=1.3 --seed dev-01 --seed dev-02
python -m harness.compare --list --track t1               # what the index holds
python -m harness.compare '<label A>' '<label B>' --seeds dev
python -m pytest -q tests                                 # offline checks, no server
```

- A run's label is its policy, its parameters and the code's version, so each change gets its own label. A week that the index already holds for a label is not played again: the world is deterministic.
- Every week is saved under `data/runs/` in the main checkout, shared by all tracks: events, actions, the reveal, the final snapshot, the driver list. `harness/play.py` lists the files. Use other tracks' weeks for analysis too.
- For an experiment that the runner does not cover, for example copies of a world (`fork`), write a script in your track's folder. It must take its worlds from `harness.slots` (`slots.create`, `slots.fork`).

## Limits that every track shares

The team holds at most 8 practice worlds that have not ended, copies included. Each track owns its slots:

| Track | Slots | About |
|---|---|---|
| `t1` intake and on-time | 2 | 65 weeks an hour |
| `t2` quotes | 2 | 65 weeks an hour |
| `t3` fees and drivers | 2 | 65 weeks an hour |
| `t4` notes | 1 | 32 weeks an hour |
| `orch` the orchestrator | 1 | holdout checks and ranking runs |

One level 8 week takes about 110 seconds and 1,900 requests. Budget your weeks before you start a sweep.

## Rules for a track

1. **Worlds only through `harness.slots`.** Never call `client.create` or `world.fork` directly. Never play a ranking run (`board`) or touch the final: a ranking run counts even when it fails.
2. **Stay in your slots.** Do not set another track's `SPREAD_TRACK`.
3. **Compare on the dev seeds, the same seeds for both versions.** The holdout seeds are the orchestrator's. For research, use seeds of your own, named after your track, for example `t2-study-1`.
4. **Report margin and on-time share together.** A change is an improvement when the total margin over the 10 dev weeks is higher and no week drops out of the ranking. A result on one or two weeks is a lead, not a finding.
5. **Do not tune to single weeks.** Every world draws its own drivers and prices. Prefer a rule that reads the week over a number that fits the dev seeds.
6. **Keep `tracks/<track>/FINDINGS.md` current**: what you tried, the labels, the numbers, what failed and why. Write it as you go, not at the end. The orchestrator reads it, and the jury asks for exactly this.
7. **Change your own part.** A change to `dispatch/desk.py`, `harness/` or another track's part must be small, and your report must name it.
8. **Commit to your branch often**, with the label and its numbers in the message. Do not push, and do not merge into `main`.
9. **Simple beats clever.** Each part needs a reason that fits in one sentence.

## Style

Use the challenge's words: dealer, request, quote, order, gig, fee, typical fee, deadline. Times are whole world minutes from Monday 00:00; money is whole cents.
