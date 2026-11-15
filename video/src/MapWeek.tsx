import React from "react";
import { interpolate, useCurrentFrame } from "remotion";
import week from "./data/week.json";
import { C, F } from "./theme";

type Move = { pu: number; de: number; late: boolean; path: number[][] };
const moves = week.moves as Move[];
const reqs = week.requests as [number, number[]][];
const borderD = (week.border as number[][][]).map((r) => "M" + r.map((p) => p.join(",")).join("L") + "Z").join("");
const SHOW = ["helsinki", "tampere", "turku", "oulu", "jyvaskyla", "kuopio", "rovaniemi", "lahti", "pori", "vaasa", "joensuu"];

export const WEEK_MIN = 7 * 1440;

const lerpPath = (path: number[][], t: number) => {
  if (path.length < 2) return path[0];
  const segs: number[] = [];
  let tot = 0;
  for (let i = 1; i < path.length; i++) {
    const d = Math.hypot(path[i][0] - path[i - 1][0], path[i][1] - path[i - 1][1]);
    segs.push(d); tot += d;
  }
  let want = t * tot;
  for (let i = 0; i < segs.length; i++) {
    if (want <= segs[i] || i === segs.length - 1) {
      const u = segs[i] ? Math.min(1, want / segs[i]) : 1;
      return [path[i][0] + (path[i + 1][0] - path[i][0]) * u, path[i][1] + (path[i + 1][1] - path[i][1]) * u];
    }
    want -= segs[i];
  }
  return path[path.length - 1];
};

// Finland and the week's real cars: rings where requests arrive, amber cars on their lanes,
// a green (on time) or red (late) mark where each car was delivered. `minute` is world time.
export const MapWeek: React.FC<{ minute: number; scale?: number; x: number; y: number; labels?: boolean }> =
  ({ minute, scale = 1, x, y, labels = true }) => {
    const minPerFrame = 28; // trails and rings live a fixed real time, whatever the playback speed
    return (
      <svg width={560 * scale} height={980 * scale} viewBox="0 0 560 980" style={{ position: "absolute", left: x, top: y, overflow: "visible" }}>
        <defs>
          <filter id="glow" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="2.4" /></filter>
        </defs>
        <path d={borderD} fill={C.land} stroke={C.coast} strokeWidth={1.2} strokeLinejoin="round" />
        {labels && Object.entries(week.places).filter(([id]) => SHOW.includes(id)).map(([id, p]) => (
          <g key={id}>
            <circle cx={p.xy[0]} cy={p.xy[1]} r={2.2} fill={C.frost} opacity={0.7} />
            <text x={p.xy[0] + 7} y={p.xy[1] + 4} fontFamily={F.sans} fontSize={13} fill={C.faint}>{p.name}</text>
          </g>
        ))}
        {reqs.map(([at, xy], i) => {
          const age = (minute - at) / minPerFrame;
          if (age < 0 || age > 24) return null;
          const p = age / 24;
          return <circle key={"r" + i} cx={xy[0]} cy={xy[1]} r={3 + p * 16} fill="none" stroke={C.headlight} strokeWidth={1.4} opacity={(1 - p) * 0.55} />;
        })}
        {moves.map((m, i) => {
          if (minute < m.pu) return null;
          
          const travel = Math.max(m.de - m.pu, minPerFrame * 18);
          const t = Math.min(1, (minute - m.pu) / travel);
          const sinceDone = (minute - (m.pu + travel)) / minPerFrame;
          const lane = "M" + m.path.map((p) => p.join(",")).join("L");
          const laneOp = sinceDone > 0 ? interpolate(sinceDone, [0, 60], [0.5, 0.12], { extrapolateRight: "clamp" }) : 0.5;
          const pos = lerpPath(m.path, t);
          const last = m.path[m.path.length - 1];

          return (
            <g key={"m" + i}>
              <path d={lane} fill="none" stroke={C.headlight} strokeWidth={1} opacity={laneOp} />
              {t < 1 ? (
                <>
                  <circle cx={pos[0]} cy={pos[1]} r={6} fill={C.headlight} opacity={0.5} filter="url(#glow)" />
                  <circle cx={pos[0]} cy={pos[1]} r={2.6} fill={C.headlight} />
                </>
              ) : (
                <circle cx={last[0]} cy={last[1]} r={2.4} fill={m.late ? C.late : C.ontime} opacity={interpolate(sinceDone, [0, 90], [1, 0.55], { extrapolateRight: "clamp" })} />
              )}
            </g>
          );
        })}
      </svg>
    );
  };

const count = (arr: number[], t: number) => { let n = 0; for (const v of arr) if (v <= t) n++; return n; };
export const stats = (minute: number) => {
  let margin = 0;
  for (const [t, s] of week.margin as number[][]) { if (t <= minute) margin = s; else break; }
  return {
    requests: count(reqs.map((r) => r[0]), minute),
    won: count(week.won as number[], minute),
    delivered: count(week.delivered as number[], minute),
    margin: margin / 100,
  };
};
export const clock = (minute: number) => {
  const days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
  const m = Math.max(0, Math.min(WEEK_MIN - 1, Math.floor(minute)));
  const d = Math.floor(m / 1440), h = Math.floor((m % 1440) / 60), mm = m % 60;
  return `${days[d]} ${String(h).padStart(2, "0")}:${String(mm - (mm % 10)).padStart(2, "0")}`;
};
