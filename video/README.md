# The video

A presentation video for Spread with no presenter: every claim is on screen, with its evidence and its source line. Made with [Remotion](https://remotion.dev) (React → MP4), 1920×1080, 30 fps, about 4½ minutes, 15 scenes. It uses the demo's look: the night palette, amber headlights, Fraunces, IBM Plex Sans and Mono, and the real Finland map.

The output is `out/bahn-spread.mp4`.

## Fill in the final's result, then re-render

1. Edit `src/final.ts`. Fill the five fields of `FINAL`: `rank`, `rankedTeams`, `marginEur`, `orders`, `onTimePct`. A field left `null` shows as `__`. The best ranking round, `BEST_ROUND`, is in the same file.
2. Run `./render.sh` from this folder. It writes `out/bahn-spread.mp4` in about 5 minutes on 16 cores.

The result appears in two places: the dashed tile in scene 2 ("The result") and the last scene.

## Preview, edit, render

```sh
./render.sh                      # the full video -> out/bahn-spread.mp4
./render.sh draft                # half resolution, faster -> out/draft.mp4
./render.sh still formula 650    # one frame of one scene -> out/stills/formula-650.png
```

`render.sh` takes Node and Chromium from nixpkgs through `nix build`, so nothing is installed permanently. On the first run it also points Remotion's bundled ffmpeg at nixpkgs' glibc, gcc-lib and zlib with patchelf. That bundled ffmpeg is a generic Linux binary, and NixOS cannot run it otherwise. For the interactive studio, get a Node shell and run `npx remotion studio src/index.ts`. Outside NixOS, the plain `npx remotion render src/index.ts Main out/bahn-spread.mp4` works.

| Path | What it is |
|---|---|
| `src/final.ts` | The final's result: the only thing to fill in. |
| `src/Root.tsx` | The scene list and each scene's duration. Each scene is also its own composition, `scene-<id>`, for stills. |
| `src/scenes1.tsx` | The hook (the real week on the map), the claim, the result, and how the system decides. |
| `src/scenes2.tsx` | Idea 1 (cost model), the decision rule on request R00013, idea 2 (prices), idea 3 (fees), idea 4 (safe cars, bundles). |
| `src/Ablation.tsx` | The final's code on the same 10 dev weeks, with one idea switched off per row (deck slide 7). |
| `src/scenes3.tsx` | How we know, the test final, robustness, limits, the close. |
| `src/MapWeek.tsx` | Finland and the week's cars, drawn for any world minute. |
| `src/ui.tsx`, `src/theme.ts` | The scene frame, the animation helpers, the palette and fonts. |
| `prepare.py` | Builds `src/data/*.json` from `../demo/assets/` and the main checkout's `data/runs.jsonl`. Standard library only. |

## Where the numbers come from

Every number comes from the repository. Each scene's source line names the file: `docs/deck/slides.md` and `docs/deck/numbers.json`, `tracks/*/FINDINGS.md` (ranking round 12 is in `tracks/orch/FINDINGS.md`, 04:37 UTC), and the test final's week in `demo/assets/`. The 40 unseen weeks in the robustness scene are the `b89-main` rows of `data/runs.jsonl`. Their mean and lowest week match FINDINGS (96.1% on time, lowest 92.4%, €17,308 a week).

## Scenes

| # | Scene | Seconds | What it shows |
|---|---|---:|---|
| 0 | hook | 17 | The test final's real week on the map of Finland: requests, cars, deliveries, margin counting up. |
| 1 | claim | 18 | The approach in one sentence and the four ideas. |
| 2 | result | 18 | The final (placeholder until filled in), the best ranking round, the test final, 40 unseen weeks. |
| 3 | flow | 18 | How a request flows through the parts; the desk keeps the books. |
| 4 | idea1-cost | 20 | The learned cost model: why (1.19 × vs 0.92 ×), fee error, effect. |
| 5 | formula | 23 | The quote rule built term by term on request R00013, and the expected-margin curve over prices. |
| 6 | idea2-prices | 19 | Day-to-day price levels, the level update, same-day quotes, effect. |
| 7 | idea3-fees | 19 | The flat fee against the hourly ladder, why drivers wait, effect. |
| 8 | idea4-cars | 20 | What breaks at 55% more orders, safe cars, bundles, effect. |
| 9 | ablation | 22 | The final's code on the same 10 weeks with one idea off per row. |
| 10 | method | 14 | Mean margin per week on the same 40 worlds at each adopted step; the rules. |
| 11 | testfinal | 19 | The gap the live leaderboard showed and the fix. |
| 12 | robust | 18 | 40 unseen weeks, the restart rehearsal, latency. |
| 13 | limits | 18 | What did not work, what would break it, what we don't know. |
| 14 | close | 11 | The approach again, the final's result, the best round. |
