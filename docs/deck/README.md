# The jury deck

10 slides, 16:9. The source is `slides.md`; everything else is generated from it, apart from `flow.svg` and `deck.css`.

| File | What it is |
|---|---|
| `slides.md` | The deck's text. One slide per `---`. **Edit here.** |
| `flow.svg` | The system diagram (slide 2), drawn by hand. Edit its text directly. |
| `deck.css` | The look: type, colours, blocks (`tiles`, `effect`, `caveat`, `formula`, `cols`). |
| `charts.py` | Draws `charts/*.svg` from `data/runs.jsonl` and the recorded test-final feed; writes `numbers.json`. |
| `build.py` | `slides.md` → `deck.html` (one self-contained file: SVGs inlined, no network) and `deck.pdf`. |
| `deck.html`, `deck.pdf` | The built deck. Open `deck.html` in a browser: ← → / space / PageUp-Down / Home / End, `f` for full screen, click right or left third. |

## Build

```sh
python3 docs/deck/charts.py                                              # refresh charts from saved weeks (optional)
nix shell nixpkgs#chromium --command python3 docs/deck/build.py --pdf    # deck.html + deck.pdf
python3 docs/deck/build.py                                               # deck.html only, no chromium needed
```

`charts.py` reads `$SPREAD_DATA/runs.jsonl` (default: the main checkout's `data/`). Standard library only.

## Sunday 09:40: fill in the final

One edit: in `slides.md`, slide 1, the line under `FILL IN AT ABOUT 09:40`:

```
- **Final: __ of __** €__ margin · __ orders · __% on time
```

Then rebuild (`build.py --pdf`) and commit `slides.md`, `deck.html`, `deck.pdf`.

## Where each number comes from

Every slide's last line names its sources. In short:

| Slide | Numbers | Source |
|---|---|---|
| 1 | Ranking round €84,857, 96.4% on time, 2,018 orders | our 5 board runs `b81-board-s9-1..5` in `data/runs.jsonl` (`numbers.json` → `board_saturday_2100`) |
| 1 | "9th of about 230" | the public board, as recorded by the orchestrator. **Not in any findings file: check it.** |
| 1 | Test final 5th of 75, €17,443, 356 orders, 97.2% | `tracks/orch/finals/testfinal-20261114-1800/README.md`; `charts.py` re-reads it from the feed |
| 1, 9 | 40 unseen weeks: €17,308 / week, 399 orders, 96.1%, lowest 92.4% | `b89-main` on rob-21..60, `numbers.json` → `unseen40_b89`; tracks/orch/FINDINGS.md 21:50 |
| 2 | Formula | `dispatch/pricing.py` (`ProfitQuoter.prices`, `chance`, `factor`, the level update), `dispatch/policies/main.py` defaults |
| 3 | Offline errors 0.309 / 0.274 / 0.232, log loss 0.133 / 0.121 / 0.101 | tracks/ml/FINDINGS.md "Offline result" |
| 3 | 1.19 × vs 0.92 × typical | docs/pricing-fix-report.md |
| 3 | +€32,271, 29 of 40, 390 vs 364 orders, lowest 90.2 → 92.0 | `b37-fee3` vs `t3s15-safe-flat15`, FINDINGS 14:00 (charts.py reproduces it) |
| 3 | Model 5: +€14,444 in-sample, −€1,875 unseen, lowest weeks | FINDINGS 21:30 and 21:40 |
| 4 | Chart: four variants vs `b37-fee3` on the same 30 dev + rob weeks | `numbers.json` → `sameday_vs_b37_30wk` |
| 4 | +€31,975 over 40, 31 ahead, lowest 93.8%; 67% vs 34%; 4,117 requests | FINDINGS 15:05 |
| 4 | Day levels 1.10–1.67 × list | tracks/t2/FINDINGS.md (first section) |
| 5 | 84 → 306 min, 1.11 → 1.18 | tracks/t3/FINDINGS.md (hold-the-ladder study, `s11_viewratio.py`) |
| 5 | 86 → 7–12 min, 7.0% → about 5.9% | tracks/t3/FINDINGS.md (flat-fee screens `t3s14`) |
| 5, 6 | +€69,993 (+14.3%), 38 of 40, 364 vs 277 orders | `t3s15-safe-flat15` vs `t3s10-calm`, FINDINGS 13:40 (charts.py reproduces it) |
| 6 | On time by kind of car; €127,567 vs €103,440 | tracks/t1/FINDINGS.md, `t1s13-flood` vs `t1s11-base` |
| 6 | 0.79 × / 1.0% vs 0.97 × / 3.7% | tracks/t3/FINDINGS.md (bundle settings study, 40 saved `b46` weeks) |
| 6 | +6.4% (€74,982 vs €70,496) | tracks/t5/FINDINGS.md, `b13-bundle2` vs `t3s5-model2`, 7 dev weeks |
| 7 | Chart: the day's 8 steps on the same 40 worlds | `numbers.json` → `steps`. The step gains match FINDINGS except model 4 + car 1.1: +€19,828 on these 40 weeks, +€18,349 in FINDINGS (there on dev + rob-01..30) |
| 7 | +€3,166, 91.7% | docs/jury.md §3 and §5 |
| 8 | Scatter of 75 ranked teams | `leaderboard-feed.sse.gz`, last frame |
| 8 | 113 orders, €48 / €19, 110 cars, 73% at the floor | ANALYSIS.md, sections 1–3 |
| 8 | +€31,187, 34 of 40; holdout +€10,243, 9 of 10; rob-21..30 +€5,993 | FINDINGS 19:45 and 21:40 |
| 9 | Chart: +€14,342, 20 of 30 | `b89-main` vs `b68` on rob-21..50, `numbers.json` → `unseen_b89_vs_b68` |
| 9 | €11,288 / 95.2% vs €11,802 / 96.5%; 121 ms; 564 ms | tracks/t3/LIVE.md (`t3-live-2`, `t3-live-ref2`, `t3-live-5`) |
| 10 | Rejected ideas | docs/jury.md §5, tracks/*/FINDINGS.md |
| 10 | D01 trust 25 → 12, 60% → 30%; price war 23% vs 32–48% | ANALYSIS.md section 3 and section 1 ("Our own days") |

## Markdown subset

See the docstring of `build.py`: `---` slide, `::: name` … `:::` blocks (nest), `+++` next column, `![alt](x.svg)` inlined SVG, lists, tables, `**bold**`, `` `code` ``. A line starting with `<` passes through as HTML.
