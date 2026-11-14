# Track 3: Fees and drivers

**Question.** At what fee, and how long after posting, does a gig book, by lane, hour and where drivers live?

## Findings

**The hourly climb overpays overnight.** In `base@f5a6b3b` (fr) dev weeks about 30% of gigs book at the top of the climb (1.35 × typical). Most were posted 14:00–17:00 and booked 06:00–08:00 the next morning: the climb reaches its top in the evening, when drivers view gigs but hardly book (bookings per hour fall sharply after 19:00). In `dev-10` those top-step bookings paid €4,257 above the opening fee.

**`night=true`** (`dispatch.fees.Fees`, `d0aadb3`) counts the climb's steps only in reading hours, from `wake` to `sleep` o'clock. Urgent schedules are unchanged. All rows are on top of `reach --set open=0.85 --set future_same_day=true`, level 8, test key:

| Label | Seeds | Margin | vs fr | Better on | Worst week | Ranked |
|---|---|---|---|---|---|---|
| `base@f5a6b3b` (fr) | dev | €69,264 | | | 94.0% | 10/10 |
| `night@d0aadb3` (23–07) | dev | €69,002 | −€263 | 5/10 | 93.3% | 10/10 |
| **`night19@d0aadb3` (19–06)** | dev | **€71,666** | **+€2,402** | **9/10** | 93.6% | 10/10 |
| `n18@d0aadb3` (18–06) | dev | €73,502 | +€4,237 | 10/10 | 92.7% | 10/10 |
| `ev120@d0aadb3` (a step every 2 h) | dev | €69,614 | +€350 | 6/10 | 92.8% | 10/10 |
| `fr@e7bf4da` | holdout | €66,153 | | | 95.5% | 10/10 |
| **`night19@d0aadb3`** | holdout | **€70,355** | **+€4,202** | **9/10** | 95.9% | 10/10 |

`night19` is frozen in `harness/ranked.py`. `n18` earns more but its worst week falls under 93%. 23–07 pauses too late: by 23:00 the climb has already reached its top.

## Fees for more volume, on `ltd3h8cr` (3a2dce2)

Base: frozen + `lanes=1 crowd=0.1 room=8 same_up=0.15 today_days=3 today_hours=8`; control `ltd3h8cr@95326e6` (dev €106,041, worst 96.5%; `ctl-sun@3a2dce2` matches it on dev-01 to the cent). Where the fees go on its dev weeks: on Monday about 70% of gigs book at the opening fee within about 45 minutes; Saturday bookings pay 1.24–1.29 × typical.

| Label | Change | Dev vs control | Better / worse | Worst week |
|---|---|---|---|---|
| `o80@3a2dce2` | `open=0.8` | +€1,286 | 5 / 5 | 94.9% |
| `o75@3a2dce2` | `open=0.75` | −€213 | 5 / 5 | 94.3% |
| `home60@87c1fcb` | `home_offer=0.6` | €0 | 0 / 0 | 96.5% |
| `home80@87c1fcb` | `home_offer=0.8` | €0 | 0 / 0 | 96.6% |
| **`wk@cda2f14`** | **`weekend=true`** | **+€1,184** | **10 / 0** | **96.6%** |
| `eo75@cda2f14` | `early_open=0.75` | −€302 | 4 / 6 | 95.8% |
| `eo75d2@cda2f14` | `early_open=0.75 early_days=2` | −€2,764 (8 weeks) | 3 / 5 | 95.3% |

- **`home_offer` does nothing.** A driver who has just delivered our car 90+ minutes from home declines or ignores an offer of our open gig nearby that goes their way, at 0.6 or 0.8 × typical: 15 offers on dev-07 (9 declined, 6 expired), 2 on dev-01 (both declined), and every week plays as the control.
- **`open=0.8`** passes on dev but wins only half the weeks; it plays on study and fresh next.
- **`weekend=true` wins on every dev week** (+€12 to +€297): a normal schedule does not climb on Saturday or Sunday, so a car asked on Friday for Monday books on Monday morning near the fee it had on Friday evening instead of at the Saturday top (1.24–1.29 typical). No week loses on-time share by more than 0.2 points. It plays on fresh and study next; `fri_from=14` (073abfd) also stops the Friday-afternoon climb for such gigs.
- **`weekend=true` on the unseen weeks:** t2-fresh (20 weeks) +€1,767, better 18 / worse 2; t2-study (17 of 20) +€1,591, better 16 / worse 1, worst 94.7%. But **t2-fresh-08 falls from 92.0% to 91.1%** (−€100): 37 late against 33, and all 4 extra are due on the last Monday. A Monday-due gig that holds its fee over the weekend climbs only from Monday 06:00. `sunday=false` (9730c94) pauses Saturday only, so such a gig climbs on Sunday and is near its top on Monday morning, as in the control.
- **A cheaper Monday opening (`early_open`) loses**: Monday's gigs book at the opening fee because they are cheap to do, not because drivers would take less; at 0.75 more of them climb, and with two days the on-time share falls on every week.
- Still playing: `Desk.pair` (narrow `pair=0.8/0.7`, wide `pair_save=0.5/0.2`).

## What failed

- `night` with the drivers' own hours, 23:00–07:00: no gain.
- `sleep=18`: more margin, but the worst week is 92.7%.
