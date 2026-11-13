# Track 1: Intake and on-time

The intake limits unbooked orders plus quotes awaiting a decision to 15, and declines same-day options. It uses markup 1.6, all later options, opening fee 1.5 and six fee steps of 0.15 every 30 minutes. The limit is a conservative initial rule, not a measured capacity model.

| Label | Dev weeks | Margin | On time | Ranked |
|---|---:|---:|---:|---:|
| `t1-limit15-later-price16-fee11` | 10 | €37,221 | 95.3% | 9/10 |
| `t1-limit15-later-price16-fee13` | 10 | €12,114 | 96.2% | 10/10 |
| `base` | 10 | −€689,088 | 45.1% | 0/10 |
| `t1-limit15-later-price16-fee15` | 10 | −€31,979 | 96.0% | 10/10 |
| `t1-price16-fee15` | 4 | −€16,953 | 86.2% | 1/4 |
| `t1-limit15-later-price16-fee15` (same four) | 4 | −€11,352 | 96.1% | 4/4 |

The full comparison against base improves margin by €657,109 and ranks every week, but still loses money. Minimum on-time share was 93.4%. The four-week price-only test failed to rank three weeks; it is only a lead. The queue and later-options changes were tested together, so their individual effects are unknown.

In progress: `t1-limit15-later-price16-fee11`, same policy with opening fee 1.1 and 0.1 steps every 60 minutes. This tests whether lower fees preserve on-time performance and improve margin.

The completed lower-fee comparison `t1-limit15-later-price16-fee11` made **€37,221**, 95.3% on time, but ranked **9/10**; dev-10 reached only 89.8%, and dev-07 92.7%. Against fee15 it gained €69,200 but lost one ranked week, so it is not kept. The intermediate fee test `t1-limit15-later-price16-fee13` is in progress: opening 1.3, step 0.1 every 60 minutes, six steps.

Stopped the intermediate-fee run at the 30-minute stint limit after three completed weeks; cleaned up both track slots. On the paired dev-01 through dev-03, fee13 made €3,863 at 96.3% on time, 3/3 ranked; fee15 lost €7,434 at 96.5%, 3/3 ranked. This is a lead only. Resume the same label for the remaining seven weeks before deciding whether to keep it. No changes outside intake and policy assembly were made.

## Second stint: saved order analysis

For the ten fee11 weeks, the final snapshots contain 1,588 non-cancelled orders: 64 late, none undelivered, and 1,524 on time. Private pickup or delivery appears in 29/64 late orders versus 160/1,524 on-time orders; trade-ins in 7/64 versus 15/1,524; a note in 29/64 versus 681/1,524. Pickup towns with no resident driver account for 5/64 late versus 60/1,524 on time. A recorded failed visit occurred for 4/64 late versus 25/1,524 on time. These are associations, not proof of cause.

Dev-10 had 18 late of 177, seven with private addresses; its late pickup towns included Oulu and Kokkola (three each). Dev-07 had 13 late of 179, three with private addresses, including four pickups in Oulu. This suggests different failure modes; avoiding all private addresses alone cannot explain either week. Further investigation of booking drops, distance, deadline slack and daily conditions remains necessary.

The desk handles `deadline_close` by repricing open gigs with the urgent fee schedule, currently opening at 1.5 times typical and rising by 0.25 every 30 minutes to 2.5. It does not release booked drivers. A stronger schedule still needs a paired experiment.

Using each request's response deadline as the win time, median deadline slack was 1,875 minutes for late orders versus 4,460 for on-time orders. Eleven late orders and 96 on-time orders had a booking dropped; 43 late and 20 on-time orders received a deadline warning. Orders won Thursday contributed 26 late out of 488; Wednesday 17 out of 321. These days are not evidence of flu or snow without further event analysis. The warning is strongly associated with lateness but arrives after the intake decision.

Fee13 completed: €12,113.94, 1,648 orders, 96.2% on time, worst dev-07 93.2%, 10/10 ranked and all at least 92%. Kept as policy defaults against fee15, improving margin by €44,093 while meeting the floor.
