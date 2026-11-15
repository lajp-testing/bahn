import React from "react";
import { useCurrentFrame } from "remotion";
import { C, F, eur } from "./theme";
import { In, Label, prog, Scene } from "./ui";

// The final's code on the same 10 dev weeks, each row with one idea switched off (docs/deck/slides.md, slide 7).
// [idea switched off, margin €, change €, orders a week, on time mean %, lowest week %, full system ahead in N of 10]
const ROWS: [string, number, number, number, number, number, number][] = [
  ["expected-margin quoter (fixed markup)", 118016, -59027, 259, 93.0, 87.1, 10],
  ["bundles", 138985, -38058, 359, 96.8, 94.5, 10],
  ["note reader", 141823, -35219, 320, 97.0, 94.6, 10],
  ["learned cost model (hand-fit formula)", 148742, -28301, 360, 94.9, 93.4, 10],
  ["flat fees (rising hourly ladder)", 150450, -26592, 403, 96.8, 95.6, 10],
  ["same-day at 8 h of slack", 152203, -24839, 332, 97.5, 95.9, 10],
  ["cost tilt", 168296, -8746, 398, 95.6, 92.8, 9],
  ["dealer trust", 171617, -5425, 413, 96.6, 95.2, 8],
  ["safe cars", 173827, -3216, 390, 96.6, 94.9, 7],
  ["queue limit", 177085, 42, 409, 96.2, 92.7, 7],
];

export const Ablation: React.FC<{ n: number }> = ({ n }) => {
  const f = useCurrentFrame();
  const top = 290, rh = 52, X0 = 1050, BW = 380, max = 60000;
  const cols = { orders: 1400, ontime: 1450, ahead: 1690 };
  const head = (x: number, s: string, align: "left" | "right" = "right") => (
    <div style={{ position: "absolute", left: align === "right" ? x - 200 : x, width: 200, textAlign: align, top: top - 44 }}>
      <Label style={{ fontSize: 17 }}>{s}</Label></div>
  );
  return (
    <Scene n={n} kicker="Effect of each idea · with and without, same weeks"
      title="Switch one idea off and the margin falls: same 10 weeks"
      source="The final's code on the 10 dev weeks, one idea switched off per row: docs/deck/slides.md slide 7 (main 6be5ef6). On time: mean / lowest week. Ahead: weeks where the full system earned more.">
      <In at={20}>
        <div style={{ position: "absolute", left: 120, top: top - 44 }}><Label style={{ fontSize: 17 }} color={C.headlight}>Idea switched off</Label></div>
        <div style={{ position: "absolute", left: X0 - BW, width: BW, textAlign: "right", top: top - 44 }}><Label style={{ fontSize: 17 }} color={C.headlight}>Margin lost over 10 weeks</Label></div>
        {head(cols.orders, "orders/week")}{head(cols.ontime + 190, "on time")}{head(cols.ahead + 110, "full ahead")}
        <div style={{ position: "absolute", left: 120, right: 120, top: top - 12, borderTop: `1px solid ${C.rule}` }} />
        <div style={{ position: "absolute", left: 120, top: top, fontSize: 25, color: C.birch, fontWeight: 600, lineHeight: `${rh}px` }}>Full system: €177,043</div>
        <div style={{ position: "absolute", left: cols.orders - 200, width: 200, textAlign: "right", top, fontFamily: F.mono, fontSize: 24, lineHeight: `${rh}px`, color: C.birch }}>401</div>
        <div style={{ position: "absolute", left: cols.ontime, top, fontFamily: F.mono, fontSize: 24, lineHeight: `${rh}px`, color: C.birch }}>97.2 / 95.5%</div>
      </In>
      <div style={{ position: "absolute", left: X0, top: top + rh - 6, height: ROWS.length * rh + 6, borderLeft: `1px solid ${C.frost}`, opacity: prog(f, 20, 10) }} />
      {ROWS.map(([name, , d, o, m, lo, ahead], i) => {
        const at = 50 + i * 14;
        const p = prog(f, at, 28);
        const y = top + (i + 1) * rh;
        const w = (Math.abs(d) / max) * BW * p;
        const bad = lo < 90;
        return (
          <div key={name} style={{ opacity: prog(f, at - 6, 10) }}>
            <div style={{ position: "absolute", left: 120, top: y, width: X0 - 120 - BW - 10, fontSize: 24, color: C.frost, lineHeight: `${rh}px`, whiteSpace: "nowrap" }}>{name}</div>
            <div style={{ position: "absolute", left: d < 0 ? X0 - w : X0, top: y + 14, height: rh - 28, width: Math.max(w, 2), background: d < 0 ? (i === 0 ? C.headlight : C.coast) : C.frost, borderRadius: 2 }} />
            <div style={{ position: "absolute", left: d < 0 ? X0 + 14 : X0 + 14, top: y, fontFamily: F.mono, fontSize: 24, lineHeight: `${rh}px`, color: i === 0 ? C.headlight : C.birch }}>
              {d < 0 ? "−" : "+"}{eur(Math.abs(d) * p)}</div>
            <div style={{ position: "absolute", left: cols.orders - 200, width: 200, textAlign: "right", top: y, fontFamily: F.mono, fontSize: 24, lineHeight: `${rh}px`, color: C.frost }}>{o}</div>
            <div style={{ position: "absolute", left: cols.ontime, top: y, fontFamily: F.mono, fontSize: 24, lineHeight: `${rh}px`, color: C.frost }}>
              {m.toFixed(1)} / <span style={{ color: bad ? C.late : C.frost }}>{lo.toFixed(1)}%</span></div>
            <div style={{ position: "absolute", left: cols.ahead, top: y, fontFamily: F.mono, fontSize: 24, lineHeight: `${rh}px`, color: C.frost }}>{ahead} of 10</div>
          </div>
        );
      })}
      <In at={260} style={{ position: "absolute", left: 120, right: 120, top: top + 11 * rh + 18 }}>
        <div style={{ fontSize: 25, color: C.frost, lineHeight: 1.4 }}>
          Without the quoter one week drops to <span style={{ color: C.late, fontWeight: 600 }}>87.1%</span>, unranked. The queue limit earns nothing on its own, but it keeps the weakest week safe.
        </div>
      </In>
    </Scene>
  );
};
