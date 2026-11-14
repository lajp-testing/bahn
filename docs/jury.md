# Bahn: earn the right to take the next car

First jury draft. Describes the defaults of `dispatch/policies/main.py` at `aec1152`, not every experiment in the repository. Sources beside figures are run labels or commits; linked findings explain their scope. “(check)” marks evidence still needed before presentation. Money is reported in game euros, rounded as in the source; the dispatcher uses whole cents and whole world minutes.

## 1. The problem

We dispatch car transport for a simulated week: a dealer sends a request, we quote delivery options, a win becomes an order, and we post a gig with a fee to attract a freelance driver. Margin is what remains after fees, refunds and penalties. Level 8 gives us roughly a third of normal driver supply, unevenly spread between towns; drivers learn whether waiting brings a higher fee, and the competitor changes its prices in response to our wins. Outages, a price war, driver illness and bulk requests disturb the week. Winning work is easier than delivering it. Below 90% of orders on time we are not ranked; only the top 10 ranked teams by margin reach the jury. Our central decision is therefore how much profitable work we can still promise. [Sources: kit **RULES**, “Practice and the final” and “Score”; **HANDBOOK**, “Dealers compare prices” and “The final”.]

## 2. The system

**The desk keeps the books so every decision uses the same account of the week.** It remembers requests, orders, gigs, bookings and deliveries, answers changes and failed visits, and sends actions. Each part sees events and can ask for a wake-up. Practice and the live runner use this same desk. [Code: `dispatch/desk.py`.]

**The profit quoter learns what dealers will pay while accounting for what their cars will cost.** For each option it searches for the price with the greatest expected margin: chance of winning multiplied by price after expected late losses, less expected driver fees and a charge for a filling queue. Wins raise the learned price level; losses lower it, with faster learning early in the day. Deliberate declines do not teach the model that prices are too high. Dealer trust comes from our own account: timely deliveries raise that dealer's accepted price level; a late refund reduces its trust count. This uses earned trust, without discounting today's order to speculate on future trust. [Code: `dispatch/pricing.py`.]

**The intake protects delivery capacity before we promise it away.** It counts orders without a booked driver and quotes awaiting a dealer decision. Its limit is 35, or 45 before noon; pending quotes count in full. Options normally need 720 minutes of slack after the first car's drive, using note-adjusted times. Same-day options need 360 minutes and at least 80 drivers living within 30 km of pickup. Private addresses are allowed. These are practical admission rules, not a forecast of available driver shifts. [Code/defaults: `dispatch/intake.py`, `dispatch/policies/main.py` at `aec1152`.]

**The measured fee ladder pays enough to get a booking without paying the top fee immediately.** Normal gigs open at approximately 0.75 of typical fee, or 0.90 where few drivers live near pickup, then rise by 0.10 every 60 minutes to 1.50. Normal raises pause from 21:00 to 07:00: a sleeping driver cannot respond to them. Deadline warnings use the urgent ladder. Fee model 2 is separate from this opening rule: it estimates total fees and late risk for the quoter from pickup lead time, arrival hour, private addresses, road distance and nearby drivers. [Code/defaults: `dispatch/fees.py`, `dispatch/policies/main.py`; model fit `00fabd4`.]

**Bundles let a scarce driver move more cars with less travel between jobs.** A newly won car can join an unbooked gig, including one still waiting to be sent. We combine up to three single-car orders, excluding private addresses and urgent cars. The route must fit windows and opening hours, with at most 30 minutes between cars and at most 660 driving minutes. Its fee is 0.85 of the sum of the cars' schedules. If still unbooked, it splits after 120 minutes of the drivers' day, or 240 minutes before its last feasible start, whichever comes first. Patience gives bundling a chance without trapping cars together indefinitely. [Code/defaults: `dispatch/bundles.py`, `dispatch/policies/main.py`; adopted in `59b6257`.]

**The repairs keep cars moving and avoid urgent fees when timeliness is already lost.** `windows` treats a window ending now as ended, preventing a refused repost. `orphans` posts an undelivered car again when it has neither a gig nor a pending post. `calm` uses the normal ladder when generating a new schedule for an urgent order past its last pickup minute; it does not automatically rewrite every existing late gig. [Code: `Desk.cut`, `Desk.tick`, `Desk.fees_for`; defaults `01035cd`.]

**The note reader turns a dealer's words into constraints before a failed visit teaches us the same lesson.** It reads Finnish, Swedish and English clauses for ready times, release after payment, pickup and delivery hours, deadlines, manual licences and plates. It handles corrections and denied times, then the planner uses these facts for stops and the intake uses them for slack. It is a local rule-based reader, with no remote language-model call in the decision loop. Its uncertainty flag does not currently make the intake decline a request. [Code: `dispatch/reader.py`, `dispatch/notes.py`.]

**The live runner preserves decisions as well as events so a restart can recover learned state.** It batches arriving events, uses the desk, and writes action/result pairs to a per-world journal. On rejoin it replays events and recorded results in minute order, then rebuilds current orders and gigs from the snapshot. The journal restores information absent from events, including accepted quote prices, pending quotes and single-car fee schedules. [Code: `dispatch/live.py`, `Desk.rejoin`; `ab85f1c`.]

## 3. How we know

We compare versions on the same weeks. Determinism makes a repeated identical policy reproduce its score; it does not make a small policy change stay local. A changed booking changes later driver availability and dealer trust. We therefore examine total margin, aggregate on-time share, individual weak weeks and how many weeks improve. Copies of a world help test a mechanism; complete weeks test its effect on the business. [Sources: kit **RULES**; [track findings](../tracks/t5/FINDINGS.md).]

The broader validation uses 10 dev worlds, 20 fresh worlds (`rob-01` through `rob-20`) and 10 holdout worlds. These became repeatedly used comparison sets, so “fresh” describes their introduction, not a promise that every later selection was independent. The limit-and-patience combination earned €484,003 against €456,931 over these 40 paired weeks, and raised the minimum on-time share from 92.8% to 93.7%. That is evidence for a combination, not an additive sum of individual gains. [Source: `b24-limit35-patience120` versus `b22-baseline`, `59b6257`, [orchestrator findings](../tracks/orch/FINDINGS.md).]

The table records the evidence available for the parts now on. Historical baselines differ; **do not add these gains together**. A blank isolated effect is an evidence gap, not a zero effect.

| Part retained | Measured result and delivery constraint | Source / comparison |
|---|---|---|
| Profit quoter and earned dealer trust | Historical integrated quoter: €73,495, 98.1% on time, all 10 dev weeks ranked. Later trust **and limit** integration: €88,588, 97.8%, all 10 ranked. Separate gains for learning and trust remain (check). | `316d626`; `4b77c14` (also changes intake). |
| Intake slack and selective same-day | €73,495 → €83,223; on time 98.1% → 97.6%, minimum 96.9% → 94.5%, all 10 dev weeks ranked. Tests general slack and same-day admission together. | `t1s4-base` → `t1s4-same360-80`, [track 1](../tracks/t1/FINDINGS.md). |
| Measured ladder, hourly raises | €64,350.29 → €67,234.10; on time 97.5% → 97.9%, minimum 96.4% → 96.1%, all 10 dev weeks ranked. | `t3-stint4-baseline` → `t3-stint4-rise60`, [track 3](../tracks/t3/FINDINGS.md). |
| Night pause | Adopted mainline: €105,898 over dev, 96.6% on time, minimum 93.4%. Isolated paired effect of the pause (check). | `40cadee`; historical run label `b10-quiet21` in [track 5](../tracks/t5/FINDINGS.md). |
| Fee model 2 | About +€280 over 10 dev weeks; on time 96.6% → 97.6%, minimum 93.4% → 95.9%. Margin gain alone is weak evidence. | `t3s5-base` → `t3s5-model2`, `0271218`. |
| Bundles | In 11 complete paired fee probes, the same cars booked for €916 together versus €1,068 alone, about 14% less. Early complete dev result with three-car bundles: €119,723, minimum 94.6%; aggregate on-time share for that label (check). | `t5-pair-1-pairs.jsonl`, [track 5](../tracks/t5/FINDINGS.md); `b13-bundle3`, [HANDOFF](../HANDOFF.md). Probe measures booking, not completed delivery. |
| Intake limit plus bundle patience | +€27,072 over 40 weeks; minimum 92.8% → 93.7%; orders 10,214 → 11,090. Aggregate on-time share for the adopted combination (check). | `b24-limit35-patience120` versus `b22-baseline`, `59b6257`. |
| `windows` + `orphans` | +€45 over 30 weeks; minimum remains 93.7%. Kept to remove a real failure, despite almost neutral margin. | `b26-fix-wo` versus unrepaired mainline; [review response](reviews/2026-11-14-response.md), `7e8a097`. |
| `calm` | +€5,347 over 30 weeks; on time 96.90% → 96.97%. Extension to 40 weeks: +€6,163, but minimum falls from 93.7% to 91.6%. | `t3s10-calm` versus `b26-fix-wo`; `edaa802`, `01035cd`, orchestrator findings. |
| Live runner and replay | Interrupted rehearsal: €11,287.63, 95.19% on time, versus reference €11,801.96, 96.5%. Scope and timing below. | `t3-live-2` / `t3-live-ref2`, `ab85f1c`. |
| Current note reader | Functionality is in the mainline; its isolated full-week margin and delivery effect remain (check). The early equipment-only reader's results are not a measurement of this reader. | `31e02d6`, `099dd53`; [track 4](../tracks/t4/FINDINGS.md). |

The worst week is a constraint, not a footnote. The initial capacity combination improved it; the subsequent `calm` decision deliberately accepted less headroom for more margin. The orchestrator attributed the weaker holdout weeks to likely downstream divergence, but that explanation is not proof of safety. We should present the observed tradeoff plainly. [Source: orchestrator findings, “calm becomes the default”.]

## 4. What we tried and dropped

- **Direct offers at realistic fees:** `t2s10-offers` lost €2,016 against `t2s9-base` over 30 weeks; on-time share barely moved, 96.90% → 96.91%, while the weakest week reached 91.0%. Only 91 of 3,783 offers were accepted. Removing the premium still lost €1,236. [Sources: `c614652`, `e7c6b5c`, track 5 findings.] The earlier cheap-offer failures alone had not settled the question.
- **Holding fees back:** `t3s11-hold720` lost €65,251 and `t3s11-back300` lost €134,674 over 30 paired weeks. On-time shares were 94.88% and 97.05%, with minima 90.1% and 92.2%. Unbooked gigs occupied the intake queue for longer, reducing orders. [Source: `21bb4fd`, versus `b26-fix-wo`, track 3 findings.]
- **More intake without enough delivery capacity:** limit 40 lost €2,213 and reached a minimum of 90.8% over 30 weeks. Lower prices combined with limit 35 and patience 120 produced a week at 87.4%, unranked. [Sources: `b27-limit40`, review response; orchestrator findings, adoption table.]
- **Outage detector:** despite a clear retrospective regional price signal, `b20-outage25` / `b20-outage25-rob` lost €2,732.32 against `b17-unsent3` / `b17-unsent3-rob` over 30 weeks; on time was 97.13%, minimum 92.12%. [Source: [handoff comparison](../tracks/orch/handoff-comparison.md), `14ac6f9`.]
- **Trust investment:** discounting today's quote for hoped-for future dealer trust lost between €2,000 and €9,000 in the reported 10-dev-week comparisons. The corresponding delivery figures need retrieval (check). [Source: review response, `c4fc1a5`; labels `b4-limit25-trust1-invest05`, `-invest1`, `-invest2`, `b4-trust1-invest1`, `b4-limit35-trust1-invest1`.]

## 5. Robustness

Restart recovery was rehearsed, not just designed. On `t3-live-2`, with two interruptions and downtime advancing at final speed, the runner ended at €11,287.63 and 95.19% on time. The same-seed reference `t3-live-ref2` made €11,801.96 and 96.5%: a 4.36% margin loss and 1.36 percentage-point delivery loss. This is one rehearsal on an earlier configuration, not a guarantee for the current defaults. [Sources: `ab85f1c`, [live rehearsal record](../tracks/t3/LIVE.md).]

In `t3-live-5`, the slowest measured desk batch was 121.039 ms and the slowest action round trip 563.665 ms. That test covered an accelerated Monday and final-speed Tuesday, not a full final. The recorded saved-week replay check passed. [Source: live rehearsal record.] The operational wrapper restarts the process after a crash (`bf8dae3`); the runner itself reconnects and rebuilds after a network failure.

Practice runs use a machine near the server, with shared slot locks and saved results. The later move to Stockholm reduced reported week runtime from 56 seconds to 22 seconds (`7e8a097`), allowing more paired checks. These are practice timings, not final latency guarantees. The live runner now selects `main` by default (`df776f8`), avoiding dependence on remembered experimental flags.

## 6. Open questions before presentation

The action journal records results after the server answers. A crash after acceptance but before the local write leaves a reconciliation gap; restart replay is not exactly-once execution. [Source: live rehearsal record and `dispatch/live.py`.]

The cost model was fitted before the current bundle mix. Its calibration under current defaults, and the effect of larger refunds for cars on `calm`, deserve further validation. Known review issues also remain: repeated deadline warnings can restart the urgent ladder, and the default still adds charging stops on short low-battery routes. Proposed repairs did not automatically earn adoption. [Sources: track 3 findings; review response; current `Desk.raise_fees` and `ReadNotes.plan`.]

Before this becomes the final jury account, fill the marked measurement gaps, confirm the final frozen configuration, and add the organiser-run test-final and final results (check). The supplied records establish rehearsal results and historical practice comparisons, not those later outcomes.
