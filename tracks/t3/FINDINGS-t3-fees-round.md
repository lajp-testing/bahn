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

### Where the fees go on the note-reader build (rd@bc3b064, 10 dev weeks, 4,001 bookings)

Measured from the saved weeks (`tracks/t3/booking.sh`, `late.sh` and `fit.py`; no new runs):

| Booked at | Bookings | Median wait | Late | Paid above the 0.85 opening |
|---|---|---|---|---|
| 0.85 (the opening) | 1,758 | 0 h | 12 | – |
| 0.86–0.99 | 566 | 1 h | 5 | €3,508 |
| 1.0–1.19 | 626 | 3 h | 10 | €8,251 |
| 1.2–1.49 (the top) | 829 | **16 h** | 28 | **€22,755** |
| ≥ 1.5 (after the warning) | 222 | 1 h | **96** | €10,724 |

- **The top of the climb is paid overnight.** The 1.2–1.49 bookings come at 06:00–08:00 after a wait of 10 hours or more: the climb reaches its top by 19:00 and the first driver up books it there.
- **The urgent fee rescues badly.** 43% of the orders booked after the deadline warning still arrive late.
- **Late orders are predictable at the quote.** Late share 3.5%; 12% with under 8 h from the answer to the last pickup, 7% with 1–2 days, 8–13% with fewer than 30 drivers within 60 km of the pickup, 9% with a private address, 6% for a premium car, 45% for the 20 trade-ins. Drives of 4–5 hours are not riskier (2.8%) and earn €49 an order. A logistic fit on these features (`ReachIntake.RISK`) is calibrated in five bands.

### Two switches, both off by default (c8aaf68, e652c54)

- **`back=true`** (`dispatch.fees.BackFees`): the climb is placed backwards from the deadline warning. It opens at `open` and reaches its top `lead` (2 h) reading minutes before the warning, a step an hour before that, in reading hours only (`wake` to `sleep`). With `morning=4` steps fall only 06:00–10:00. With `step_eur=600` each step adds €6 instead of 0.1 typical fees, up to `cap` (1.6) typical fees. With `risk_open`, risky orders open higher.
- **`dual=<target>`** (`ReachIntake.steer`, `late_cost`): an on-time controller with a price on lateness. The dial adds `(base + price) × risk × list` to an order's cost (a small change in `dispatch/quote.py`: `DialQuoter(late=...)`); after each request the price moves by `eta × (late and at-risk share − target)`. It replaces the on/off `late_budget` brake.

With every switch off the branch plays `rd@bc3b064` to the cent (`ctl@e652c54`: dev-01 €7,500.57, dev-10 €10,050.04).

All rows on top of the `rd@bc3b064` settings, 10 dev weeks, test key:

| Label | Change | Margin | vs rd | Better on | On time | Worst week | Ranked |
|---|---|---|---|---|---|---|---|
| `rd@bc3b064` | | €85,983 | | | 96.4% | 94.3% | 10/10 |
| `bk@e652c54` | `back=true` | **€97,532** | **+€11,549** | **10/10** | 94.2% | **90.3%** (dev-10), 90.6% (dev-02) | 10/10 |
| `o70@e652c54` | `open=0.7` | €82,286 | −€3,697 | 3/10 | 94.7% | 92.0% (dev-10) | 10/10 |
| `bkd5@e652c54` | `back=true dual=0.05` | €98,377 | +€12,394 | 10/10 | 94.8% | **90.2%** (dev-02) | 10/10 |
| `bkl8@e652c54` | `back=true lead=480` | €90,204 | +€4,221 | 9/10 | 96.6% | 92.9% (dev-10) | 10/10 |
| `bkl13@e652c54` | `back=true lead=780` | €87,749 | +€1,766 | 7/10 | 97.5% | 95.7% (dev-10) | 10/10 |
| **`bkt@d8ca071`** | `back=true thin_lead=780` | **€92,047** | **+€6,064** | **8/10** | 95.9% | **93.4%** (dev-10) | 10/10 |
| `bkdl@d8ca071` | `back=true dual=0.05 base=0 dual_lead=300` | €96,322 | +€10,339 | 9/10 | 94.7% | 90.5% (dev-02) | 10/10 |

`back=true` gains about €950 in every week (€3,093 on dev-07), but on-time share falls 2.2 points and two weeks sit just above the minimum. It is a lead for the on-time controller, not a candidate on its own.

`open=0.7` loses on the note-reader base: t1's +€3,839 for 0.7 was on an older stack.

**Why `back=true` is late, and why the controller does not fix it.** On dev-02, `bk` drew 61 deadline warnings against 38 for `rd`, 35 expired gigs against 16, and 30 of its 32 urgent bookings arrived late (rd: 15 of 27). Orders with 2 days or more of slack went from 2 late to 15. With `lead=120` the climb reaches its top 2 hours before the warning; a raise sends no notification, so drivers see the top fee too late to reach the pickup, and the gigs that miss it go to the urgent fee that rarely rescues. The dual price moves the quotes, so it trims volume (−5% orders) but not this fee-side lateness. `lead` of 8 and 13 reading hours, so the top is in the app a reading day before the warning.

**One lead does not fit every order.** Each hour of lead buys on-time share at a price: 2 h +€11.5k at 90.3%, 8 h +€4.2k at 92.9%, 13 h +€1.8k at 95.7%. Split by where drivers live, `bk` against `rd` over the 10 dev weeks added 77 late orders: where 30+ drivers live within 60 km of the pickup and 15+ of the delivery, +€5,908 for 33 more late (€179 each); with a thin end, +€4,600 for 44 more (about €100 each); thin at both ends with 2+ days of slack, +€229 for 14 more (€16 each). Hence `thin_lead` (BackFees): the short lead where drivers are dense, 13 reading hours where an end is thin. `bkt` is the first arm over 93% in every week.

**The controller on the fees.** `dual_lead=300` lengthens the lead by 300 minutes for each unit of the price, and `base=0` leaves the quotes alone until lateness passes the target. It lifted dev-10 from 90.3% to 94.2%, but dev-02 still ended at 90.5%: with a 5% target the price rises only once that week's lateness is already in the orders won. Six of the ten weeks are the same as `bk` to the cent, so the controller never engaged there.

`night19` is frozen in `harness/ranked.py`. `n18` earns more but its worst week falls under 93%. 23–07 pauses too late: by 23:00 the climb has already reached its top.

## On the round build (e33175a + lanes=1)

Frozen flags + `lanes=1`, 10 dev weeks, against `rg-dc12@9480b60` (`day_cap=0.12` alone: €100,271, worst 96.5%; `lanes1@90a19a6` is €98,847, worst 93.4%). Fresh columns are t2-fresh-06 / 07 / 08 (lanes1: 82.6 / 92.1 / 90.1%; rg-dc12: 91.3 / 95.2 / 90.1%).

| Label | Change on top of `day_cap=0.12` | Dev vs rg-dc12 | Better on | Worst week | Fresh 06 / 07 / 08 |
|---|---|---|---|---|---|
| `rgdc12q@9480b60` | `dual=0.04 base=0.5 soon=300 sd_brake=true` | −€3,345 | 3/10 vs lanes1 | 95.4% (dev-07) | 91.8 / 94.1 / 90.8% |
| `rgdq25@2958023` | `dual=0.04 base=0.25 soon=300 sd_brake=true` | −€2,833 | 5/10 | 94.8% (dev-02) | |
| `rgdq25n@2958023` | `dual=0.04 base=0.25` | −€2,295 | 5/10 | 94.8% (dev-02) | |
| `rgdq02@2958023` | `dual=0.02 base=0.5 soon=300 sd_brake=true` | −€3,773 | 1/10 | 95.4% (dev-07) | |
| `rgdc12c@2958023` | `crowd_load=0.08` | −€1,824 | 1/10 | 96.0% (dev-10) | 92.2 / 94.6 / 91.5% |
| `rgdc12c06@2958023` | `crowd_load=0.06` | | | dev-10 95.9% | 91.5 / 94.3 / 91.5% |
| `rgdc12c10@2958023` | `crowd_load=0.10` | −€1,456 | 1/10 | | 90.4 / 94.6 / 90.2% |

- **On lanes the dual controller costs more than it gains at every weight.** `day_cap` already gives the safety, so the dual price only sheds volume (dev-02 loses about €1,540 and 18 orders in both base=0.25 arms).
- **`day_cap=0.11` (`rgdc11@2958023`) ties with 0.12.** Dev €99,638 (−€633 against 0.12, +€791 against lanes1, worst 96.2%). All 20 t2-fresh weeks €217,626 (+€402 against 0.12, +€1,277 against lanes1), worst 90.6% (fresh-08), none under 90%, two under 93% (fresh-06 91.4%, fresh-08 90.6%). The gain on the crowded weeks (fresh-07 +€655) is paid back on fresh-15 (−€569) and on dev, so 0.12 stays.
- **`crowd_load` is the only arm that lifts fresh-08** (+1.4 points at 0.08; at 0.10 the lift is gone), but it costs €1.5–1.8k on dev. The quoter's `crowd` does the same on the quote side and gains on dev, so the fee version is not a candidate.

## What failed

- `night` with the drivers' own hours, 23:00–07:00: no gain.
- `sleep=18`: more margin, but the worst week is 92.7%.
