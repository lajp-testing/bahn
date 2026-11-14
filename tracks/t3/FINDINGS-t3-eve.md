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

## t2-fresh-08 on the round candidate `ltd1cr@95326e6`

Flags: frozen + `lanes=1 today_days=1 same_up=0.15 crowd=0.1 room=8`. Fresh-08 is at 93.2% (lanes1: 90.1%), with 28 late of 424.

**What is late.** Not one crowded day: on `lcr10r10` the late orders split between Thursday (10), Friday (16) and the last Monday (13). The class that is peculiar to this week is the **long next_day order**:
- next_day orders of 300+ drive minutes are 10 of 21 late on fresh-08 and 7.1% late on the 29 other dev and fresh weeks (the next two numbers on the same weeks). Deliveries to Oulu, Rovaniemi, Vaasa and Kokkola are 22.8% late (other weeks: 4.8%). Espoo pickups are 15.4% late (1.0%).
- In the 69 other weeks a long gig books 24 hours or more before its last pickup, at 0.8–1.4 × typical (693 of 788). On fresh-08, the orders won under 30 hours before their last pickup found no driver at all until the pickup window had closed: 6 of 6 late. Rovaniemi orders from Espoo and Hyvinkää reached 2.5 × typical at the deadline warning, 3 hours before the pickup, and refunded €215–471 each.
- Over 70 weeks (dev, fresh, study, holdout, orch), next_day orders of **500+ minutes with under 30 hours to the last pickup** are 8 of 19 late and lose €1,866. They are the only long class with a negative margin: every other one earns €84–145 an order, including 500+ with 30 hours or more (€113/order, 21.7% late).

**The fee does not rescue them.** `eve_drive=300` (`Fees`, eac25d8) raises an unbooked long gig on the afternoon before its last pickup:

| Label | eve_top | fresh-08 | fresh-06 | fresh-07 | dev-10 |
|---|---|---|---|---|---|
| `ltd1cr@95326e6` | | €9,030, 93.2% | €10,214, 93.5% | €12,129, 95.6% | €12,218, 97.0% |
| `eve300@eac25d8` | 1.5 | +€508, 93.0% | −€953, 92.0% | −€33 | −€638 |
| `eve300t20@eac25d8` | 2.0 | +€316, 93.2% | −€417, 92.6% | −€228 | −€656 |
| `eve300t25@eac25d8` | 2.5 | +€52, 93.2% | −€538, 92.6% | −€437 | −€675 |

Even at 2.5 × typical the evening before, no driver took a Rovaniemi run for the next morning. Raises elsewhere cost margin and teach drivers to wait.

**The fix is not to sell it: `far_lead=30`** (`ReachIntake.expansion_options`, 9483b0d, a small change to track 1's part). No next_day on a long lane of `far_drive` (500) minutes or more whose last pickup is under 30 hours after the dealer decides; within_3_days is still quoted. `far30@9483b0d` against `ltd1cr@95326e6`:

| Seeds | Margin | Better / worse | Worst week |
|---|---|---|---|
| dev | −€974 (dev-07 −€543, dev-10 −€432) | 0 / 2 | 96.2% (unchanged) |
| t2-fresh, 20 weeks | **+€2,619** | 3 / 1 | 93.2% → **93.5%** |
| t2-study, 20 weeks | **+€1,820** | 4 / 0 | 95.2% (unchanged) |
| all 50 | **+€3,465** | 7 / 3 | none under 93% |

Fresh-08 is €10,983 (+€1,952) at 93.7%, with 26 late (Rovaniemi 1, against 5). On dev-07 the rule removed a late Turku–Rovaniemi order (−€272), but another Rovaniemi order then ran late in the same week; on dev-10 it removed an on-time one (+€192). Dev alone is path noise at this size.

**It does not pass on the orchestrator's seeds** (against `ltd1cr@95326e6`): holdout €113,357 (+€880, better on only 2/10, worst 94.5%); orch-01..10 €107,640 (−€1,005, better 0/10, worst 95.1%). On its own `far_lead=30` is not a candidate. The gain on fresh and study comes from the few weeks that hold a far-north run sold late, and the other weeks give back a little. Next test: on top of `ltd3h8cr@95326e6`'s flags (`far30h8`).

## What failed

- `night` with the drivers' own hours, 23:00–07:00: no gain.
- `sleep=18`: more margin, but the worst week is 92.7%.
