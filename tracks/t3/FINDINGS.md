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

## What failed

- `night` with the drivers' own hours, 23:00–07:00: no gain.
- `sleep=18`: more margin, but the worst week is 92.7%.
