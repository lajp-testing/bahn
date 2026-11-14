# Live rehearsal

Work in progress. The live loop previously selected only the final; `--world` now selects a non-ranking practice world after checking the world list. `harness.pace` creates a level 8 world through the slot broker and advances its clock while a separate live process acts. The final selection is unchanged.

Replay inspection: `Desk.rejoin` replays events, but `ProfitQuoter.result` records accepted prices and their factors and offsets. These action results are absent from events, so the replay cannot reproduce its learned level. `LimitedIntake.admit` maintains pending quotes outside event replay. The desk also loses original per-car schedules in `clock`, although it reconstructs bundle split times from current gigs. Restart correctness remains unproved; do not rely on a restart until these are addressed.

The offline suite passed: 22 tests. The reference and first rehearsal are waiting for t3 slots; results are pending. No margin, on-time, restart or timing claims have been established.
