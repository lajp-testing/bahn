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

## What failed

- `night` with the drivers' own hours, 23:00–07:00: no gain.
- `sleep=18`: more margin, but the worst week is 92.7%.

## On the frozen long-lane base (bba37d6 + slack 7caf8ff, worktree bahn-t3s, branch t3-fees-int)

All rows on top of the frozen flags (`long_lanes`, `long_markup=1.15`, `thin_both`, `thin_drivers=20`, `long_same_day=false`). The control `sctl@c03f13d` reproduces `vol-lp-readgate@edc1eb4` to the cent.

| Label | Change | Dev margin | vs readgate | Dev worst | fresh-06 / 07 / 08 |
|---|---|---|---|---|---|
| `vol-lp-readgate@edc1eb4` (frozen) | | €96,887 | | 94.4% (dev-10) | 82.8 / 90.1 / 90.5% (vr@3ea3f7f) |
| `sbkt@c03f13d` | `back=true thin_lead=780` | €103,579 | +€6,691 | 91.8% (dev-10) | 84.0 / 88.2 / 88.4% |
| `sbkx@86f0691` | + dual_lead, soon, sd_brake | €104,130 | +€7,243 | 91.8% | 84.2 / 87.8 / 88.8% |
| `ssl@c03f13d` | `same_day_slack=1440` | €108,026 | +€11,139 | 91.6% (dev-10) | |
| `sslbkt@c03f13d` | slack + bkt | €115,625 | +€18,738 | 91.6% (dev-04) | |
| `ssld5@c03f13d` | slack + `dual=0.05` | €110,510 | +€13,623 | 92.8% (dev-10) | 81.2 / 88.9 / 83.3% |
| `sqx@86f0691` | `dual=0.04 base=0.5 soon=300 sd_brake=true` | | | | 88.1 / 91.2 / 91.5% |
| `flu12@bb72ae4` | `flu_drops=12` | | | dev-10 95.2% | 84.1 / 90.1 / 90.5% |
| **`dc12@42fa639`** | **`day_cap=0.12`** | **€97,263** | **+€376** | **95.4% (dev-10)** | **91.3 / 93.0 / 90.5%** |
| `dc13@42fa639` | `day_cap=0.13` | | | | 90.1 / 92.3 / 90.5% |
| `dc13q@42fa639` | `day_cap=0.13` + sqx | | | | 91.3 / 91.3 / 91.5% |
| `sldc13@42fa639` | slack + `day_cap=0.13` | | | | 89.1 / 86.9 / 87.5% |

- **The fee schedule gains margin but not safety.** On this base every `back=true` arm makes on-time share worse, on dev and on the unseen fresh weeks.
- **The bulk-order Friday is an intake problem.** On t2-fresh-06, 82 orders won on Thursday were due on Friday and 42 were late; every late order got its driver only at the urgent fee, after the warning. Weeks with more than about 0.13 orders per driver due on one day before the last Monday went late: fresh-06 132/666, dev-10 102/712, fresh-03 116/829. orch-04 at 106/948 did not. **`day_cap`** (`ReachIntake.day_full`) quotes no option whose deadline day already holds `day_cap` × the drivers in orders. At 0.12 it binds on 3 dev weeks only and lifts the worst dev week to 95.4%.
- **The flu morning reprice (`flu_drops`, `Fees.tick`) does not rescue it.** Night drops (00:00–06:00) are a clean flu signal on weekdays: 24 on dev-10, 20 on fresh-06, 13 on fresh-10, and ≤11 on every other weekday. But the urgent fees at 06:00 cost fresh-06 half its margin and leave it at 84.1%: the day's work was already sold.
- **`same_day_slack=1440` is unsafe on unseen weeks**, even with day_cap.
