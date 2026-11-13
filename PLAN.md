# Plan: parallel approach tracks on practice worlds

Status: approved on Friday 13 November. The tooling of phase 0 is built; no run has started. Times are Helsinki time.

## What I measured

- One level 8 week with the kit's Python starter took 1 min 49 s from this machine: 1,891 requests at about 57 ms each, and 2.4 s of CPU. It reproduced the handbook's −€72,612.51 to the cent, so practice is deterministic as promised.
- Practice speed is bound by the network round trip, not by the language. Python and TypeScript would run at the same speed, so the code is Python: standard library only for the dispatcher, numpy and pandas for analysis.
- The practice limit was 666 requests a second when I checked. It falls to about 170 with 60 teams practising, 50 with 200, and 20 while a test final runs.

## The API budget

| Limit | Value | What it means for us |
|---|---|---|
| Unfinished practice worlds | 8 per team, forks included | The real ceiling: 8 weeks at once, whoever runs them |
| One week | about 110 s, 1,900 requests | 8 in parallel is about 4 weeks a minute, 260 an hour at best |
| Requests a second | 8 worlds need about 140 | Fine above 60 practising teams; slower below that |
| Test finals | Sat 14:00 and 20:00, about 20 min each | Practice drops to 20 requests a second: sweeps pause |
| Ranking runs | 5 per level per round, each holds a slot | A deleted or crashed run still counts |

Slots are split statically, so no track can starve another:

| Owner | Slots | Weeks an hour (about) |
|---|---|---|
| Track 1: intake and on-time | 2 | 65 |
| Track 2: quotes | 2 | 65 |
| Track 3: fees and drivers | 2 | 65 |
| Track 4: notes | 1 | 32 |
| Orchestrator (holdout checks, ranking runs, live runner) | 1 | 32 |

A 10-seed comparison of two versions is 20 weeks: about 20 minutes on 2 slots.

## Phase 0: shared foundation (me, about 1.5 hours, before any subagent starts)

Done already: the Nix flake (`nix develop` gives Python 3.14, numpy, pandas, pytest, ruff, jq, and loads the key from `.env`, which git ignores).

To build on `main`:

1. **Client.** The kit's client, vendored, standard library only.
2. **Slot broker.** Every world is created through it. It holds file locks in one shared directory, enforces each track's quota, deletes a world when its run fails, and has a janitor for leaked worlds. It refuses ranking runs and the final unless the orchestrator asks. One `PAUSE` file stops all runners, for test finals.
3. **Runner.** Plays a policy on a level and seed. It writes one result row, the event log and the reveal to a shared data directory, so every track's weeks feed every other track's analysis.
4. **Base policy.** The starter split into four replaceable parts: quote, intake, fees, notes. Each track changes its own part.
5. **Seed sets.** `dev` (10 seeds) for the tracks. `holdout` (10 seeds) that only I run, on merge candidates.
6. **Compare tool.** Two policies on the same seeds: margin, on-time share, orders won, weeks ranked.

## Phase 1: four tracks, one Opus 5.5 medium subagent each

Each subagent works in its own git worktree and branch, and only through the runner.

| Track | Question | What it delivers |
|---|---|---|
| 1. Intake and on-time | How many cars, and which, can the drivers of a level 8 week move on time? | A policy ranked on all 10 dev seeds with a positive margin: a throttle that raises prices as unbooked work piles up |
| 2. Quotes | At what price against the list price do quotes start to lose, by lane, dealer, day and hour? | A win-probability model, learned in the week's first hours, and a quote that maximises expected profit. It also tests whether forks give the exact switching price |
| 3. Fees and drivers | At what fee, and how long after posting, does a gig book, by lane, hour and where drivers live? | A cost estimate for each request, and a fee schedule. It tests flat against rising fees, and direct offers |
| 4. Notes | What does each note mean? | A rule-based reader scored against reveal truth, with an "unsure" answer that makes the system decline |

Track 1 is the mainline: tracks 2 to 4 each replace one part of it.

Left for later: gigs with several cars and return legs, trust farming, detectors for the flu and the bulk order, broad parameter sweeps, and the cherry-pick fallback. The first three need a stable base to measure against.

### Rules every subagent gets

- Worlds only through the runner, inside the track's slot quota. No ranking runs, no final.
- Compare on the dev seeds only, the same seeds for both versions. Report margin and on-time share together.
- A change is an improvement when the total over the 10 seeds is better and no week drops out of the ranking.
- Keep a `FINDINGS.md` in the track's folder: what was tried, the numbers, what failed. The jury asks for exactly this.
- Never print or commit the key.

### How I check in

- Inside a stint a subagent iterates by itself: change its part, play the 10 dev weeks (about 10 minutes on 2 slots), read the paired numbers, keep or revert. That is three to five iterations an hour.
- The first stint is about 30 minutes, when a bad start is cheapest to catch. Later stints are about 45 minutes. I read each report and the diff before the next stint.
- Between reports I read the shared run index and each `FINDINGS.md`. I look for: quota or seed-set violations, tuning to single seeds, claims without paired numbers, and work outside the track.
- I merge a track's change into `main` only when it also wins on the holdout seeds. The other tracks pick it up at their next stint.
- I cancel or re-brief a track that has gone two stints without a measured result.

## My own work during phase 1

- **The live runner** for the final: stream, rebuild after a restart, the 20-actions-a-second limit. It must be ready before the first test final.
- **Ranking rounds**, played with `main` once it is ranked on all dev seeds.

## Schedule

| When | What |
|---|---|
| Fri, now to about 23:30 | Phase 0 |
| Fri 23:30 to Sat morning | Phase 1 stints, overnight |
| Sat 13:45 | Sweeps pause; 14:00 first test final with the live runner |
| Sat afternoon | Phase 2: the deferred approaches on the merged base, then parameter sweeps |
| Sat 20:00 | Second test final |
| Sun 04:00 | Code freeze. Only fixes after this |
| Sun 06:00 | Last ranking round as a final check |
| Sun 08:00 | The final |

## Decisions I need from you

1. **Commits.** Worktrees need the foundation committed. May I commit to local branches, `main` included, without asking each time? I will not push.
2. **Overnight.** May the tracks run unattended overnight, with me merging winners into `main`?
3. **The final's machine.** This VM works (about 57 ms a request). Tell me if you have a machine nearer Stockholm.
