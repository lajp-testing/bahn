import React from "react";
import { AbsoluteFill, Easing, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { C, F } from "./theme";

export const ease = Easing.bezier(0.22, 1, 0.36, 1);
export const prog = (f: number, start: number, dur = 18) =>
  interpolate(f, [start, start + dur], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: ease });

// Text that rises into place at frame `at` (relative to the scene).
export const In: React.FC<{ at?: number; dur?: number; dy?: number; style?: React.CSSProperties; children: React.ReactNode }> =
  ({ at = 0, dur = 18, dy = 18, style, children }) => {
    const f = useCurrentFrame();
    const p = prog(f, at, dur);
    return <div style={{ opacity: p, transform: `translateY(${(1 - p) * dy}px)`, ...style }}>{children}</div>;
  };

// A number that counts up from 0 to `to` between frames at and at+dur.
export const Count: React.FC<{ to: number; at?: number; dur?: number; fmt: (v: number) => string }> =
  ({ to, at = 0, dur = 36, fmt }) => {
    const f = useCurrentFrame();
    return <>{fmt(to * prog(f, at, dur))}</>;
  };

export const SCENES = 14;

// Every scene: a kicker (what part of the story), a claim (the title), the body, and the source line.
export const Scene: React.FC<{ n: number; kicker: string; title?: React.ReactNode; source?: string; titleWidth?: number; children?: React.ReactNode }> =
  ({ n, kicker, title, source, titleWidth = 1500, children }) => {
    const f = useCurrentFrame();
    const { durationInFrames } = useVideoConfig();
    const out = interpolate(f, [durationInFrames - 10, durationInFrames], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
    return (
      <AbsoluteFill style={{ background: C.night, color: C.birch, fontFamily: F.sans, opacity: out }}>
        <Grain />
        <div style={{ position: "absolute", left: 120, top: 86, right: 120 }}>
          <In at={0} dur={14} dy={8}>
            <div style={{ fontFamily: F.mono, fontSize: 22, letterSpacing: "0.14em", textTransform: "uppercase", color: C.headlight }}>
              {kicker}
            </div>
          </In>
          {title && (
            <In at={4} dur={20}>
              <h1 style={{ fontFamily: F.serif, fontWeight: 560, fontSize: 60, lineHeight: 1.1, letterSpacing: "-0.01em",
                margin: "18px 0 0", maxWidth: titleWidth, fontVariationSettings: '"opsz" 72' }}>{title}</h1>
            </In>
          )}
        </div>
        {children}
        {source && (
          <In at={30} style={{ position: "absolute", left: 120, right: 120, bottom: 44 }}>
            <div style={{ borderTop: `1px solid ${C.rule}`, paddingTop: 14, fontFamily: F.mono, fontSize: 17, color: C.faint }}>{source}</div>
          </In>
        )}
        <Progress n={n} />
      </AbsoluteFill>
    );
  };

// A quiet ticker in the top right corner: which of the scenes this is.
const Progress: React.FC<{ n: number }> = ({ n }) => (
  <div style={{ position: "absolute", right: 120, top: 94, display: "flex", gap: 6 }}>
    {Array.from({ length: SCENES }, (_, i) => (
      <div key={i} style={{ width: i === n - 1 ? 26 : 10, height: 3, borderRadius: 2,
        background: i === n - 1 ? C.headlight : i < n - 1 ? C.frost : C.rule }} />
    ))}
  </div>
);

// A faint vignette and contour so the ground is not a flat fill.
export const Grain: React.FC = () => (
  <AbsoluteFill style={{ background: `radial-gradient(ellipse 80% 70% at 70% 40%, rgba(20,42,68,0.55), rgba(10,20,31,0) 70%)` }} />
);

export const Label: React.FC<{ children: React.ReactNode; color?: string; style?: React.CSSProperties }> = ({ children, color = C.frost, style }) => (
  <div style={{ fontFamily: F.mono, fontSize: 19, letterSpacing: "0.1em", textTransform: "uppercase", color, ...style }}>{children}</div>
);

export const Body: React.FC<{ children: React.ReactNode; style?: React.CSSProperties }> = ({ children, style }) => (
  <div style={{ fontSize: 32, lineHeight: 1.42, color: C.frost, ...style }}>{children}</div>
);

export const B: React.FC<{ children: React.ReactNode; c?: string }> = ({ children, c = C.birch }) => (
  <b style={{ color: c, fontWeight: 600 }}>{children}</b>
);

// The effect line every idea ends on: an amber rule and the measured change.
export const Effect: React.FC<{ at: number; children: React.ReactNode; style?: React.CSSProperties }> = ({ at, children, style }) => {
  const f = useCurrentFrame();
  const p = prog(f, at, 22);
  return (
    <div style={{ position: "relative", paddingLeft: 30, opacity: p, ...style }}>
      <div style={{ position: "absolute", left: 0, top: 4, bottom: 4, width: 5, background: C.headlight, transform: `scaleY(${p})`, transformOrigin: "top" }} />
      <Label color={C.headlight} style={{ marginBottom: 8 }}>Effect · same weeks, with and without</Label>
      <div style={{ fontSize: 34, lineHeight: 1.38, color: C.birch }}>{children}</div>
    </div>
  );
};
