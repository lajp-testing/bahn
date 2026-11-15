#!/usr/bin/env bash
# Render on NixOS: Node, Chromium and patchelf from nixpkgs, nothing installed permanently.
#   ./render.sh                 full video -> out/bahn-spread.mp4
#   ./render.sh draft           half resolution -> out/draft.mp4
#   ./render.sh still <scene> <frame>   one PNG -> out/stills/<scene>-<frame>.png
set -euo pipefail
cd "$(dirname "$0")"
NODE=$(nix build --no-link --print-out-paths nixpkgs#nodejs_22)
export PATH="$NODE/bin:$PATH"
export REMOTION_BROWSER="$(nix build --no-link --print-out-paths nixpkgs#chromium)/bin/chromium"
[ -d node_modules ] || npm ci --no-audit --no-fund
# Remotion's bundled ffmpeg is a generic Linux binary: point it at nixpkgs' loader and libraries (idempotent).
D=node_modules/@remotion/compositor-linux-x64-gnu
if ! "$D/ffmpeg" -version >/dev/null 2>&1; then
  PE="$(nix build --no-link --print-out-paths nixpkgs#patchelf)/bin/patchelf"
  GLIBC="$(nix build --no-link --print-out-paths nixpkgs#glibc | head -1)/lib"
  GCC="$(nix build --no-link --print-out-paths nixpkgs#stdenv.cc.cc.lib)/lib"
  Z="$(nix build --no-link --print-out-paths nixpkgs#zlib | head -1)/lib"
  for b in ffmpeg ffprobe remotion; do "$PE" --set-interpreter "$GLIBC/ld-linux-x86-64.so.2" "$D/$b"; done
  for b in ffmpeg ffprobe remotion "$D"/*.so; do b="${b#$D/}"; "$PE" --set-rpath "\$ORIGIN:$GCC:$GLIBC:$Z" "$D/$b"; done
fi
mkdir -p out/stills
case "${1:-full}" in
  full)  npx remotion render src/index.ts Main out/bahn-spread.mp4 --crf=20 --concurrency=16 ;;
  draft) npx remotion render src/index.ts Main out/draft.mp4 --scale=0.5 --crf=28 --concurrency=16 ;;
  still) npx remotion still src/index.ts "scene-$2" "out/stills/$2-$3.png" --frame="$3" ;;
  *) echo "usage: $0 [full|draft|still <scene> <frame>]"; exit 1 ;;
esac
