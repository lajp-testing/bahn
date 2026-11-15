import React from "react";
import { useCurrentFrame } from "remotion";
import nums from "./data/numbers.json";
import { C, F, eur, ord } from "./theme";
import { B, Body, Effect, In, Label, prog, Scene } from "./ui";
import { finalLine } from "./scenes1";
import { BEST_ROUND as BR } from "./final";

// ---------- 9 · how we know: the same 40 worlds at every adopted step ----------
const STEP_NAMES = ["start", "safe cars + flat fees", "learned cost model", "same-day + cost tilt", "model 4, tilt 1.1", "cheaper short cars", "model 5", "higher limits"];
export const Method: React.FC = () => {
  const f = useCurrentFrame();
  const st = nums.steps as { at: string; mean_week_eur: number; lowest_on_time: number[] }[];
  const W = 1100, H = 420, lo = 11000, hi = 18000;
  const X = (i: number) => 40 + i * ((W - 80) / (st.length - 1)), Y = (v: number) => H - ((v - lo) / (hi - lo)) * H;
  const p = prog(f, 40, 150);
  const k = p * (st.length - 1);
  const pts = st.map((s, i) => [X(i), Y(s.mean_week_eur)]);
  const shown = Math.floor(k);
  let d = `M${pts[0][0]},${pts[0][1]}`;
  for (let i = 1; i <= shown; i++) d += ` L${pts[i][0]},${pts[i][1]}`;
  if (shown < st.length - 1) {
    const u = k - shown, a = pts[shown], b = pts[shown + 1];
    d += ` L${a[0] + (b[0] - a[0]) * u},${a[1] + (b[1] - a[1]) * u}`;
  }
  return (
    <Scene n={10} kicker="How we know" title="Every idea is a switch, judged on the same 40 worlds with and without it"
      source="Mean margin per week over the same 40 worlds (10 dev, 20 rob, 10 holdout) at each adopted step of 14 November; data/runs.jsonl via docs/deck/numbers.json. Model 5's step is partly in-sample.">
      <div style={{ position: "absolute", left: 120, top: 300 }}>
        <Label color={C.headlight}>Margin per week, mean of the same 40 worlds</Label>
        <svg width={W} height={H + 120} style={{ overflow: "visible", marginTop: 20 }}>
          {[12000, 14000, 16000, 18000].map((v) => (
            <g key={v}><line x1={0} x2={W} y1={Y(v)} y2={Y(v)} stroke={C.rule} />
              <text x={-12} y={Y(v) + 6} fill={C.faint} fontFamily={F.mono} fontSize={18} textAnchor="end">{eur(v / 1000)}k</text></g>
          ))}
          <path d={d} fill="none" stroke={C.headlight} strokeWidth={4} strokeLinejoin="round" />
          {st.map((s, i) => i <= k + 0.001 && (
            <g key={i}>
              <circle cx={pts[i][0]} cy={pts[i][1]} r={7} fill={C.headlight} />
              <text x={pts[i][0]} y={pts[i][1] - 18} fill={C.birch} fontFamily={F.mono} fontSize={20} textAnchor="middle">{eur(s.mean_week_eur)}</text>
              <text transform={`translate(${pts[i][0] - 4},${H + 24}) rotate(30)`} fill={C.frost} fontFamily={F.sans} fontSize={19}>{s.at} {STEP_NAMES[i]}</text>
            </g>
          ))}
        </svg>
      </div>
      <div style={{ position: "absolute", left: 1330, top: 300, width: 470 }}>
        {[
          ["Off by default", "With its switch off, the code must reproduce the mainline to the cent before a comparison counts."],
          ["Paired weeks", "Both versions on the same seeds. Total margin and the weakest week decide."],
          ["The weakest week can veto", "Earlier urgent fees made +€3,166 but put a week at 91.7%: rejected."],
        ].map(([h, s], i) => (
          <In key={h} at={200 + i * 70} style={{ marginBottom: 30 }}>
            <div style={{ fontFamily: F.serif, fontSize: 32, fontWeight: 560 }}>{h}</div>
            <div style={{ fontSize: 25, color: C.frost, marginTop: 6, lineHeight: 1.4 }}>{s}</div>
          </In>
        ))}
      </div>
    </Scene>
  );
};

// ---------- 10 · the test final taught us the gap ----------
export const TestFinal: React.FC = () => {
  const f = useCurrentFrame();
  const tf = nums.testfinal;
  const bar = (at: number, label: string, v: number, c: string) => {
    const p = prog(f, at, 30);
    return (
      <div style={{ marginTop: 22 }}>
        <div style={{ fontSize: 24, color: C.frost }}>{label}</div>
        <div style={{ display: "flex", alignItems: "center", gap: 14, marginTop: 6 }}>
          <div style={{ height: 34, width: 1.15 * v * p, background: c, borderRadius: 2 }} />
          <div style={{ fontFamily: F.mono, fontSize: 30, color: C.birch }}>{Math.round(v * p)} orders</div>
        </div>
      </div>
    );
  };
  return (
    <Scene n={11} kicker="What the test final taught us" title="The live leaderboard showed our gap: about 110 short, cheap cars"
      source="tracks/orch/finals/testfinal-20261114-1800/ANALYSIS.md (leaderboard feed recorded every 2 s); b68-floor075-short095-carshort085 vs b52-fee4-car110, tracks/orch/FINDINGS.md 19:45.">
      <div style={{ position: "absolute", left: 120, top: 300, width: 800 }}>
        <In at={20}><Label color={C.headlight}>Saturday's test final</Label></In>
        {bar(30, "the leader", tf.top_orders, C.frost)}
        {bar(50, "us, 5th of 75", tf.our_orders, C.headlight)}
        <In at={120} style={{ marginTop: 34 }}><Body>The leader's <B>113 extra orders</B> brought €48 of revenue and €19 of margin each. Only one reading fits orders, revenue and cost: cars under 100 km at the typical fee.</Body></In>
      </div>
      <div style={{ position: "absolute", left: 1020, top: 300, width: 780 }}>
        <In at={250}><Label color={C.headlight}>Why we lost them</Label>
          <Body style={{ marginTop: 8 }}><B>73%</B> of our one-car gigs opened exactly at our 0.85 fee floor. Short cars were dear to move, so dear to quote.</Body></In>
        <In at={350} style={{ marginTop: 26 }}><Label color={C.headlight}>The fix, that evening</Label>
          <Body style={{ marginTop: 8 }}>Fee floors <B>0.75 / 0.95</B>, and lanes under 100 km costed at <B>0.85 ×</B>.</Body></In>
      </div>
      <Effect at={420} style={{ position: "absolute", left: 120, right: 120, top: 830 }}>
        <B c={C.headlight}>+€31,187</B> over 40 weeks, ahead in 34; on the 10 holdout worlds +€10,243 (9 of 10).
      </Effect>
    </Scene>
  );
};

// ---------- 11 · robust ----------
export const Robust: React.FC = () => {
  const f = useCurrentFrame();
  const un = (nums.unseen as [string, number, number, number, boolean][]).slice().sort((a, b) => a[2] - b[2]);
  const W = 1000, lo = 88, hi = 100, X = (v: number) => ((v - lo) / (hi - lo)) * W;
  return (
    <Scene n={12} kicker="Robust" title="It holds on weeks it has never seen, and rejoins after a crash"
      source="b89-main (the final's code) on rob-21..60, data/runs.jsonl; restart: tracks/orch/FINDINGS.md 23:55 and tracks/t3/LIVE.md.">
      <div style={{ position: "absolute", left: 120, top: 300, width: W }}>
        <In at={20}><Label color={C.headlight}>On time, each of 40 unseen weeks · one dot a week</Label></In>
        <svg width={W} height={220} style={{ overflow: "visible", marginTop: 30, transform: "scale(1)" }}>
          <rect x={0} y={20} width={X(90)} height={140} fill={C.late} opacity={0.08} />
          <line x1={X(90)} x2={X(90)} y1={10} y2={170} stroke={C.late} strokeDasharray="6 6" />
          <text x={X(90) - 10} y={10} fill={C.late} fontFamily={F.mono} fontSize={19} textAnchor="end">unranked</text><text x={X(90)} y={200} fill={C.late} fontFamily={F.mono} fontSize={19} textAnchor="middle">90%</text>
          <line x1={0} x2={W} y1={160} y2={160} stroke={C.rule} />
          {[92, 96, 100].map((v) => <text key={v} x={X(v)} y={200} fill={C.faint} fontFamily={F.mono} fontSize={19} textAnchor="middle">{v}%</text>)}
          {un.map((u, i) => {
            const p = prog(f, 30 + i * 3, 12);
            const same = un.filter((v, j) => j < i && Math.abs(v[2] - u[2]) < 0.35).length;
            return <circle key={u[0]} cx={X(u[2])} cy={140 - same * 22} r={9} fill={C.ontime} opacity={p} transform={`translate(0, ${(1 - p) * -30})`} />;
          })}
        </svg>
        <In at={170} style={{ marginTop: 20 }}><Body>All 40 ranked: mean <B>96.1%</B> on time, lowest <B>92.4%</B>; €17,308 and 399 orders a week.</Body></In>
      </div>
      <div style={{ position: "absolute", left: 1220, top: 300, width: 580 }}>
        <In at={240}><Label color={C.headlight}>Killed mid-week, restarted</Label>
          <Body style={{ marginTop: 8, fontSize: 27 }}>The live runner journals every action and rebuilds from the world and the journal: <B>€27,655</B>, 460 orders, 93.7% on time, against €28,447, 467, 94.6% without the crash.</Body></In>
        <In at={340} style={{ marginTop: 26 }}><Label color={C.headlight}>Fast enough</Label>
          <Body style={{ marginTop: 8, fontSize: 27 }}>Slowest decision batch <B>91 ms</B>; a quote has 4.5 real seconds in the final.</Body></In>
      </div>
    </Scene>
  );
};

// ---------- 12 · limits ----------
const LIM: [string, [string, string][]][] = [
  ["Did not work", [
    ["Holding fees back", "−€65,251 over 30 weeks: unbooked gigs fill the intake."],
    ["Cheaper quotes for volume", "each extra order cost about €75 of margin."],
    ["Bundles of 4 or 5 cars", "−€5,653 / −€1,915 over 30 weeks."],
    ["Model 5's margin gain", "in-sample only; on unseen worlds money-neutral."],
  ]],
  ["Would break it", [
    ["A late car for the biggest dealer", "one car 3 minutes late halved its trust (25 → 12); we won 60% of its requests that day, 30% the next."],
    ["A price war day", "our quote stops at the car's cost: we won 23% of that day's requests."],
  ]],
  ["We don't know", [
    ["", "How the top teams move more cars per driver."],
    ["", "The separate effect of the price level, dealer trust and the note reader."],
  ]],
];
export const Limits: React.FC = () => (
  <Scene n={13} kicker="Limits" title="What did not work, what would break it, what we don't know"
    source="docs/jury.md §5 and the tracks' FINDINGS.md files; tracks/orch/finals/testfinal-20261114-1800/ANALYSIS.md.">
    <div style={{ position: "absolute", left: 120, top: 330, right: 120, display: "grid", gridTemplateColumns: "1.15fr 1fr 0.85fr", gap: 60 }}>
      {LIM.map(([h, items], c) => (
        <div key={h}>
          <In at={20 + c * 150}><div style={{ fontFamily: F.serif, fontSize: 40, fontWeight: 560, color: [C.frost, C.late, C.headlight][c], borderBottom: `1px solid ${C.rule}`, paddingBottom: 12 }}>{h}</div></In>
          {items.map(([b, s], i) => (
            <In key={i} at={40 + c * 150 + i * 30} style={{ marginTop: 22 }}>
              <div style={{ fontSize: 26, lineHeight: 1.4, color: C.frost }}>{b && <B>{b}: </B>}{s}</div>
            </In>
          ))}
        </div>
      ))}
    </div>
  </Scene>
);

// ---------- 13 · close ----------
export const Close: React.FC = () => {
  const fl = finalLine();
  return (
    <Scene n={14} kicker="pelaaja juhlii · Spread · Junction 2026">
      <div style={{ position: "absolute", left: 120, top: 250, right: 120 }}>
        <In at={10}><div style={{ fontFamily: F.serif, fontSize: 64, fontWeight: 560, lineHeight: 1.12, maxWidth: 1500 }}>
          Price each car over its own learned cost. Take only the work our drivers can deliver. Measure every idea on the same weeks.</div></In>
        <In at={90} style={{ marginTop: 70, display: "flex", alignItems: "baseline", gap: 40 }}>
          <div style={{ fontFamily: F.serif, fontSize: 80, fontWeight: 600, color: C.headlight }}>{fl.head}</div>
          <div style={{ fontFamily: F.mono, fontSize: 32, color: C.birch }}>{fl.sub}</div>
        </In>
        <In at={130} style={{ marginTop: 26 }}>
          <Body>Best ranking round: <B>{ord(BR.rank)} of {BR.rankedTeams}</B> ranked teams, {eur(BR.marginEur)} over {BR.runs} weeks, every week ranked.</Body>
        </In>
        <In at={170} style={{ marginTop: 60 }}>
          <div style={{ fontFamily: F.mono, fontSize: 22, color: C.faint }}>Every number in this video is in our repository: data/runs.jsonl, tracks/*/FINDINGS.md, docs/deck.</div>
        </In>
      </div>
    </Scene>
  );
};
