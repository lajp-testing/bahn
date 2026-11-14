# Handoff to the next orchestrator (written Sat 14 Nov 2026, 06:40 UTC)

You take over as the **orchestrator** of this project from a Claude session that ran out of usage. Read `CLAUDE.md` first (the project, the code, the rules for tracks), then this file. `PLAN.md` is older; where it differs, this file wins.

## The goal and the clock (all times UTC; Helsinki is UTC+2)

- Spread: one level 8 week, the **final on Sun 15 Nov 06:00**. A team is ranked only with at least 90% of orders on time; the 10 ranked teams with the highest margin present to a jury (elegant, clear, creative, robust).
- **Test finals: Sat 12:00 and Sat 18:00.** A test final is set 15 minutes before its start. No code freeze: we keep improving until the final; the best measured setting must be live (`bin/vps-live`) well before 06:00 UTC Sunday (the final is set at 05:30). Submissions close Sun 08:00.
- Practice board: `curl -s "https://spread.bahnexpress.com/v1/leaderboards/practice?level=8"` (no key). A ranking round is 5 secret worlds, each playable once. Our team is **"pelaaja juhlii"**. In the current round ("Saturday 00:00") we have €49,201 (rank 41 of about 150), played before bundles existed; the top is €85,925 and rank 10 is €75,475. Leaders deliver 410 to 450 cars a week at about €40 each; we delivered about 250 at €39. **When a new round starts** (the board's `current.name` changes), play it with the best mainline and tell the user how we compare: `SPREAD_TRACK=orch bin/vps python3 -m harness.run --policy main --set <settings> --board`, five times, one after the other.

## What the user asked for (still in force)

- Free to commit and push to `main` (remote `origin`, credentials are set up). Unattended runs are fine.
- **Subagents: GLM 5.3 only** (`delegate_task` target `{"providerInstanceId":"pi","model":"mistral/zai-glm-5-3","options":{"thinking":"high"}}`), **not the Flash version**, not Codex, not Claude. GLM needs narrow, mechanical briefs with exact commands, and the sentence "run `bin/vps` in the foreground and never end your turn while runs play". Each stint is a new `delegate_task` in a worktree from `main` (commit `main` first). No secrets in briefs.
- **Lengthen the stints a bit to save usage**: about 45 to 60 minutes per stint, few wake-ups, long detached batches on the practice machine, no status polling, short turns. Do the cheap offline analysis yourself.
- A worst week of about 92.5% on time is acceptable while exploring, but the final setting needs a clear margin over 90%: the final is a single week, and an unranked week scores nothing.
- Keep practice runs on the Hetzner machine (detached); the laptop's connection may drop. The user's first wish was for the final to run "here"; I told the user I plan to run the test final from the Hetzner machine with `bin/vps-live` (lower latency, restarts itself) and asked them to say if they object. No answer yet.
- Ask before deleting worlds you did not create. Never print or commit the key (`.env`) or the GitHub token. Do not edit `~/.claude/CLAUDE.md` / `/etc/nixos/agents/AGENTS.md`.

## Tools you need

- `bin/vps <command>`: runs one command on the practice machine and follows it. `bin/vps-batch <name> <script>`: starts a script there as a detached unit `bahn-<name>` in a **frozen copy** of the checkout; `bin/vps-batch <name>` shows its state, the end of its log, and pulls results into `data/`. My batch scripts end with `echo "batch done"`. Example scripts: `/tmp/claude-1000/-home-agent--t3-projects-bahn/c7891b44-762e-4662-abaf-7165b786a6fa/scratchpad/batch16.sh` … `batch20.sh` (copy the pattern; `run <track> <label> <args>`).
- Slots: 8 worlds at once. Tracks `t1`, `t2`, `t3` have 2 slots each, `t5` and `orch` one each (`t4` shares `t5`'s). A lane with one slot plays about 1.5 weeks a minute. With no subagent on a track, use its slots in your batches. Holdout seeds and `--board` need `SPREAD_TRACK=orch`.
- Seeds: `--seeds dev` (10 weeks), `--seeds holdout` (10, orch only), and 20 fresh weeks `--seed rob-01 … --seed rob-20`.
- `python3 -m harness.table <label prefixes>` (dev seeds), `python3 -m harness.compare <A> <B> --seeds dev`. For the `rob` weeks read `data/runs.jsonl` yourself (fields `label`, `seed`, `marginCents`, `onTimeShare`, `wonOrders`, `folder`).
- Analyses that read saved weeks: `tracks/t5/report.py <label>` (bundles by size), `tracks/t1/duedays.py`, `tracks/t1/latecause.py`, `tracks/t2/outage.py pickup <labels>`, `tracks/t2/war.py`, `tracks/t2/curve.py`. Keep printed output short.
- Tests: `nix develop --command python -m pytest -q tests` (23 pass).

## Evidence rule

**Ten weeks cannot tell two bundle variants apart**: the same setting differs by about ±€2,000 over the 10 dev weeks from noise. Decide on dev plus the 20 `rob` weeks, compared on the same seeds, and look at the three lowest on-time weeks, not only the total.

## Where the mainline stands

`main` is at `d603709` (pushed). The policy `main` with no `--set` is still the old mainline (no bundles, fee model 1): dev €105,898, 20 `rob` weeks €207,170 with lowest weeks 90.8% and 91.0%. Everything new is behind `--set` and **the defaults in `dispatch/policies/main.py` still have to be changed** once the choice is made.

New since the morning, all measured with `--set fee_model=2`:

| Part | Switch | What it does | Evidence |
|---|---|---|---|
| Fee model 2 | `fee_model=2` | refit of the expected fee and late risk the quoter uses | dev €106,178, worst week 95.9%; holdout €105,762, worst 95.0%; `rob` €207,363 but lowest weeks 90.1%, 90.4% |
| **Bundles** (`dispatch/bundles.py`) | `bundle=3` | a newly won car joins an open gig when one driver can do all stops in a row (next pickup at most 30 min from the last delivery); the bundle pays 0.85 of the sum of its cars' own fee schedules; without a driver 4 h before its last possible start it goes back to one gig per car | measured in copies of one world: a two-car gig cost 14% less than the two cars alone (`tracks/t5/FINDINGS.md`). Dev: `b13-bundle3` €119,723, worst 94.6% (`b13-bundle2` €114,825). Bundled cars paid 0.89 to 0.91 of typical against 1.04 alone and were late 1% against 3.3% |
| Join a gig not sent yet | in the code since `b17` | cars won in the same minute can share a gig (dealers send batches of 2 to 39 requests) | dev `b17-unsent3` €117,862 (inside noise of `b13-bundle3`); `rob` running |
| Earlier urgent fees | `fee_early=300` | an order without a driver goes to the urgent fees when 300 minutes of the drivers' day are left before its last pickup (the world warns at 3 h) | dev `b18-early300` €121,868, **worst week 96.4%**; `rob` running (`b18-early300-rob`, `b18-early480-rob`) |
| Outage detector | `outage=0.25` | on one day a week the competitor is down around one town (usually Helsinki, about 10% of the week's requests); requests picked up there win 60 to 80% at prices where the rest win 12 to 28%. The quoter compares the day's wins in a region with the rest of the country and prices the region 25% higher | hindsight scan over 30 weeks is clear (`tracks/t2/outage.py`); the first live version did nothing (dev `b19-outage25` €116,405); the rewritten one is `b20-outage25` (dev done, not yet looked at; `rob` running) |
| Price for a car that fits an open gig | `pair=0.15` | the quoter takes that share off the expected fee | dev: +€4,300 with two cars, about 0 with three (`b15-bundle3-pair20` €117,448); `rob` `b16-bundle3-pair15-rob` running |

Tried with bundles and not better: `bundle=4` or `5` (same as 3 within noise), `bundle_dead=60` (worse), `bundle_discount` 0.75 or 1.0 (flat), higher opening fees (`fee_buffer=0.3`, worse), `bundle_patience=120/240` (flat to slightly better, `rob` in `b16`). Higher volume: `limit=35 morning_limit=45` and `car=1.0` each raise orders by 7 to 13% and dev margin by 0 to 8%, but lower the worst week to about 93%; `rob` in `b16`.

The price war (one day a week the competitor is 20% cheaper): nothing to gain; every price from 1.2 to 1.5 times list earns about the same per request that day (`tracks/t2/curve.py`).

Why weeks fail: one bad day, usually Friday (most orders are due then, drivers drop bookings that morning; the weekly flu keeps 30% of drivers home for a day). About half of late orders never had a driver before the world's warning: that is what `fee_early` addresses.

## Running right now

Batches `b16` (bundle variants on the 20 `rob` weeks), `b17` (`b17-unsent3-rob`), `b18` (earlier urgent fees), `b20` (outage detector) are on the practice machine. Check each with `bin/vps-batch <name>`; they may need 20 to 40 more minutes. No subagent is running. Unmerged branch `t3/pricing-event-response` holds only an exploratory scan; ignore it.

## What to do next, in order

1. When `b16`–`b20` are done, compare on the same `rob` seeds against `b17-unsent3-rob` (the current code with `bundle=3`): `fee_early=300` or `480`, `outage=0.25`, `limit=35`, `car=1.0`, `pair=0.15`, `bundle=5`, `bundle_patience=120`. Adopt what raises the 30-week total without lowering the lowest weeks; then run the combination of the adopted settings on dev + `rob` + holdout once, and make it the default of `main` (also set `fee_model=2`, `bundle=3` as defaults). Commit, push.
2. **Sat 11:30: test final.** `bin/vps-live start --policy main --set fee_model=2 --set bundle=3 <adopted settings>` starts the live runner on the practice machine; it waits for the final, plays it from the stream, restarts itself after a crash and rejoins from the world and its action journal (rehearsed: a week with two kills ended 4% below the uninterrupted one). `bin/vps-live` shows the log, `bin/vps-live stop` stops it. Make sure no practice batch is running from about 11:45 until the test final has ended (about 34 minutes). Afterwards compare its score with practice weeks and read the log for refused actions and errors. Repeat at 18:00 with the then-best setting. For the real final start it Sun 05:15 with the frozen setting.
3. Play the next ranking round when it opens (see above) and report the comparison to the user.
4. More margin, if time allows: raise the share of cars that travel in a bundle (now about 42%; the main reason a car goes alone is that no open gig ends within 30 minutes of its pickup, `tracks/t5/why.py`); the volume settings together with `fee_early`; the outage detector's threshold (`outage_z`, `outage_n`).
5. Robustness before the final: the final setting's lowest week over dev + `rob` + holdout should be above about 93%. `private=false` (decline private addresses) and `late_floor=0.03` are safety switches that cost 1 to 3% margin.
6. For the jury: prune the switches that stayed off (`invest`, `dealer`, `towns`, `same`, `kind_offset`, `shape`, `lanes`, the governors, `fee_far_open`, `fee_soon_open`, …) after the freeze decision, and bring `tracks/*/FINDINGS.md` and `PLAN.md` up to date: each part with one sentence of reason and its measured effect.

## Things that bit me

- `harness.table` shows dev seeds only. `rob` results need your own few lines over `data/runs.jsonl`.
- A batch runs in a frozen copy, so a fix made after its start is not in it: new code needs a new batch name.
- Print little: one analysis that listed every request batch cost a lot of context.
- The world refuses a second gig for a car that is already in a live gig, so a lost race (a driver books the gig the desk is about to withdraw) is harmless; the desk restores its books from the refused answers.
