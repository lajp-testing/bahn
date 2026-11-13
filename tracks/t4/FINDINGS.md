# Track 4: notes

Training corpus: all notes from existing dev-01 through dev-08 reveals (3,074 request records, including any repeated runs). The corpus builder retains the request and, for won orders, all leg truth. Dev-09 and dev-10 are reserved for testing and were not examined while writing rules.

First candidate recognizes explicit manual-licence, plates and summer-tyre phrases. Unrecognized facts are unknown, not false; all nonempty notes remain unsure. The policy uses the first two requirements on the first post and retains the starter's windows. It does not yet interpret dates, hours or corrections. This is an intentionally incomplete candidate, not an improvement claim.

## Held-out reader score

On the existing dev-09 and dev-10 reveals, 785 won requests had notes, with 796 leg observations. `python3 tracks/t4/corpus.py '<dev-09 glob>' '<dev-10 glob>' | python3 tracks/t4/score.py` reports right / wrong / unsure:

| Field | Right | Wrong | Unsure |
|---|---:|---:|---:|
| Earliest pickup | 0 | 0 | 796 |
| Pickup hours | 0 | 0 | 796 |
| Release | 0 | 0 | 796 |
| Delivery hours | 0 | 0 | 796 |
| Deadline | 0 | 0 | 796 |
| Manual | 11 | 0 | 785 |
| Plates | 6 | 0 | 790 |
| Summer tyres | 5 | 0 | 791 |

Counts are per won leg, and unknown includes both actual negatives and unrecognized positives. All 785 noted requests are unsure overall; an intake that declines every unsure note would be unusably restrictive. This first reader intentionally makes no negative assertions. The revealed ready time and site hours include the request's baseline, so a future reader must distinguish no note change from an unknown note change when scoring.

The end-to-end candidate `t4@76cf465` is running against the dev seeds; results are not yet available. Offline tests: 9 passed. No change outside the notes part, the policy, tests and track research files.

Training corpus follow-up, per won leg (repeated runs included): 162 later ready times, 119 changed pickup hours, 73 changed delivery hours, 58 releases, 134 note deadlines, 87 manual gearboxes, 51 plate requirements and 17 summer-tyre cases. These categories overlap. Examples include Finnish corrections ("valmis huomenna klo 13, ei kun klo 12"), pickup hours ("Nouto 10 - 15.30"), and multiple sites ("Kohde sulkee klo 15. Liike auki klo 8-19"). These show why the current equipment-only candidate leaves substantial work undone.

Preliminary paired dev-01 only: base margin −€60,648, on time 40.8%, versus `t4@76cf465` −€59,753 and 42.7%; neither ranked. Failed visits fell 36 to 17 (base: 10 not_ready, 11 closed, 13 no_plates, 2 licence; candidate: 13 not_ready, 4 closed). Failed-visit ledger costs fell €1,927.89 to €714.78; waiting rose €30 to €60; no fine ledger lines. The changed actions alter subsequent bookings and outcomes, so this is a lead, not a causal attribution or a ten-week finding.

After two paired dev weeks: total margin base −€128,641 vs candidate −€125,765; on time 45.8% vs 47.5%; both ranked 0/2. Base failed visits: not_ready 21, closed 23, no_plates 21, licence 5; candidate: not_ready 26, closed 12, no_plates 0, licence 2. Failed-visit costs €3,645.82 vs €1,575.62; waiting €180 vs €90; no fines. Two weeks remain a lead only.

After three paired weeks: margin −€198,329 vs −€195,177, on time 45.6% vs 48.0%, ranked 0/3 vs 0/3. Failed visits: base 21 not_ready, 36 closed, 29 no_plates, 9 licence; candidate 27 not_ready, 21 closed, 0 no_plates, 3 licence. Failed-visit cost €4,676.85 vs €2,110.60; waiting €288 vs €201; no fines. This remains preliminary.

After four paired weeks: margin −€283,140 vs −€276,622, on time 43.6% vs 45.6%, ranked 0/4 vs 0/4. Failed visits: base 27 not_ready, 37 closed, 41 no_plates, 11 licence; candidate 31 not_ready, 21 closed, 1 no_plates, 4 licence. Failed-visit cost €5,476.65 vs €2,278.84; waiting €439.50 vs €351; no fines. Candidate dev-04's saved event log was empty; the ended world's events were recovered through its read-only events API before calculating these counts. The visit script now excludes zero-byte logs. The result remains preliminary.

## Stint stop

Stopped the sweep at the roughly 30-minute limit with four completed pairs. Dev-05 timed out once; the retry was still running at the stop, so no dev-05 result is included. The track slot was reclaimed. The ten-week result and a complete reader are outstanding; do not treat this candidate as proven or enable its all-unsure risk as an automatic decline. Next: parse and test ready/release times, site hours, deadlines and corrections against a fresh held-out week, then rerun all ten paired seeds and audit missing event logs.
