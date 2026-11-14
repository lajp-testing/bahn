# Assessment of the whole-repository review (14 November 2026)

Each claim of `2026-11-14-whole-repo-review.md` checked against the code and against the current mainline's own saved weeks (`b24-limit35-patience120`: limit 35, bundles of three, fee model 2, patience 120; 40 weeks: dev, rob-01..20, holdout). Script: `tracks/orch/verify_review.py`.

| # | Claim | Verdict | Our evidence |
|---|---|---|---|
| 1 | An expired gig is posted again with a window that ends this minute; the world refuses it and the car is never posted again | **True, and the main cause of undelivered cars** | `without_windows` dropped a window only when `to < now`. In 40 weeks all **8** undelivered orders (penalties €2,441, plus the lost price) ended with a refused post "The pickup window of R… ended". Repair `windows` |
| 2 | A refused post of one car has no fallback | **True** | `read_results` handled only refused bundles and withdrawals. 11 refused one-order posts in 40 weeks. Repair `orphans` (a car without a gig is posted again without windows) |
| 3 | After `lastPickupAt` the open gig is dead until `gig_expired` | **True** | 95 gigs expired more than an hour after their order's last pickup minute, 1,450 dead hours in all. Repair `late` |
| 4 | A dropped gig comes back at the top of its ladder | **Direction true, size overstated for the current code** | 1,221 drops, 1,068 rebooked: fee 0.96 times typical before, 1.29 after; 477 of 1,068 (45%, not 74 of 76) at the top step. Not repaired yet |
| 5 | Each `deadline_close` restarts the urgent ladder at 1.5 | **True** | `raise_fees` repriced with a new urgent schedule each time; 158 of 527 warned orders got two or more warnings. Repair `keep_urgent`. The point that `fee_early` was measured with this reset is also true |
| 6 | Direct offers were tested only below any fee the gigs booked at | **True** | `tracks/t5/FINDINGS.md`: offers at 0.5 to 1.0 times typical; the same gigs booked later at about 1.35. Untested at a realistic fee |
| 7 | The intake counts every pending quote as a won order | **True** (code) | `unbooked + len(pending) >= limit`. Switch `pending=<weight>` |
| 8 | The price curve peaks at more orders than we win | **Plausible, consistent** | Not re-derived. Consistent with limit 35 + patience 120: +€27,072 over 40 weeks with 9% more orders |
| 9 | The final depends on hand-typed flags | **Was true, fixed** | `main` now defaults to the measured setting; `dispatch.live` defaults to `main` |
| 10 | `invest` was never measured | **False** | Labels `b4-limit25-trust1-invest05/1/2`, `b4-trust1-invest1`, `b4-limit35-trust1-invest1` (10 dev weeks each): every weight lost €2,000 to €9,000 against the same setting without it |
| — | A car under 30% charge always gets a charging stop; the rule asks for one only over 200 km | **True** | RULES.md rule 3; `ReadNotes.plan` ignored the distance. Repair `charging` |
| — | `harness.run --label` reuses weeks after a code change | True | Known; labels are chosen per change by hand |

The repairs are switches (`--set repairs=windows+orphans+late+keep_urgent+charging`) so that each is measured on the same 30 weeks before it becomes the default; batch `b26` measures the first four.
