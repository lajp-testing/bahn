import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { C, F, eur } from "./theme";
import { B, Body, Count, Effect, Grain, In, Label, prog, Scene } from "./ui";
import { MapWeek, WEEK_MIN, clock, stats } from "./MapWeek";
import { FINAL } from "./final";

// ---------- 0 · the hook: the real week flowing across Finland ----------
export const Hook: React.FC = () => {
  const f = useCurrentFrame();
  const minute = interpolate(f, [24, 404], [0, WEEK_MIN], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const s = stats(minute);
  const out = interpolate(f, [500, 510], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const stat = (label: string, v: string, c: string = C.birch) => (
    <div>
      <Label>{label}</Label>
      <div style={{ fontFamily: F.mono, fontSize: 54, fontWeight: 600, color: c, marginTop: 4, fontVariantNumeric: "tabular-nums" }}>{v}</div>
    </div>
  );
  return (
    <AbsoluteFill style={{ background: C.night, color: C.birch, fontFamily: F.sans, opacity: out }}>
      <Grain />
      <MapWeek minute={minute} x={1150} y={40} scale={1.02} />
      <div style={{ position: "absolute", left: 120, top: 110, width: 980 }}>
        <In at={0}><div style={{ fontFamily: F.mono, fontSize: 22, letterSpacing: "0.14em", textTransform: "uppercase", color: C.headlight }}>
          Spread · Junction 2026 · team pelaaja juhlii</div></In>
        <In at={6} dur={24}><h1 style={{ fontFamily: F.serif, fontWeight: 560, fontSize: 76, lineHeight: 1.06, margin: "20px 0 0", letterSpacing: "-0.015em" }}>
          One week of car transport across Finland, run by our dispatcher.</h1></In>
        <In at={60}><Body style={{ marginTop: 30, maxWidth: 900 }}>
          Each <B c={C.headlight}>ring</B> is a dealer's request for a price. Each <B c={C.headlight}>moving dot</B> is a car
          a freelance driver carries for us; it turns <B c={C.ontime}>green</B> on time, <B c={C.late}>red</B> late.</Body></In>
        <In at={150} style={{ marginTop: 56 }}>
          <div style={{ fontFamily: F.mono, fontSize: 30, color: C.headlight, fontVariantNumeric: "tabular-nums" }}>{clock(minute)}</div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "26px 40px", marginTop: 18, width: 820 }}>
            {stat("Requests", String(s.requests))}
            {stat("Orders won", String(s.won))}
            {stat("Delivered", String(s.delivered), C.ontime)}
            {stat("Margin", eur(s.margin))}
          </div>
        </In>
      </div>
      <In at={300} style={{ position: "absolute", left: 120, bottom: 70, width: 960 }}>
        <div style={{ fontSize: 28, color: C.birch, lineHeight: 1.4 }}>
          Saturday's test final, replayed from our own logs: <B c={C.headlight}>5th of 75 ranked teams</B>, 97.2% on time.
        </div>
      </In>
    </AbsoluteFill>
  );
};

// ---------- 1 · the claim and the four ideas ----------
const IDEAS = [
  ["Learn what each car will cost", "trained on 1.9 million of our own orders"],
  ["Quote the price with the most expected margin", "at the price dealers accept today"],
  ["Pay drivers one flat fee", "a raise ahead only makes drivers wait"],
  ["Take the cars that stay on time", "and let one driver carry two or three"],
];
export const Claim: React.FC = () => (
  <Scene n={1} kicker="Our approach in one sentence"
    title={<>We price each car over its own learned cost, and take only the work our drivers can deliver.</>} titleWidth={1500}>
    <div style={{ position: "absolute", left: 120, top: 420, right: 120, display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 36 }}>
      {IDEAS.map(([h, s], i) => (
        <In key={i} at={170 + i * 40}>
          <div style={{ borderTop: `2px solid ${C.headlight}`, paddingTop: 22 }}>
            <div style={{ fontFamily: F.mono, fontSize: 22, color: C.headlight }}>Idea {i + 1}</div>
            <div style={{ fontFamily: F.serif, fontSize: 38, lineHeight: 1.15, marginTop: 12, fontWeight: 520 }}>{h}</div>
            <div style={{ fontSize: 26, color: C.frost, marginTop: 14, lineHeight: 1.4 }}>{s}</div>
          </div>
        </In>
      ))}
    </div>
    <In at={330} style={{ position: "absolute", left: 120, bottom: 120, right: 120 }}>
      <Body>Each idea is kept only if it raises the margin on the same weeks, with no week below 90% on time.</Body>
    </In>
  </Scene>
);

// ---------- 2 · the result ----------
const blank = (v: number | null, fmt: (v: number) => string) => (v == null ? "__" : fmt(v));
export const finalLine = () => ({
  head: `Final: ${blank(FINAL.rank, String)} of ${blank(FINAL.rankedTeams, String)}`,
  sub: `${blank(FINAL.marginEur, (v) => eur(v))} margin · ${blank(FINAL.orders, String)} orders · ${blank(FINAL.onTimePct, (v) => v.toFixed(1))}% on time`,
  filled: FINAL.rank != null,
});
export const Result: React.FC = () => {
  const fl = finalLine();
  const tile = (at: number, big: React.ReactNode, what: string, detail: React.ReactNode) => (
    <In at={at}>
      <div style={{ borderTop: `1px solid ${C.rule}`, paddingTop: 22 }}>
        <div style={{ fontFamily: F.serif, fontSize: 52, fontWeight: 560, color: C.birch }}>{big}</div>
        <Label style={{ marginTop: 10 }} color={C.headlight}>{what}</Label>
        <div style={{ fontSize: 27, color: C.frost, marginTop: 12, lineHeight: 1.42 }}>{detail}</div>
      </div>
    </In>
  );
  return (
    <Scene n={2} kicker="The result" title="Every run ranked: on the board, in the test final, on weeks it never saw"
      source="Round 12: tracks/orch/FINDINGS.md (04:37 UTC). Test final: tracks/orch/finals/testfinal-20261114-1800. Unseen weeks: b89-main on rob-21..60, data/runs.jsonl.">
      <In at={20} style={{ position: "absolute", left: 120, top: 330, right: 120 }}>
        <div style={{ border: `2px dashed ${fl.filled ? C.headlight : C.coast}`, borderRadius: 6, padding: "26px 36px", display: "flex", alignItems: "baseline", gap: 40 }}>
          <div style={{ fontFamily: F.serif, fontSize: 72, fontWeight: 600, color: C.headlight }}>{fl.head}</div>
          <div style={{ fontFamily: F.mono, fontSize: 30, color: C.birch }}>{fl.sub}</div>
          <div style={{ marginLeft: "auto", fontFamily: F.mono, fontSize: 20, color: C.faint }}>the final, Sunday 07:00 UTC</div>
        </div>
      </In>
      <div style={{ position: "absolute", left: 120, top: 580, right: 120, display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 56 }}>
        {tile(70, <>3rd of 33</>, "Best ranking round · Sunday 06:00",
          <><B><Count to={79842} at={80} dur={45} fmt={(v) => eur(v)} /></B> over 5 runs, every run ranked, 95.3–97.6% on time.</>)}
        {tile(150, <>5th of 75</>, "Saturday's test final",
          <><B>€17,443</B> margin, 356 orders, 97.2% on time.</>)}
        {tile(230, <>40 of 40</>, "Weeks no part was tuned on",
          <><B>€17,308</B> and 399 orders a week, 96.1% on time, lowest 92.4%.</>)}
      </div>
    </Scene>
  );
};

// ---------- 3 · how the system decides ----------
type Box = { name: string; line: string; col: number; row: number; hl?: boolean };
const BOXES: Box[] = [
  { name: "Dealer request", line: "cars, lanes, a note; options with deadlines and list prices", col: 0, row: 0 },
  { name: "Note reader", line: "Finnish, Swedish, English → ready times, hours, licences", col: 1, row: 0 },
  { name: "Intake", line: "take a car only if drivers can deliver it on time", col: 2, row: 0, hl: true },
  { name: "Quoter", line: "the price with the most expected margin", col: 3, row: 0, hl: true },
  { name: "Dealer decides", line: "our price against a competitor's → order or lost", col: 4, row: 0 },
  { name: "Bundles", line: "up to 3 cars share one driver's gig", col: 4, row: 1, hl: true },
  { name: "Fees", line: "one flat fee per gig, at most two raises", col: 3, row: 1, hl: true },
  { name: "Driver books", line: "when the fee beats the driver's own cost", col: 2, row: 1 },
  { name: "Delivered", line: "on time, or the dealer gets a refund", col: 1, row: 1 },
];
export const Flow: React.FC = () => {
  const f = useCurrentFrame();
  const W = 300, G = 45, X0 = 120, Y = [300, 640], H = 180;
  const bx = (b: Box) => X0 + b.col * (W + G);
  return (
    <Scene n={3} kicker="How the system decides" title="A desk keeps the books; small parts make every decision"
      source="Code: dispatch/desk.py, reader.py, intake.py, pricing.py, learned3.py, bundles.py, fees.py. Practice and the live final use the same desk.">
      <svg width={1920} height={1080} style={{ position: "absolute", left: 0, top: 0 }}>
        {BOXES.slice(1).map((b, i) => {
          const a = BOXES[i];
          const p = prog(f, 30 + (i + 1) * 26, 14);
          let d: string;
          if (a.row === b.row) {
            const dir = b.col > a.col ? 1 : -1;
            const x1 = dir > 0 ? bx(a) + W : bx(a), x2 = dir > 0 ? bx(b) : bx(b) + W, y = Y[a.row] + H / 2;
            d = `M${x1},${y} L${x1 + (x2 - x1) * p},${y}`;
          } else {
            const x = bx(a) + W / 2, y1 = Y[0] + H, y2 = Y[1];
            d = `M${x},${y1} L${x},${y1 + (y2 - y1) * p}`;
          }
          return <path key={i} d={d} stroke={C.frost} strokeWidth={2} fill="none" opacity={0.8} />;
        })}
        {/* the learned cost model feeds the intake, the quoter and the fees */}
        {(() => {
          const p = prog(f, 290, 20);
          const y = (Y[0] + H + Y[1]) / 2;
          const xs = [bx(BOXES[2]) + W / 2, bx(BOXES[3]) + W / 2];
          return (
            <g opacity={p}>
              {xs.map((x, i) => <path key={i} d={`M${x},${y - 22} L${x},${Y[0] + H + 4}`} stroke={C.headlight} strokeWidth={2} strokeDasharray="5 5" />)}
              <path d={`M${xs[1]},${y + 22} L${xs[1]},${Y[1] - 4}`} stroke={C.headlight} strokeWidth={2} strokeDasharray="5 5" />
            </g>
          );
        })()}
      </svg>
      {BOXES.map((b, i) => (
        <In key={b.name} at={24 + i * 26} style={{ position: "absolute", left: bx(b), top: Y[b.row], width: W, height: H }}>
          <div style={{ height: "100%", background: C.panel, border: `1px solid ${b.hl ? C.coast : C.rule}`, borderRadius: 6, padding: "20px 22px" }}>
            <div style={{ fontFamily: F.serif, fontSize: 32, fontWeight: 560, color: b.hl ? C.birch : C.frost }}>{b.name}</div>
            <div style={{ fontSize: 22, color: C.frost, marginTop: 10, lineHeight: 1.38 }}>{b.line}</div>
          </div>
        </In>
      ))}
      <In at={290} style={{ position: "absolute", left: 120 + 2 * (W + G) - 10, top: (Y[0] + H + Y[1]) / 2 - 22, width: 2 * W + G + 20 }}>
        <div style={{ background: C.night, border: `1px solid ${C.headlight}`, borderRadius: 22, padding: "6px 20px", textAlign: "center",
          fontFamily: F.mono, fontSize: 21, color: C.headlight }}>learned cost model: driver fee, late risk</div>
      </In>
      <In at={330} style={{ position: "absolute", left: 120, top: 870, right: 120 }}>
        <Body style={{ fontSize: 28 }}>The <B>desk</B> keeps one account of requests, orders, gigs and deliveries; it asks the parts for every decision.</Body>
      </In>
    </Scene>
  );
};
