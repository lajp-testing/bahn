"""Requests with two options: which option the dealer takes, and what each earns."""
import pandas as pd, numpy as np
pd.set_option('display.width', 250)
df = pd.read_pickle('/var/lib/amp-runner/src/alt-lab/t2/rows8.pkl'); df = df[df.label == 'c1n@1e30321']
print(df.groupby('opts').apply(lambda g: pd.Series(dict(n=len(g), declined=g.declined.mean(), quoted=(~g.declined).sum(), won=g.won.sum() / max((~g.declined).sum(), 1), sd_quoted=g.sd_quoted.mean()))).round(3).to_string())
w = df[df.won].copy(); w['cost'] = w.fee + w.refund + w.other; w['margin'] = w.rev - w.cost
print(w.groupby(['opts', 'opt']).apply(lambda g: pd.Series(dict(n=len(g), price=g.price.mean(), typical=(g.ref * g.legs).mean(), list=g['list'].mean(), cost_ratio=g.cost.sum() / (g.ref * g.legs).sum(), fee_ratio=g.fee.sum() / (g.ref * g.legs).sum(),
    late=g.isLate.mean(), margin=g.margin.mean(), share=g.margin.sum() / g.price.sum()))).round(3).to_string())
