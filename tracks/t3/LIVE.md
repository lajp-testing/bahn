# Live rehearsal

Work in progress. The live loop previously selected only the final; `--world` now selects a non-ranking practice world after checking the world list. `harness.pace` creates a level 8 world through the slot broker and advances its clock while a separate live process acts. The final selection is unchanged.

Replay inspection: `Desk.rejoin` replays events, but `ProfitQuoter.result` records accepted prices and their factors and offsets. These action results are absent from events, so the replay cannot reproduce its learned level. `LimitedIntake.admit` maintains pending quotes outside event replay. The desk also loses original per-car schedules in `clock`, although it reconstructs bundle split times from current gigs. Restart correctness remains unproved; do not rely on a restart until these are addressed.

The offline suite passed: 22 tests. The reference and first rehearsal are waiting for t3 slots; results are pending. No margin, on-time, restart or timing claims have been established.

First uninterrupted rehearsal: `t3-live-1`, `main`, `fee_model=2`, `bundle=2`, 5-minute steps at 0.03 seconds per world minute. Margin €8,902.80, 206 orders, 97.09% on time. Reference `t3-live-ref` on the same seed: €9,042.97, 209 orders, 98.56% on time. Rehearsal margin was 1.55% lower and on-time share 1.46 percentage points lower. This is a single-seed rehearsal, not a general policy finding.

The first rehearsal used a checkout copied before batch timing instrumentation was added; its slowest batch is unknown. No restart or final-speed day has been run. The current rehearsal lacks restart scheduling and does not yet prove state recovery. The normal runner's reference took 680 seconds including slot wait.
