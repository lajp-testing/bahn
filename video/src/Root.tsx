import React from "react";
import { Composition, Series, Still } from "remotion";
import "./theme";
import { Claim, Flow, Hook, Result } from "./scenes1";
import { Formula, Idea1, Idea2, Idea3, Idea4 } from "./scenes2";
import { Close, Limits, Method, Robust, TestFinal } from "./scenes3";
import { Ablation } from "./Ablation";
const AblationScene: React.FC = () => <Ablation n={9} />;

// One idea per scene; durations in frames at 30 fps (about 2.5 words a second plus a second to settle).
export const SCENE_LIST: [string, React.FC, number][] = [
  ["hook", Hook, 510],
  ["claim", Claim, 540],
  ["result", Result, 540],
  ["flow", Flow, 540],
  ["idea1-cost", Idea1, 600],
  ["formula", Formula, 690],
  ["idea2-prices", Idea2, 570],
  ["idea3-fees", Idea3, 570],
  ["idea4-cars", Idea4, 600],
  ["ablation", AblationScene, 660],
  ["method", Method, 420],
  ["testfinal", TestFinal, 570],
  ["robust", Robust, 540],
  ["limits", Limits, 540],
  ["close", Close, 330],
];
const TOTAL = SCENE_LIST.reduce((s, [, , d]) => s + d, 0);

const Main: React.FC = () => (
  <Series>
    {SCENE_LIST.map(([id, C, d]) => <Series.Sequence key={id} durationInFrames={d}><C /></Series.Sequence>)}
  </Series>
);

export const Root: React.FC = () => (
  <>
    <Composition id="Main" component={Main} durationInFrames={TOTAL} fps={30} width={1920} height={1080} />
    {SCENE_LIST.map(([id, C, d]) => (
      <Composition key={id} id={`scene-${id}`} component={C} durationInFrames={d} fps={30} width={1920} height={1080} />
    ))}
  </>
);
void Still;
