# The video

A presentation video for Spread with no presenter: every claim is on screen, with its evidence and its source line. Made with [Remotion](https://remotion.dev) (React → MP4), 1920×1080, 30 fps, about 4 minutes. It uses the demo's look: the night palette, amber headlights, Fraunces, IBM Plex Sans and Mono, and the real Finland map.

The output is `out/bahn-spread.mp4`.

## Fill in the final's result, then re-render

1. Edit `src/final.ts`. Fill the five fields: `rank`, `rankedTeams`, `marginEur`, `orders`, `onTimePct`. A field left `null` shows as `__`.
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
| `src/scenes3.tsx` | How we know, the test final, robustness, limits, the close. |
| `src/MapWeek.tsx` | Finland and the week's cars, drawn for any world minute. |
| `src/ui.tsx`, `src/theme.ts` | The scene frame, the animation helpers, the palette and fonts. |
| `prepare.py` | Builds `src/data/*.json` from `../demo/assets/` and the main checkout's `data/runs.jsonl`. Standard library only. |

## Where the numbers come from

Every number comes from the repository. Each scene's source line names the file: `docs/deck/slides.md` and `docs/deck/numbers.json`, `tracks/*/FINDINGS.md` (ranking round 12 is in `tracks/orch/FINDINGS.md`, 04:37 UTC), and the test final's week in `demo/assets/`. The 40 unseen weeks in the robustness scene are the `b89-main` rows of `data/runs.jsonl`. Their mean and lowest week match FINDINGS (96.1% on time, lowest 92.4%, €17,308 a week).
