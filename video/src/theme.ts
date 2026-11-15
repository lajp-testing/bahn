import { continueRender, delayRender, staticFile } from "remotion";

// The demo's palette, "kartta yöllä": a road map after dark (demo/style.css).
export const C = {
  night: "#0A141F", land: "#142A44", sea: "#0C1A2C", coast: "#33608C",
  birch: "#EFE9DC", frost: "#8FA6BE", faint: "#7D93AB", headlight: "#F0A532",
  ontime: "#54C08A", late: "#EF6D6D", rule: "#223349", panel: "#0E1B2C",
};
export const F = {
  serif: "Fraunces, Georgia, serif",
  sans: "'IBM Plex Sans', sans-serif",
  mono: "'IBM Plex Mono', monospace",
};

const faces: [string, string, FontFaceDescriptors][] = [
  ["Fraunces", "fonts/Fraunces-var.woff2", { weight: "100 900" }],
  ["IBM Plex Sans", "fonts/IBMPlexSans-var.woff2", { weight: "400 600" }],
  ["IBM Plex Mono", "fonts/IBMPlexMono-400.woff2", { weight: "400" }],
  ["IBM Plex Mono", "fonts/IBMPlexMono-600.woff2", { weight: "600" }],
];
if (typeof document !== "undefined") {
  const h = delayRender("fonts");
  Promise.all(faces.map(([fam, file, d]) => {
    const f = new FontFace(fam, `url(${staticFile(file)}) format("woff2")`, d);
    return f.load().then((l) => document.fonts.add(l));
  })).then(() => continueRender(h)).catch((e) => { console.error(e); continueRender(h); });
}

export const eur = (v: number, d = 0) => "€" + v.toLocaleString("en-US", { minimumFractionDigits: d, maximumFractionDigits: d });
export const ord = (n: number) => n + (n % 100 >= 11 && n % 100 <= 13 ? "th" : ["th", "st", "nd", "rd"][n % 10] ?? "th");
