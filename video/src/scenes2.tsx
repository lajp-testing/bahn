import React from "react";
import { useCurrentFrame } from "remotion";
import week from "./data/week.json";
import nums from "./data/numbers.json";
import { C, F, eur } from "./theme";
import { B, Body, Count, Effect, In, Label, prog, Scene } from "./ui";

const Col: React.FC<{ x: number; w: number; top?: number; children: React.ReactNode }> = ({ x, w, top = 310, children }) => (
  <div style={{ position: "absolute", left: x, top, width: w }}>{children}</div>
);

// a horizontal bar that grows; value printed at its end
const HBar: React.FC<{ at: number; label: string; v: number; max: number; w: number; fmt: (v: number) => string; c?: string; bold?: boolean }> =
  ({ at, label, v, max, w, fmt, c = C.frost, bold }) => {
    const f = useCurrentFrame();
    const p = prog(f, at, 30);
    return (
      <div style={{ marginTop: 18, opacity: prog(f, at - 6, 10) }}>
        <div style={{ fontSize: 24, color: bold ? C.birch : C.frost, fontWeight: bold ? 600 : 400 }}>{label}</div>
        <div style={{ display: "flex", alignItems: "center", gap: 14, marginTop: 6 }}>
          <div style={{ height: 22, width: (w * v / max) * p, background: c, borderRadius: 2 }} />
          <div style={{ fontFamily: F.mono, fontSize: 26, color: bold ? C.birch : C.frost }}>{fmt(v * p)}</div>
        </div>
      </div>
    );
  };

// ---------- 4 · idea 1: the learned cost model ----------
export const Idea1: React.FC = () => (
  <Scene n={4} kicker="Idea 1 · What a car will cost" title="A model learned from our own 1.9 million orders says what each car will cost"
    source="tracks/ml/FINDINGS.md (41,497 holdout orders, 10 worlds); docs/pricing-fix-report.md (1.19 / 0.92); b37-fee3 vs t3s15-safe-flat15, tracks/orch/FINDINGS.md.">
    <Col x={120} w={760}>
      <In at={30}><Label color={C.headlight}>The idea</Label>
        <Body style={{ marginTop: 8 }}>For every request, predict the <B>driver fee</B> the car will need and its <B>chance of being late</B>, from 44 facts known at quote time. Gradient-boosted trees, run as plain Python: 0.1 ms a request.</Body></In>
      <In at={150} style={{ marginTop: 34 }}><Label color={C.headlight}>Why</Label>
        <Body style={{ marginTop: 8 }}>Our hand-fit formula expected a won car to cost <B>1.19 ×</B> its typical fee. The ledger said <B>0.92 ×</B>. We were quoting far above what dealers accepted.</Body></In>
    </Col>
    <Col x={1000} w={800}>
      <In at={240}><Label color={C.headlight}>Fee error on holdout worlds, × typical fee (lower is better)</Label></In>
      <HBar at={250} label="constant" v={0.309} max={0.32} w={560} fmt={(v) => v.toFixed(3)} c={C.rule} />
      <HBar at={275} label="hand-fit formula" v={0.274} max={0.32} w={560} fmt={(v) => v.toFixed(3)} c={C.coast} />
      <HBar at={300} label="learned model" v={0.232} max={0.32} w={560} fmt={(v) => v.toFixed(3)} c={C.headlight} bold />
    </Col>
    <Effect at={380} style={{ position: "absolute", left: 120, right: 120, top: 790 }}>
      <B c={C.headlight}>+<Count to={32271} at={385} fmt={(v) => eur(v)} /></B> over the same 40 weeks, ahead in 29; 390 orders a week instead of 364;
      the lowest week rose from 90.2% to 92.0% on time.
    </Effect>
  </Scene>
);

// ---------- 5 · the decision rule, on one real request ----------
const t = week.r13.terms;
const e2 = (c: number) => eur(c / 100, 2);
export const Formula: React.FC = () => {
  const f = useCurrentFrame();
  const curve = t.curve as number[][];
  const W = 600, H = 330, x0 = 1.12, x1 = 2.34, vmax = 0.1;
  const X = (x: number) => ((x - x0) / (x1 - x0)) * W, Y = (v: number) => H - (v / vmax) * H;
  const draw = prog(f, 420, 60);
  const n = Math.max(2, Math.ceil(curve.length * draw));
  const path = curve.slice(0, n).map((p, i) => `${i ? "L" : "M"}${X(p[0]).toFixed(1)},${Y(p[1]).toFixed(1)}`).join("");
  const pick = prog(f, 480, 20);
  const line = (at: number, lhs: React.ReactNode, rhs: React.ReactNode, hi = false) => (
    <In at={at} dy={10} style={{ marginTop: 14 }}>
      <div style={{ fontFamily: F.mono, fontSize: 25, lineHeight: 1.4, color: C.frost, whiteSpace: "nowrap" }}>
        {lhs ? <><span style={{ color: hi ? C.headlight : C.birch, fontWeight: 600 }}>{lhs}</span> = </> : <span style={{ paddingLeft: "3.5em" }} />}{rhs}
      </div>
    </In>
  );
  return (
    <Scene n={5} kicker="Idea 2 · The decision rule" title="Each quote is the price with the most expected margin"
      source="dispatch/pricing.py; request R00013 of the test final week (demo/assets/decisions.json), the replay matches the live quote to the cent.">
      <Col x={120} w={1000} top={270}>
        <In at={20}><Label color={C.headlight}>The rule</Label></In>
        {line(30, "price", <>list price × x, with x the multiple that maximises</>)}
        {line(70, "", <>(x × (1 − late risk) − cost) × chance(x)</>)}
        {line(120, "cost", <>1.1 × expected fee ÷ list price + 0.3 × (waiting ÷ limit)²</>)}
        {line(170, "chance(x)", <>1 ÷ (1 + e<sup>(x ÷ dealer trust − market level) ÷ 0.2</sup>)</>)}
        <In at={240} style={{ marginTop: 40 }}><Label color={C.headlight}>Request R00013 · Monday 09:21 · Raisio → Ylivieska, 496 km, next day</Label></In>
        {line(260, "cost", <>1.1 × {e2(t.expected)} ÷ {e2(t.list)} + 0.3 × (0 ÷ 35)² = <b style={{ color: C.birch }}>{t.cost.toFixed(3)}</b></>)}
        {line(300, "chance(1.45)", <>1 ÷ (1 + e<sup>(1.452 ÷ 1.00 − {t.level.toFixed(3)}) ÷ 0.2</sup>) = <b style={{ color: C.birch }}>{(t.chance * 100).toFixed(1)}%</b></>)}
        {line(340, "margin", <>(1.452 × {(1 - t.risk).toFixed(3)} − {t.cost.toFixed(3)}) × {t.chance.toFixed(3)} × €144 = <b style={{ color: C.birch }}>{e2(t.value * t.list)}</b></>)}
        {line(380, "price", <>{e2(t.list)} × {t.x.toFixed(4)} = <b style={{ color: C.headlight }}>{e2(t.price)}</b></>, true)}
      </Col>
      <div style={{ position: "absolute", left: 1200, top: 330, width: W }}>
        <In at={410}><Label>Expected margin at each price tried</Label></In>
        <svg width={W} height={H + 50} style={{ overflow: "visible", marginTop: 18 }}>
          <line x1={0} x2={W} y1={H} y2={H} stroke={C.rule} strokeWidth={2} />
          <path d={path} fill="none" stroke={C.frost} strokeWidth={3} />
          <g opacity={pick}>
            <line x1={X(t.x)} x2={X(t.x)} y1={Y(t.value)} y2={H} stroke={C.headlight} strokeWidth={2} strokeDasharray="4 5" />
            <circle cx={X(t.x)} cy={Y(t.value)} r={8} fill={C.headlight} />
            <text x={X(t.x) + 14} y={Y(t.value) - 14} fill={C.headlight} fontFamily={F.mono} fontSize={24}>× {t.x.toFixed(2)} list = {e2(t.price)}</text>
          </g>
          <text x={0} y={H + 34} fill={C.faint} fontFamily={F.mono} fontSize={20}>× {x0.toFixed(2)}</text>
          <text x={W} y={H + 34} fill={C.faint} fontFamily={F.mono} fontSize={20} textAnchor="end">× {x1.toFixed(2)} list price</text>
          <text x={0} y={H + 62} fill={C.faint} fontFamily={F.sans} fontSize={21}>← cheaper: less margin a car</text>
          <text x={W} y={H + 62} fill={C.faint} fontFamily={F.sans} fontSize={21} textAnchor="end">dearer: fewer wins →</text>
        </svg>
      </div>
      <In at={540} style={{ position: "absolute", left: 1200, top: 830, width: W }}>
        <Body style={{ fontSize: 28 }}>The dealer took it. A driver delivered it on time for {e2(week.r13.fee)}: <B c={C.ontime}>{e2(t.price - week.r13.fee)} margin</B>.</Body>
      </In>
    </Scene>
  );
};

// ---------- 6 · idea 2: following the market ----------
export const Idea2: React.FC = () => {
  const sd = nums.sameday as { label: string; change_eur: number; ahead: number; lowest_on_time: number }[];
  const names = ["cost tilt 1.0", "cost tilt 1.05", "same-day at 8 h slack", "same-day + tilt 1.05"];
  const f = useCurrentFrame();
  return (
    <Scene n={6} kicker="Idea 2 · Prices that follow the market" title="The price dealers accept moves every day, so ours follows wins and losses"
      source="Day levels from copies of whole weeks: tracks/t2/FINDINGS.md. Chart: 30 dev + rob weeks against b37-fee3 (b44, b43, b45, b46). 40-week figure: tracks/orch/FINDINGS.md 15:05.">
      <Col x={120} w={800}>
        <In at={30}><Label color={C.headlight}>Why</Label>
          <Body style={{ marginTop: 8 }}>In copies of whole weeks, the price at which dealers switch to the competitor moved between <B>1.10 and 1.67 × list</B> from day to day.</Body></In>
        <In at={130} style={{ marginTop: 26 }}><Label color={C.headlight}>The idea</Label>
          <div style={{ fontFamily: F.mono, fontSize: 28, color: C.birch, marginTop: 10 }}>level += 0.06 × (won − chance)</div>
          <Body style={{ marginTop: 8 }}>after every decision. And quote <B>same-day</B> whenever 8 h of slack remain: a request quoted both same-day and next-day is won <B>67%</B> of the time, next-day alone <B>34%</B>.</Body></In>
      </Col>
      <Col x={1020} w={780}>
        <In at={250}><Label color={C.headlight}>Margin change over 30 weeks · lowest week on time</Label></In>
        {sd.map((s, i) => {
          const p = prog(f, 265 + i * 22, 28);
          const bad = s.lowest_on_time < 90;
          return (
            <div key={s.label} style={{ marginTop: 22, opacity: prog(f, 259 + i * 22, 10) }}>
              <div style={{ fontSize: 24, color: i === 3 ? C.birch : C.frost, fontWeight: i === 3 ? 600 : 400 }}>{names[i]}</div>
              <div style={{ display: "flex", alignItems: "center", gap: 14, marginTop: 6 }}>
                <div style={{ height: 22, width: 400 * (s.change_eur / 28000) * p, background: i === 3 ? C.headlight : C.coast, borderRadius: 2 }} />
                <div style={{ fontFamily: F.mono, fontSize: 24, color: C.birch }}>+{eur(s.change_eur * p)}</div>
                <div style={{ fontFamily: F.mono, fontSize: 24, color: bad ? C.late : C.ontime }}>{s.lowest_on_time.toFixed(1)}%{bad ? " unranked" : ""}</div>
              </div>
            </div>
          );
        })}
      </Col>
      <Effect at={400} style={{ position: "absolute", left: 120, right: 120, top: 800 }}>
        Same-day alone lost a week. With the cost tilt that keeps marginal cars out: <B c={C.headlight}>+€31,975 over 40 weeks</B>, ahead in 31, lowest week 93.8%.
      </Effect>
    </Scene>
  );
};

// ---------- 7 · idea 3: one flat fee ----------
export const Idea3: React.FC = () => {
  const f = useCurrentFrame();
  const W = 760, H = 300;
  const p = prog(f, 40, 60);
  // schematic: an hourly ladder against our flat fee with two raises (hours since posting)
  const ladder = Array.from({ length: 12 }, (_, i) => [i / 12 * W, H - 30 - i * 23]);
  const ladderD = ladder.map(([x, y], i) => `${i ? `L${x},${ladder[i - 1][1]} ` : "M"}${x},${y}`).join(" ") + ` L${W},${ladder[11][1]}`;
  const flat = `M0,${H - 90} L${W * 0.5},${H - 90} L${W * 0.5},${H - 140} L${W * 0.86},${H - 140} L${W * 0.86},${H - 190} L${W},${H - 190}`;
  return (
    <Scene n={7} kicker="Idea 3 · Drivers and fees" title="Drivers learn our fees, so a gig opens at one flat fee and rarely rises"
      source="tracks/t3/FINDINGS.md (hold-the-ladder study; flat-fee screens t3s14); t3s15-safe-flat15 vs t3s10-calm, tracks/orch/FINDINGS.md 13:40. Code: dispatch/fees.py.">
      <Col x={120} w={W} top={300}>
        <In at={20}><Label color={C.headlight}>Fee of one gig over time (schematic)</Label></In>
        <svg width={W} height={H + 40} style={{ overflow: "visible", marginTop: 24 }}>
          <defs><clipPath id="cp"><rect x={0} y={-40} width={W * p} height={H + 80} /></clipPath></defs>
          <line x1={0} x2={W} y1={H} y2={H} stroke={C.rule} strokeWidth={2} />
          <g clipPath="url(#cp)">
            <path d={ladderD} fill="none" stroke={C.faint} strokeWidth={2.5} strokeDasharray="7 6" />
            <path d={flat} fill="none" stroke={C.headlight} strokeWidth={4} />
          </g>
          <text x={W} y={ladder[11][1] - 14} fill={C.faint} fontFamily={F.sans} fontSize={22} textAnchor="end">old: a raise every hour</text>
          <text x={0} y={H - 104} fill={C.headlight} fontFamily={F.sans} fontSize={22}>our fee</text>
          <text x={W * 0.5 + 10} y={H - 112} fill={C.headlight} fontFamily={F.sans} fontSize={20} opacity={prog(f, 80, 12)}>+0.15 after 6 h unbooked</text>
          <text x={W} y={H - 162} fill={C.headlight} fontFamily={F.sans} fontSize={20} textAnchor="end" opacity={prog(f, 95, 12)}>+0.15 a day before pickup</text>
          <text x={0} y={H + 32} fill={C.faint} fontFamily={F.mono} fontSize={19}>posted</text>
          <text x={W} y={H + 32} fill={C.faint} fontFamily={F.mono} fontSize={19} textAnchor="end">time →</text>
        </svg>
        <In at={130} style={{ marginTop: 6 }}><Body style={{ fontSize: 25 }}>It opens at the model's expected fee − 0.15 × typical fee, never below 0.75 × typical (0.95 for a lane under 40 km or a car with under 5 hours left).</Body></In>
      </Col>
      <Col x={1020} w={780} top={300}>
        <In at={190}><Label color={C.headlight}>Why</Label>
          <Body style={{ marginTop: 8 }}>Drivers wait for raises they expect. When we held raises back, bookings came <B>306 min</B> after a driver first saw the gig instead of <B>84</B>, at a higher fee.</Body></In>
        <In at={300} style={{ marginTop: 30, display: "grid", gridTemplateColumns: "1fr 1fr", gap: 30 }}>
          <div><div style={{ fontFamily: F.mono, fontSize: 44, fontWeight: 600 }}>86 → 7–12</div>
            <div style={{ fontSize: 23, color: C.frost, marginTop: 6 }}>median minutes from posting to booking, one-car gig</div></div>
          <div><div style={{ fontFamily: F.mono, fontSize: 44, fontWeight: 600 }}>7.0 → 5.9%</div>
            <div style={{ fontSize: 23, color: C.frost, marginTop: 6 }}>of one-car gigs late (about), 10 dev weeks</div></div>
        </In>
      </Col>
      <Effect at={400} style={{ position: "absolute", left: 120, right: 120, top: 856 }}>
        Flat fees together with the safe-car rule (next): <B c={C.headlight}>+<Count to={69993} at={405} fmt={(v) => eur(v)} /></B> over 40 weeks, ahead in 38 of 40.
      </Effect>
    </Scene>
  );
};

// ---------- 8 · idea 4: safe cars and bundles ----------
export const Idea4: React.FC = () => {
  const f = useCurrentFrame();
  const fl = nums.flood as [string, number, number][];
  const H = 300, lo = 70, hi = 100, Y = (v: number) => H - ((v - lo) / (hi - lo)) * H, bw = 34;
  return (
    <Scene n={8} kicker="Idea 4 · Which cars, and how many per driver" title="We take more of the cars that stay on time, and let one driver carry two or three"
      source="tracks/t1/FINDINGS.md (t1s13-flood vs t1s11-base); tracks/orch/FINDINGS.md 13:40; tracks/t3/FINDINGS.md (bundles in 40 saved weeks); tracks/t5/FINDINGS.md.">
      <Col x={120} w={800} top={290}>
        <In at={20}><Label color={C.headlight}>We won 55% more orders to see what breaks · on time by kind of car</Label></In>
        <svg width={800} height={H + 90} style={{ overflow: "visible", marginTop: 30 }}>
          <line x1={0} x2={780} y1={Y(90)} y2={Y(90)} stroke={C.late} strokeWidth={1.5} strokeDasharray="6 6" opacity={0.8} />
          <text x={780} y={Y(90) - 8} fill={C.late} fontFamily={F.mono} fontSize={18} textAnchor="end">90%: the ranking line</text>
          {fl.map(([name, a, b], i) => {
            const x = i * 130 + 10, p = prog(f, 40 + i * 12, 26);
            return (
              <g key={i}>
                <rect x={x} y={Y(lo + (a - lo) * p)} width={bw} height={H - Y(lo + (a - lo) * p)} fill={C.coast} />
                <rect x={x + bw + 6} y={Y(lo + (b - lo) * p)} width={bw} height={H - Y(lo + (b - lo) * p)} fill={b < 90 ? C.late : C.frost} />
                {name.split("\n").map((s, j) => <text key={j} x={x} y={H + 30 + j * 24} fill={C.frost} fontFamily={F.sans} fontSize={20}>{s}</text>)}
              </g>
            );
          })}
          <g transform={`translate(0, ${H + 84})`}>
            <rect width={18} height={18} fill={C.coast} /><text x={26} y={15} fill={C.frost} fontFamily={F.sans} fontSize={20}>normal intake</text>
            <rect x={200} width={18} height={18} fill={C.frost} /><text x={226} y={15} fill={C.frost} fontFamily={F.sans} fontSize={20}>55% more orders</text>
          </g>
        </svg>
      </Col>
      <Col x={1020} w={780} top={290}>
        <In at={170}><Label color={C.headlight}>Safe cars</Label>
          <Body style={{ marginTop: 8, fontSize: 28 }}>Past 45 cars waiting for a driver, only cars <B>under 300 km without a private address</B> still get a quote, up to 100.</Body></In>
        <In at={270} style={{ marginTop: 26 }}><Label color={C.headlight}>Bundles</Label>
          <Body style={{ marginTop: 8, fontSize: 28 }}>A new car joins an unbooked gig when one driver can do the stops in a row, up to 3 cars. In a two-car gig a car costs <B>0.79 ×</B> typical and is <B>1.0%</B> late; alone <B>0.97 ×</B> and <B>3.7%</B>.</Body></In>
      </Col>
      <Effect at={400} style={{ position: "absolute", left: 120, right: 120, top: 830 }}>
        Safe cars + flat fees: <B c={C.headlight}>+€69,993 (+14.3%)</B> over 40 weeks, 364 orders a week instead of 277. Bundles: +6.4% over 7 weeks.
      </Effect>
    </Scene>
  );
};
