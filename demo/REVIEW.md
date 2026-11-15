# Demo review: 15 November

Reviewer: a fresh agent, review only, nothing edited except this file and `review-shots/`.
I served `demo/` locally and took headless Chromium screenshots at 1440×900, 1280×800 and 390 wide,
covering every tab, the tour and inspector entries for a late car (R00683), a bundle (R00009), a
declined request (R00028) and a refunded trade-in (R00693). I read `demo.js`, `style.css`,
`index.html` and `prepare.py`, and checked the numbers against `tracks/orch/finals/testfinal-20261114-1800/`
(week.json/decisions.json recomputed in Python, the journal, ANALYSIS.md), `docs/kit/RULES.md`,
`HANDBOOK.md` and `tracks/orch/FINDINGS.md` (13:40 onwards). The map outline, label collisions and
tour zoom are being worked on elsewhere, so they get a short note only.

**Verdict: ship after fixes.** The design is deliberate and specific to its subject. The replay
really is a pure function of the clock, and most numbers check out. But several things a curious
reviewer will click on show something untrue: the end-of-week on-time share, three tour captions,
and the inspector's bundle, decline and gig history views. These are cheap to fix and they matter
more than any polish.

---

## Top 10 fixes, ranked by impact

### 1. On-time truth is wrong for trade-ins: the replay ends at 97.8% and 8 late, while the header says 97.2%
- **Where:** `prepare.py` build_week: `"late": de["at"] > order["deadline"]`. `demo.js:136` and `:626,637,709` (the same rule, `delivered > won.deadline`).
- **Evidence:** the ledger has 10 `late_refund` lines. The demo flags 8. R00693 and R00737 (2-leg trade-ins) were refunded €42.40 and €104.46 but both legs arrived before `order.deadline`, because a leg has its own window (RULES rule 5, private stops). At `#week@14280` the rail shows **97.8% and late 8** (`review-shots/week-end.png`), the header shows 97.2%, and the tour says "Ten of our 356 orders ran late". R00693's inspector shows an **"on time — the price is ours"** badge above a money bar with a refund segment (`dec-tradein-rm.png`). The "delivered late" filter misses both orders.
- **Fix:** in prepare.py, mark a move late from the leg's own deadline (the delivery window end), or simply from the set of `orderId`s that have a `late_refund` ledger line, which is exact. Export one `late` flag per order and use it in all four places in demo.js.

### 2. Three guided-tour captions are untrue
- **Where:** `demo.js:544,556,558,560`.
- **"68 minutes late"** for R00683: `lateMin = Math.round((de - deadline) / 60)` gives hours. The car arrived 4,050 minutes, about **68 hours**, late. That fits its 50% refund (€158.05 of €316.10, the >24 h band). Write "68 hours late: the dealer gets half its price back".
- **Bulk order:** "The intake's queue is near its limit of 35 unbooked orders, so we quote only the cars the flood screen says stay on time". ANALYSIS §3: on Wednesday the queue held 2–12 orders (max held+pending 25), and "no request was declined for it". The queue reached its limit only on Thursday 16–20 and Friday 14–18. "Flood screen" is also never defined. Replace with what ANALYSIS says: we won 4 of 30 because our cost held the price up during the price war.
- **Price war:** "the quoter's level spends the day stepping down". ANALYSIS: "on the price war day the level is not slow, the car's cost is the floor: the median quote stayed at 1.33–1.38 all Wednesday". Say that instead. It is also the more interesting story.

### 3. The inspector misleads on bundles, declines, gig history and notes
Each of these is a case a reviewer is likely to click:
- **Bundles** (`demo.js:715-716`, `review-shots/dec-bundle.png`): R00009 shows "booked at €61.28" and **"fee vs typical ×4.45 (floored at ×0.85, or ×1.15 under 40 km)"**. That divides the whole 2-car gig fee by one car's typical fee and quotes a floor that does not apply to bundles, so it reads as a 4.45× overpayment. The money bar then uses an equal share (€30.64) without saying so. Fix: for a bundle, show "gig fee €61.28 for 2 cars; this car's share €30.64 = ×N its typical fee", and drop the floor text.
- **Declines** (`demo.js:636-638,699`, `dec-declined-rm.png`): 90 requests were quoted at 5× list on purpose (ANALYSIS: 53 lacked slack, 19 hit the queue limit, the rest were notes and private addresses). They show a **"lost"** badge and "The dealer went to the competitor. Our level steps down…". Fix: add a `declined` badge, filter and outcome text ("We declined: no option had 12 h of slack"). Take the reason from the slack and queue data you already show. The intake's "declined (the quote sits far above the list price…)" explains the mechanism, not the reason.
- **Gig history** (`prepare.py` `gig_of` = the gig that picked the car up): R00683 shows "posted Fri 19:00", one hour before a 609 km car's deadline. That looks negligent. The journal has it posted at Thu 10:34 (g275, 15 min after the quote), then reposted as g310, g329 and g474 at Fri 19:00 (one post was refused because its window had ended). Fix: export every post, drop and reprice for the order and show them as a short gig timeline. This is the most interesting late car of the week.
- **Notes** (`prepare.py` capture `noteFacts`): `delivery_hours` and `summer_tyres` are not exported. R00676's note "perillä liike kiinni klo 16 jälkeen" (destination closed after 16:00) gets the chip **"harmless — no constraint"**, yet `reader.read()` returns `delivery_hours=(None, 960)`, and the order then paid a €30 `waiting` charge. 285 of 446 notes show as harmless, and some of them carry hours. Fix: export `delivery_hours` (and `summer_tyres`) and add a chip for each.
- **"late by 0 h"** for R00490 (3 min late), from `demo.js:719` `Math.round(x/60)`. Show minutes under 2 h, because that is also the refund band.

### 4. Per-order money is wrong for 2 orders, and the money bar's labels collide
- **Sign error** in `prepare.py` money: `waiting/fine/release_fee/undelivered_penalty` do `other + cents` with negative ledger cents, then `demo.js:723` computes `net = price − fees − refund − other`, which *adds* the cost back. R00676 shows margin **€81.21; the truth is €51.21**. Per-order nets sum to €17,750.06 against the ledger's €17,442.75. Besides the sign, €153.91 of driver fees are attributed to no order. Fix: `other -= cents` consistently (as `failed_visit` already does), show an "other" segment, and assert in prepare.py that the nets plus unattributed lines equal the ledger.
- **Bar labels** overlap when segments are narrow: "fee €181.76efund €42margin €199.80" (R00693) and "refund €158.05margin €-25" (R00683, `dec-late-rm.png`). `fmtEur(-2500)` prints "€-25". Fix: put labels in a legend row under the bar (or hide a label when its segment is under ~90 px), and format negatives as "−€25.00".

### 5. Map zoom is broken: `v.w, v.h = w, h;`
- **Where:** `demo.js:248`. The comma operator sets `v.h = w` and leaves `v.w` alone. Verified in the DOM: after one "+" the viewBox goes `544×1199 → 544×340`, and a second "+" changes only x/y, so the map never zooms further. It only "zooms" because the aspect ratio collapses.
- **Also:** `applyView` (`:233`) re-lays the towns but not `renderWeek`, so cars and rings, whose radii are in map units from `u()`, are drawn at the old scale until the clock moves.
- **Fix:** `v.w = w; v.h = h;` and call `renderWeek()` from `applyView`. Tell the agent working on the map: this may already be in their diff.

### 6. Playback stalls at "15 min/s"
- **Where:** `demo.js:528` `week.t = Math.round(week.t + dt/1000*speed)`. At 60 Hz, 15 min/s is 0.25 min a frame, which rounds back to the same minute, so the clock never moves. On a 120 Hz screen, 1 h/s (0.5 min a frame) runs at double speed.
- **Fix:** keep a float `week.tf` for playback and render `Math.floor(tf)`.

### 7. Two scoreboards that disagree, and counts that don't match the header
- **Where:** the header manifest (always the final result) above the rail (the replayed minute), `index.html:17-24,75-84`. At Wed 14:00 the screen shows both **€17,442.75** and **€3,997.35** labelled "margin". At the end the rail says **orders won 362** (6 were cancelled later) and **delivered 360** (cars: trade-ins have 2), against "356 orders" just above it. "Lost to the competitor 668" includes the 90 declines. A newcomer cannot tell which number is real.
- **Fix:** label the header "final result" (or dim it on the Week tab). Rename the rail rows "margin so far", "cars delivered", "lost or declined", and subtract an order from "won" at its `order_cancelled` minute.
- **Same family:** `clockStr` (`:29`) prints the second Monday as "Mon" (the timeline says "Mon 2"; the clock reads "Wed 22:00" at the end, `week-end.png`). Feed lines carry no day, so at the end the newest-first list reads "19:04, 09:00, 01:36, 20:07". Use "Mon 2" in the clock, and add the day to feed lines from another day.

### 8. "How it works": small factual slips and one misleading bar
- **Model 5 bar** (`demo.js:771`): the bar width uses `gain: 14444` (in-sample) next to the label "−€1,875 unseen", so a negative result is drawn as a positive bar. Draw it from the unseen number (zero width or a short left bar), or show both.
- "kept for the safer weakest weeks: **92.4% vs 91.8%**" (story.json adoption): FINDINGS 21:40 gives model 5 against b68 on unseen worlds as lowest **93.5** / 93.8 / 94.3 against 91.8 / 92.5 / 93.1. The 92.4% figure is the later b89 mainline.
- Rejected "Cheaper cars everywhere (**tilt 0.85–1.0**) bought orders at ≈€75 each": €75 applies to 0.9 and 0.85. car 1.0 was positive (+€7,395 b44, +€5,168 later). Say 0.85–0.9.
- Lead: "the eight parts **each with one reason and one measured effect**". The desk and the note reader have no measured effect (the page itself says "its full effect was never isolated"). Say "six of them measured".
- The intake card's effect is the combined "safe cars + flat fees" step (intake *and* fees). Say so on the card, as the adoption row does.
- The cost-model card says "The **final week's** model (5)", but the replayed week was played with model 4. Say "the model for the final (5)".
- Everything else checks against FINDINGS: +€69,993/38 of 40/364 vs 277, +€32,271 and rob-17 90.2→95.4, +€31,975/31 of 40/89.2%, +€31,187/holdout +€10,243/34 of 40, +€18,349/0.165 vs 0.183, limits +€6,495 (= +€2,462 + €4,033), 1.9 M orders, 44 inputs (tracks/ml), bundles €916 vs €1,068, calm +€6,163, and every rejected row.

### 9. The timeline is below the fold, and a lot of text is too small or too faint for a projector
- **Fold:** at 1440×900 and 1280×800 the map is a fixed `--map-h: 590px` (`style.css:31`), so the timeline (scrubber, story bands, late markers) starts at y≈885 and only its day labels show (`week-1440.png`). That is the main control and the "amber marks" the hint points to. Fix: `--map-h: clamp(380px, calc(100vh - 330px), 640px)`. This overlaps the map-sizing work.
- **Contrast:** `--faint #5C7188` is **3.7:1** on the background and 3.4:1 on panels, below AA for its 11–12.5 px uses: the manifest labels, table headers, the inspector's settings paragraph, feed times and chart axes. The "lost" badge is 2.97:1. Fix: raise faint to about `#7D93AB` (≥4.5:1) and set a 13 px floor.
- **Race charts:** axis text is `font-size="11/12"` in a 900-unit viewBox, about 8 px on screen (`race-1440.png`). Ticks are non-round (€5k/€11k/€16k/€21k, 127/253/380/507), "Wed 08" appears twice, and about 45% of the width (Sat to Wed 2) is two flat lines. Fix: 15–16 unit text, nice ticks (€5k steps, 100 orders), crop at Saturday 00:00 with a note "no requests after Friday 18:00". The Week timeline has the same dead half; compress Sat to Wed 2 to about 15% of the strip.
- **Type scale:** 18 distinct font sizes (10.5 to 44 px) and no scale. Pick about 6 (12/13.5/15/18/24/34).
- **Keyboard:** table rows, feed lines and map rings are click-only (`tr`/`li`/`circle` listeners), so the whole inspector is unreachable without a mouse. Make rows `tabindex=0` with Enter, or put a `<button>` in the id cell. Tabs have no `aria-selected` or `role=tab`. The space bar plays only when `body` is focused: after clicking "+1 h", space repeats "+1 h".

### 10. Robustness: silent failure when a file doesn't load, and no deep links
- `load()` (`demo.js:41-55`) has no `catch` and doesn't check `r.ok`. A missing JSON, or opening `index.html` from disk (`file://`, which a reviewer *will* try), leaves the header and empty tabs with no message. Fix: `.catch(e => main.innerHTML = "Couldn't load assets/…json. Serve the folder: cd demo && python3 -m http.server")`.
- The hash is read once: `showTab` doesn't write it, there is no `hashchange` listener, Back doesn't work, and a request can't be linked. Fix: `#decision/R00683` and `#week@3720`, written on tab change, request selection and pause, and read on `hashchange`.
- Smaller: `startTour` assumes a bundle and a late car exist (`:541-544`, a TypeError otherwise). `prepare.py` picks the race's "top team" by margin among *all* teams, unranked included (`max(final, …marginCents)`), and "us" by nearest margin. Filter on `ranked` and use the team id. `DATA` is a hard-coded absolute path. The `capture` comment "the final world's own roster was not saved" is stale (the roster is now loaded).
- Map (brief, it's on the other branch): the legend sits over the south coast where most of the traffic is ("Helsinki" reads "inki"); Hämeenlinna and Lahti collide; Finland fills about 30% of the map's width at 1440.

---

## Look and feel against the frontend-design skill

**Overall: designed, not slop.** DESIGN.md followed the skill's process (subject, tokens, layout, a review against the defaults), and it shows. The palette is a polar-night blue ground with birch text and three colours with roles. Fraunces with Plex is a real pairing, and the map is the one loud thing. "Kartta yöllä" fits a November week of moving cars across Finland, and nothing else on the page would suit a generic SaaS brief.

**Tells that remain (most visible first):**
1. **Green monospace prose.** The "How it works" effect column is whole sentences in green Plex Mono (`.part .eff`, `system-1440.png`). That breaks DESIGN principles 2 and 3 at once: mono only for data, green only for on-time. It is the most "generated" thing on the site. Use birch sans for the sentence, with only the euro figure in mono green.
2. **Mono for small meta labels and middle-dot strings:** `Mon 09:15 · dealer D02 · 1 car` (`.dhead .when`), the lane-stats line in mono joined by `·`, option rows `€49.21 · ×1.37 list · win chance 54%`, and kv values with prose in mono ("×1.40 of list — rises on wins, falls on losses"). These are skill tell #5. Write them as prose in sans and keep mono for the figures.
3. **"Word — fragment" labels and spaced em dashes everywhere:** race notes (`**Wednesday** — the price war…`), "harmless — no constraint", "on time — 90% ranks, or nothing counts", "18 of 45 unbooked — full". The em dash appears dozens of times on every tab.
4. **The default hero stat row twice:** the header manifest (big number, small label, ×5) and the rail's big number. Beyond the tell, it's the source of fix 7. Let the rail own "margin", and make the header a single line of prose ("5th of 75, €17,442.75, 356 orders, 97.2% on time").
5. **Accidental single-word accent:** `h1::first-line { font-weight: 300 }` with `h1 { font-weight: 800 }`. On desktop the whole title is 300, so the 800 is dead code. At 390 px it splits into "A dispatcher's week in" (300) and **"Finland"** (800), exactly the "one bold word" tell (`week-390b.png`). Pick one weight.
6. **Colour roles broken elsewhere:** the race chart draws the *competitor* in headlight amber ("look here") and us in on-time green. The money bar's fee segment is red, which is reserved for late. Use frost or birch for the top team, and a neutral for fees.
7. **Bordered panels with a 6 px radius** around the declist, timeline and both race charts: mild card-kit, acceptable. The challenge's "5 numbered steps" are only partly a sequence (4, "Margin", and 5, "the 90% rule", are rules, not steps), and step 5 sits alone in a two-column grid with an empty right half.

**Clarity for a newcomer.** The first-visit hint is good, and "Take the guided tour" is the right second action. But on a 1440×900 laptop the first view shows "€0" (the clock opens at Mon 09:30) next to "€17,442.75" in the header, with no timeline in sight (fix 9). The inspector's opening paragraph is settings jargon ("fee model 4, cost tilt ×1.1, flat-fee floors ×0.85/1.15, intake 35 (45 before noon, safe cars to 80)") and repeats on every request. Move it to a collapsible "settings" line and open with one plain sentence about *this* request. "quote/list ×1.31" as a column head needs a tooltip or "price vs list". The challenge tab reads well, and its numbers match RULES and HANDBOOK: the 26–54% competitor level, the 10%/two-business-day refunds, undelivered = no price plus a 2× penalty, deadlines at 20:00, 15 minutes to quote, trust +1% up to 25 and halved on a late order, the price war at 20% under from 08 to 18. The "road a request travels" is decorative: its labels zig-zag above and below, so it reads in a W order. A straight line would read faster.

**Motion.** There is one load reveal plus the spine drawing in when a request is clicked, which is right per the skill, and `prefers-reduced-motion` turns it all off. But `drawspine` scales the *whole* `.spine` (all its text) with `scaleY`, so the text is squashed for 350 ms. Animate a `::before` line instead. Stages start at `opacity:0` (`animation … both`). In headless screenshots several stages stayed invisible mid-animation (`dec-bundle.png`, stages 4 and 5 blank); in a real browser they appear. It is still fragile for print and screenshots: prefer animating from `opacity:.001` with a fallback, or only `transform`.

**Narrow (390 px).** The manifest overflows sideways ("97" is clipped), so the page scrolls horizontally. The tabs break per word ("Inspect / a / decision"). The legend covers the bottom third of the map, and the feed shows 3 lines. Not critical for a laptop or projector demo, but give the manifest `flex-wrap` and the tabs `overflow-x:auto; white-space:nowrap`.

---

## What is good and should be kept

- **The replay design:** every view a pure function of `t`, with bisection over sorted arrays. Scrubbing backwards is exact (I checked: the end-of-week margin is €17,442.75 to the cent, and the ledger sum matches). Performance with about 15k feed events is fine: each frame does O(moves) DOM work plus bisects.
- **Real data end to end:** prepare.py replays the real desk over the recorded events and journal with the as-played settings and the world's own roster. It reproduces 737 of 1,030 quotes to the cent and **says so per request** (exact / ≈ tags). Keep the honesty framing.
- **The inspector's spine:** note → intake → cost → quoter → outcome → gig → money is the best explainer on the site. With fixes 1, 3 and 4 it becomes the thing a jury remembers.
- **Story markers** on the timeline (price war band, bulk order, late triangles) and the clickable late markers that jump to the inspector.
- **The challenge tab copy:** accurate, plain and short. "The one rule that shapes everything" callout is the right emphasis.
- **"How it works" honesty:** the "rows are not additive" note, model 5's neutral result shown as neutral, the rejected table with the *rule* as the reason, and almost every number matching FINDINGS exactly.
- **Typography and palette choices** (Fraunces, Plex, polar night, amber, green, red with roles), vendored fonts, no network calls, no build step.
- **Keyboard scrubbing** (←/→ by event, shift by hour, ctrl by day), the first-visit hint, reduced-motion support and visible focus rings.

## Screenshots (`review-shots/`)
`week-first` (first visit, hint), `week-1440` (the fold), `week-end` (97.8%/8 late vs 97.2%), `tour-late`
("68 minutes", wrapped tour controls), `dec-bundle` (×4.45), `dec-declined-rm` (a decline shown as lost),
`dec-tradein-rm` (on time plus a refund, overlapping bar labels), `dec-late-rm` (gig "posted Fri 19:00", "€-25"),
`system-1440` (mono green prose), `race-1440` (8 px axes, flat half), `week-390b` (narrow),
`challenge-1440`. Files ending in `-rm` were taken with reduced motion forced on.
