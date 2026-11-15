import { Config } from "@remotion/cli/config";
// NixOS: use nixpkgs chromium instead of Remotion's downloaded headless shell (set by the render script).
if (process.env.REMOTION_BROWSER) Config.setBrowserExecutable(process.env.REMOTION_BROWSER);
Config.setVideoImageFormat("jpeg");
Config.setJpegQuality(92);
Config.setChromiumOpenGlRenderer("angle");
