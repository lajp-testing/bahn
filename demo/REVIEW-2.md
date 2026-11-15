# Demo review 2: 15 November

Reviewer: a fresh agent. I only reviewed and did not edit the demo; this file and `review-shots-2/` are the only changes.
I checked commit `b558c87`. I served `demo/` locally and drove it in a real Chromium tab, using
real pointer clicks, keyboard events, hash changes and timed scrubs. I also took headless screenshots at 1440×900, 1280×800,
1920×1080 and 390 wide. I recomputed the numbers from `assets/*.json`, from the recorded events and
ledger in `tracks/orch/finals/testfinal-20261114-1800/`, and from ANALYSIS.md, FINDINGS.md and RULES.md.

**Verdict: ship after fixes.** The fixes did their job on substance. The on-time numbers, the per-order money,
the bundles, the declines, the gig history and every How-it-works figure now check out against the data.
Five bugs remain that a reviewer will hit within a minute of clicking around, and each is a small change:
1. Clicking a ring on the map does nothing.
2. Clicking the timeline lands at the wrong minute.
3. Every page load rewrites the URL to `#decision/R00008`.
4. The race chart ends at €13k, while the header says €17,442.75.
5. Feed times after Sunday read "Tue 2 2 19:04".

On R00676, the implementer's €21.21 is correct, and REVIEW.md's €51.21 was wrong. The ledger has +€100.29 revenue,
−€49.08 driver fee and −€30.00 waiting (that line reads "site was closed at a time its stated hours show open").

---

## 1. Items from REVIEW.md

| # | Item | Status | Evidence |
|---|---|---|---|
| 1 | On-time truth for trade-ins | **Fixed** | `lateOrders` comes from the ledger's 10 `late_refund` lines. At `#week@14280` the rail shows 97.2%, 10 late and 356 won (`week-end-1440.png`). R00693 shows "late against its own delivery window" with a €42.40 refund (`dec-R00693-tall.png`). The late filter covers both trade-ins. |
| 2 | Tour captions | **Mostly fixed** | "68 hours late" is right (4,050 min). The price-war caption now describes the cost floor, and Wed 23% / Thu 48% match (50/221, 100/207). **But** the bulk-order caption says the queue "declined no request" on Wednesday. Wednesday had 10 declines; none of them was *for the queue*. The first-request caption has a stray " ; " ("within 3 days ; we lost"). |
| 3a | Bundle fee | **Fixed** | R00009: "the gig's fee €61.28 for 2 cars; this car's share €30.64, 2.23 times its typical fee", with no floor text. |
| 3b | Declines | **Fixed, but the reasons are guessed** | There is a `declined` badge, a filter and its own outcome text (`dec-R00028-tall.png`). The reason comes from `declineReason()`, a heuristic. Over the 90 declines it gives slack 70, queue 14, private 4, "cost" 2. ANALYSIS gives 53 slack, 19 queue and 18 notes/private. The "cost" reason ("the car cost more than the day's prices would pay") is not an intake rule. |
| 3c | Gig history | **Fixed** | R00683 now shows the whole story: g275 posted Thu 10:34, withdrawn, rebundled as g310, then g329, repriced, refused at Fri 19:00, g474 booked Fri 19:03. This is the best panel on the site. |
| 3d | Notes | **Fixed** (wording) | R00676 gets a delivery-hours chip. 256 of the 446 notes now read "harmless" (was 285). The chip reads "destination hours  to 16:00", with a double space and an empty start. |
| 3e | Lateness under 2 h | **Fixed** | R00490 reads "late by 3 min". |
| 4 | Money sign, bar labels | **Fixed** | R00676 €21.21 and R00683 "−€25" are correct. The legend sits under the bar. The won orders' nets sum to €17,677.06; the €234.31 gap to the ledger is the fees and release fees of the 6 cancelled orders, which is correct. The assert in `prepare.py` allows €10,000 of error, which is too loose. See also new item N11 on how the bar is drawn. |
| 5 | Zoom comma bug | **Fixed** | `v.w = w; v.h = h;`, and `applyView` re-renders. Checked in the DOM. |
| 6 | 15 min/s stall | **Fixed** | Float clock: 2 s of play moved 29 min. |
| 7 | Two scoreboards, rail counts, Mon 2 | **Fixed, with a regression** | The header is one prose line headed "Final result:". The rail reads "margin so far", "cars delivered", "lost or declined", and won minus cancelled = 356. The clock reads "Wed 2 22:00". **Regression:** feed times read "Tue 2 2 19:04" and, on the same day, "2 14:52". See N5. |
| 8 | How-it-works slips | **Fixed except the model 5 bar** | "six of them with a measured effect", the intake card naming the shared step, "the model for the final (5)", tilt 0.85 to 0.9, and 93.5–94.3 vs 91.8–93.1 all match FINDINGS. Model 5 is still drawn as a positive bar: `gain: 1875` (a positive number) next to "−€1,875 unseen". It is short and grey now, but it still points the wrong way. |
| 9a | Timeline fold | **Fixed at 1440×900 and 1280×800; broken at 1920×1080** | See N6. |
| 9b | Contrast | **Fixed** | Faint #7D93AB is 5.9:1 on the ground, 5.5:1 on panels and 4.7:1 on badges. The lost badge is 9.1:1. Exception: `.chip.off { opacity:.5 }` (the "same day: −0.2 h of slack" chips) is about 3:1 at 12 px. |
| 9c | Race axes | **Partly fixed** | Text is 15 units and ticks are round. Cropping at Saturday created two new problems, see N4. |
| 9d | Type scale | **Fixed** | The CSS uses 12 / 13.5 / 15 / 18 / 24 / 34. |
| 9e | Keyboard | **Partly fixed** | Rows, feed lines and rings have tabindex and Enter, and the tabs have `role=tab` and `aria-selected`. New problems are in N12. |
| 10a | Load errors | **Fixed** | `r.ok` is checked, and the error page names `python3 -m http.server`. |
| 10b | Deep links | **Partly fixed** | `#week@3720` and `#decision/R00676` work on `hashchange`. **Broken on load** (N3). Tab changes use `replaceState`, so Back leaves the demo instead of going to the previous tab. |
| 10c | startTour guard | **Not fixed** | `bundle[1]` and `lateMove.de` are read before the `if (!bundle \|\| !lateMove)` check, so the guard can never run. |
| 10d | prepare.py race teams, DATA, stale comment | **Fixed** | Ranked filter, our team by margin and order count, `SPREAD_DATA`, comment updated. |
| 10e | Map (brief) | **Partly fixed** | The legend no longer covers "Helsinki", but at 1440 and 1280 the label sits right on the legend's edge. Finland still fills about 35% of the map's width, and the hint covers the west coast (`week-first-1440.png`). |

**AI-design tells**

| Tell | Status |
|---|---|
| 1 Green mono prose | **Fixed.** The effect column is birch sans, with only the figures in mono green. The fix is an override appended at the end of the CSS; the old rule at `style.css:263` is still there. |
| 2 Mono meta strings | **Mostly fixed.** Option rows and kv lines are prose now. `.dhead .when` and the lane-stats line are still mono strings joined with `·`. |
| 3 Em dashes | **Improved.** The labels lost theirs, but the copy still has them (index.html 7, story.json many: "Keeps the books — requests, … — so"). |
| 4 Hero stat row twice | **Fixed.** One prose header, and the rail owns the margin. |
| 5 First-line weight trick | **Fixed.** h1 has one weight, 600. |
| 6 Colour roles | **Fixed.** The top team is drawn in frost and the fee segment is neutral. |
| 7 Card kit, step 5 alone, zig-zag road | **Not fixed.** Step 5 still sits alone with an empty right half. The road's labels still alternate up and down (`challenge-1440.png`). |
| Motion | **Fixed.** Stages animate only `transform`, and the spine line is a `::before`. Headless shots render every stage. |
| Narrow | **Partly fixed.** The manifest wraps and the tabs scroll. At 390 px the Decision tab is 521 px wide and How it works is 618 px, so both scroll sideways. |

---

## 2. New problems, ranked

**N1. Clicking a ring on the map never opens the inspector.** (`demo.js:596-600`, `:226-229`) *Must fix.*
The hint says "Click a ring … to inspect that request". With a real pointer, the log reads
`pointerdown:circle:button → pointerup:svg → click:svg`. The map's pan handler calls `svg.setPointerCapture()` on
every pointerdown, so the click is delivered to the `<svg>` and the ring's listener never runs.
A second cause: the towns group is drawn above the markers. At Wed 14:00, the centres of 63 of 72 rings sit under a town
dot or label, and `elementFromPoint` returns the town. Every ring sits on a town by construction.
*Fix:* in the map's pointerdown, return early when `e.target.closest('[role=button]')`, or call `setPointerCapture` only once
the pointer has moved more than 3 px. Add `.towns { pointer-events: none }`. Feed lines still work, and so do Enter on a focused ring and the timeline's late markers.

**N2. Clicking the timeline lands at the wrong minute.** (`demo.js:557-562`, `style.css:158`) *Must fix.*
`#tline` is `width:100%` and `height:96px` (88 px on short screens), with a `0 0 1000 96` viewBox and the default `meet`. Any strip wider than about 1,000 px is
letterboxed: at 1440 the drawing spans x = 274 to 1179 of 29 to 1411. `scrub()` maps the pointer over the *whole*
element width. I clicked exactly on the drawn start of Wednesday at 1280 wide and got **Wed 06:14**, with the cursor 38 px right of the
pointer. Near the ends the error grows to most of a day. The strip also uses only about 65% of the width, which looks unfinished (`week-wed-1440.png`).
*Fix:* map through the CTM: `const p = new DOMPoint(e.clientX, e.clientY).matrixTransform(svg.getScreenCTM().inverse()); x = p.x - 8;`.
Better still, build the viewBox from `svg.clientWidth` and rebuild it on resize, so the strip fills the row.

**N3. Every page load rewrites the URL to `#decision/R00008`.** (`demo.js:749-750`, `:825`) *Must fix.*
`buildDecision()` preselects the first request with a note through `selectRequest()`, which calls `writeHash`. Load `/` or
`#week@3720` and the tab shows the week while the address bar says `#decision/R00008`. A reviewer who copies the link, or reloads, lands
on the inspector. *Fix:* give `selectRequest` a quiet flag, `selectRequest(id, {quiet: true})`, for the preselection.

**N4. The race chart's end values contradict the header, and its footnote overprints the axis.** (`demo.js:975`, `:998`) *Must fix.*
Cropping at Saturday 00:00 ends the lines at "us €13k" and "top team €15k". `race.json` gives €13,186 / €15,076 at Sat,
but €17,442.75 / €19,592.05 at the end, because revenue is booked on delivery and deliveries run into Wed 2. The header says €17,442.75.
The footnote "the week runs to Friday 18:00; the chart stops at Saturday 00:00" is drawn at the same y as the
"Thu 08" and "Fri 08" tick labels and overprints them (`race-1440.png`).
*Fix:* compress the tail the way the Week timeline does (Sat to Wed 2 in the last 15%), so the lines end at the true finals. Or keep
the crop and label the ends with the final numbers. Move the footnote into HTML under the chart. The orders chart is unaffected (356 / 469 by Sat).

**N5. Feed times after Sunday read "Tue 2 2 19:04".** (`demo.js:34`) *Must fix.*
`hhmm = clockStr(min).slice(4)` assumes a three-letter day. "Mon 2 19:04".slice(4) is "2 19:04". The bug came in with the Mon 2 fix.
Same-day lines read "2 14:52" (`week-end-1440.png`, `tour-late-1440.png`).
*Fix:* `const hhmm = (m) => \`${pad(Math.floor(m % 1440 / 60))}:${pad(m % 60)}\``.

**N6. On a 1920×1080 projector the timeline is below the fold again.** (`style.css:31`, `:316-327`)
Above 980 px of height the subtitle shows, so the header is about 160 px tall, and `--map-h = min(780, 100vh-300)` = 780. The controls sit at
y ≈ 1,030 and the strip falls off-screen (`week-1920.png`). The header's result line also runs to the window's edge, while
`main` stops at 1,520 px.
*Fix:* use `--map-h: clamp(420px, calc(100vh - 420px), 780px)` by default and keep `-300px` inside the `max-height:980px` block.
Give `header` the same `max-width` as `main`.

**N7. On a laptop, nothing on the first screen says what Spread is.** (`style.css:319`, `demo.js:101`)
At heights of 980 px or less (every laptop and 1280×800 projector) `.sub` is hidden. The page then opens with "A dispatcher's week in Finland" and
"Final result: 5th of 75…". `story.json` has `challenge.intro`, but the page never renders it.
*Fix:* keep a one-line subtitle, for example "How our team played Spread, Bahn's car-transport dispatching challenge at Junction 2026, in one recorded
week." Render `challenge.intro` as the Challenge tab's lead.

**N8. The tour box overflows.** (`style.css:117-118`) In the late-car step, "Inspect R00683" wraps onto two lines, "7 / 8"
stacks into a vertical sliver, and "Close" sticks out of the box (`tour-late-1440.png`). *Fix:* put the step counter in
the title row, add `flex-wrap: wrap` to `.tourctrl`, and use `white-space: nowrap` on the buttons.

**N9. The decline reasons are inferred, and the counts disagree with ANALYSIS.** (`demo.js:791-799`) See 3b. *Fix:* export the
intake's real verdict from the replay in `prepare.py`, since it already calls `intake.admit` there. Until then, drop the "cost" fallback:
say "declined: reason not recorded" rather than invent one.

**N10. Bulk-order caption.** (`demo.js:678`) Change "declined no request" to "declined none for a full queue". Fix the stray " ; " in step 2 (`:670`).

**N11. The money bar reads as parts of a whole.** (`demo.js:911-921`) Price, fee and refund are stacked side by side, and the margin
is not drawn at all. R00683's €25 loss looks the same as a profitable order.
*Fix:* draw two aligned rows: the price on top, and fee + refund + other + margin below at the same scale. A negative margin then shows as costs running past the price,
in late red.

**N12. Keyboard problems.**
- Enter on a request row moves focus to `<body>`, because `selectRequest` re-renders all 1,030 rows (checked: row R00041, then BODY).
- The list has 1,030 tab stops before the detail panel.
- Space on a focused button (Guided tour, Next) toggles play, because the `keydown` handler skips only input, select and textarea.
- Feed lines and rings are rebuilt on every frame, so focus is lost while the replay plays.

*Fix:* toggle the `.sel` class in place instead of re-rendering, use a roving tabindex in the table, and skip the space shortcut on
`button, [role=button], li[tabindex]`.

**N13. Small fixes**
- Model 5 bar: draw it from the unseen number, `gain: 0` or a short left bar.
- "destination hours  to 16:00" should read "destination closes at 16:00"; R00676's "other costs €30" should say "waiting at a closed site €30".
- The floor text "(floored at ×0.85, or ×1.15 under 40 km)" also shows on long lanes: R00683 is 609 km at exactly 1.15×, which reads as if the short-lane floor applied. Show only the floor that applies.
- `fmtEur` drops the decimals on whole euros: "−€25" next to "€316.10".
- The race notes are out of order (Wed, Wed, Thu, Mon), and Monday is before the feed starts.
- The 390 px overflow on two tabs.
- The duplicate `.part .eff` rule.
- Tighten the `prepare.py` money assert from €10,000 to "nets + cancelled-order lines == ledger" to the cent.

## 3. Performance and robustness (measured)

- Scrubbing the whole week forwards and backwards in 60-minute steps costs **1.3 ms a frame**. Zooming costs 2.9 ms. There is no jank.
- The console has no errors, and every asset returns 200.
- The tour runs through all 8 steps without errors and closes cleanly.
- `#decision/R00676` and `#week@3720` work through `hashchange`.

## 4. Look and legibility (frontend-design skill)

The design is still specific to the subject: polar-night ground, birch text, amber/green/red with strict roles, and Fraunces with Plex.
The fixes made it calmer and more consistent. The scoreboard is now one prose line, the effect column is prose, there is one h1 weight, and contrast is AA throughout.
**Clearly designed, not generic.**

What still holds it back:
- **Projector distance.** Body text in the panels is 13.5 px and the chips, table and feed are 12 px. That is fine on a laptop but small from the back of a room.
  The map labels (12–14 px) and the 34 px rail margin read well. For a projected demo, one `html { font-size }` step up (or `zoom: 1.15` at 1920
  wide) would help more than any other change.
- **The map's empty half.** At 1440 Finland fills a third of the map panel. The hint and the tour box cover the west coast, where the cars run,
  while the east (Russia) is empty. Dock the hint, the tour box and the legend on the right side of the map.
- **The 30-second newcomer test.**
  - On a tall screen, it passes: subtitle, hint, "Take the guided tour", and the rail labels in plain words.
  - On a laptop, it is borderline. N7 removes the only sentence about the challenge, and N1 makes the first thing the hint asks for fail silently.
  - With N1, N2 and N7 fixed, it passes.

## 5. Must not regress

- The on-time numbers from the ledger: rail end 97.2%, 10 late, 356 won (won minus cancelled), 360 cars.
- Per-order money: R00676 **€21.21**, R00683 **−€25.00**, R00693 €199.80. Bundle shares are equal splits.
- Replay as a pure function of `t` (the end margin is €17,442.75 to the cent), and 1–3 ms frames.
- The exact/≈ tags with the 737/1,030 framing, the gig history, the decline badge and filter, and the delivery-hours chip.
- AA contrast (faint #7D93AB), the 6-step type scale, sans effect prose, one h1 weight, the single scoreboard, reduced motion, and the load-error page.
- The FINDINGS-matched How-it-works numbers listed in REVIEW.md §8.

## Screenshots (`review-shots-2/`)

| File | What it shows |
|---|---|
| `week-first-1440` | first visit |
| `week-wed-1440`, `week-wed-1280` | timeline letterboxed |
| `week-end-1440` | 97.2% / 10 late; "Tue 2 2" feed times |
| `week-1920` | timeline off-screen |
| `tour-late-1440` | tour box overflow, "2 14:52" feed times |
| `dec-R00683-tall` | gig history |
| `dec-R00693-tall` | trade-in late against its own window |
| `dec-R00009-tall` | bundle share |
| `dec-R00028-tall` | decline |
| `dec-R00676-tall` | €21.21, delivery-hours chip |
| `system-1440` | effect column |
| `race-1440` | €13k end values, footnote overprint |
| `challenge-1440` | step 5 alone, zig-zag road |
| `week-390`, `dec-390` | narrow screens |
