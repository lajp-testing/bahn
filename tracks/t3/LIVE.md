# Live rehearsal

Work in progress. The live loop previously selected only the final; `--world` now selects a non-ranking practice world after checking the world list. `harness.pace` creates a level 8 world through the slot broker and advances its clock while a separate live process acts. The final selection is unchanged.

Replay inspection: `Desk.rejoin` replays events, but `ProfitQuoter.result` records accepted prices and their factors and offsets. These action results are absent from events, so the replay cannot reproduce its learned level. `LimitedIntake.admit` maintains pending quotes outside event replay. The desk also loses original per-car schedules in `clock`, although it reconstructs bundle split times from current gigs. Restart correctness remains unproved; do not rely on a restart until these are addressed.

The offline suite passed: 22 tests. The reference and first rehearsal are waiting for t3 slots; results are pending. No margin, on-time, restart or timing claims have been established.

First uninterrupted rehearsal: `t3-live-1`, `main`, `fee_model=2`, `bundle=2`, 5-minute steps at 0.03 seconds per world minute. Margin €8,902.80, 206 orders, 97.09% on time. Reference `t3-live-ref` on the same seed: €9,042.97, 209 orders, 98.56% on time. Rehearsal margin was 1.55% lower and on-time share 1.46 percentage points lower. This is a single-seed rehearsal, not a general policy finding.

The first rehearsal used a checkout copied before batch timing instrumentation was added; its slowest batch is unknown. No restart or final-speed day has been run. The current rehearsal lacks restart scheduling and does not yet prove state recovery. The normal runner's reference took 680 seconds including slot wait.

Restart work: added a local per-world action/result journal and minute-ordered replay, restoring quote learning, intake pending quotes, and single-car fee schedules. The offline saved-week replay check and all 23 offline tests pass. The normal runner `t3-live-same` matched `b13-bundle3` on dev-01 exactly: €9,193.48 margin, 246 orders, 98.0% on time.

Reference `t3-live-ref2` (main, fee_model=2, bundle=3, t3-live-2): €11,801.96, 289 orders, 96.5% on time. An accelerated restart rehearsal with two 10-second pauses yielded €9,520.27, 238 orders, 96.22% on time, 19.3% less margin. At 0.03 seconds per minute each pause covers roughly 333 world minutes rather than the final's 33; a repeat at final speed during downtime is in progress. An initial real-speed day ran but its timing report was lost to SIGTERM; a repeat with graceful shutdown is in progress.

Repeat `t3-live-2` with each outage advancing at final speed: €11,287.63, 291 orders, 95.19% on time. Against the reference this is 4.36% less margin and 1.36 percentage points lower on-time share. The first, much worse run's 333-minute outages are a plausible cause of its result; this comparison changes the world pace as well, so it does not isolate the cause. The initial real-speed timing repeat also failed to print its timing because SIGINT was inherited as ignored; signal handling was fixed and another day is running.

Final-speed timing repeat `t3-live-5`: Tuesday at 0.3 real seconds per world minute, after accelerated Monday. Slowest desk decision batch across both days 121.039 ms; slowest `world.act` round trip 563.665 ms. The decision batch stayed below 300 ms, so bundle search was unchanged. The round trip is server/network time, not attributed to a part. End-of-Tuesday snapshot: €1,870.46 margin, 79 orders, 100% on time (not a completed week).

A journal only records an answer after it arrives; a crash or lost response after the server accepts an action but before the local write leaves an unavoidable gap without server-side action reconciliation. The saved-week test reconstructs intake pending from recorded quotes and compares parts across a break, rather than simulating the original intake decisions.
