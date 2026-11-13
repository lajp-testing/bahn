"""The limit's place table: which part transfers between the dev and the study weeks: delivery, pickup, or both?"""
import sys, pickle; sys.path.insert(0, '/var/lib/amp-runner/src/alt-lab/t2')
import pandas as pd, numpy as np
from fitlib import design, logit
T = '/var/lib/amp-runner/src/alt-lab/t2/'
df = pd.read_pickle(T + 'rows8.pkl'); df['pick'] = df.pickup; df['deliv'] = df.delivery
q = df[~df.declined & (df.markup > 1.0) & (df.markup < 3)].copy().reset_index(drop=True); dev = q.seed.str.startswith('dev')
F = pd.DataFrame(dict(lm=np.log(q.markup), lt=np.log(1 + q.trust / 100), sd=q.seed + '/' + q.day.astype(str), nosd=(~q.opts.str.startswith('same')) * 1.0, llist=np.log(q['list'] / q.legs / 60),
    legs2=(q.legs == 2) * 1.0, lates=np.minimum(q.lates, 3) * 1.0, pick=q.pick, deliv=q.deliv, private=q.private, premium=q.premium, later=q.later))
BASE = [('lm', 'num', 0), ('lt', 'num', 0), ('sd', 'cat', 0), ('nosd', 'num', 0), ('llist', 'num', 0), ('legs2', 'num', 0), ('lates', 'num', 0)]
def fit(mask, parts, extra=None):
    f = F[mask].copy()
    if extra is not None: f['x'] = extra[mask].values; parts = parts + [('x', 'num', 0)]
    X, names, pen = design(f, parts); b, nll = logit(X, q[mask].won.values * 1.0, pen); return dict(zip(names, b)), nll
for name, cats in (('delivery', ['deliv']), ('pickup', ['pick']), ('both', ['pick', 'deliv'])):
    for pen in (0.5, 2.0, 10.0):
        line = f'{name:9s} pen {pen:4.1f}:'
        for a, b in ((~dev, dev), (dev, ~dev)):
            co, _ = fit(a, BASE + [(c, 'cat', pen) for c in cats]); s = -1 / co['lm']
            x = sum(q[c].map(lambda v, c=c: co.get(c + '_' + v, 0.0)) * s for c in cats)
            co0, nll0 = fit(b, BASE); co1, nll1 = fit(b, BASE, x)
            line += f'  nll {nll0:.0f} -> {nll1:.0f} ({(nll0 - nll1) / nll0:.1%}), weight {co1["x"] * -1 / co1["lm"]:.2f}'
        print(line, flush=True)
co, nll = fit(dev | ~dev, BASE + [('private', 'num', 0), ('premium', 'num', 0), ('later', 'num', 0), ('pick', 'cat', 2.0), ('deliv', 'cat', 2.0)]); s = -1 / co['lm']
print('other effects on the limit (log markup): private %.3f premium %.3f later %.3f' % (co['private'] * s, co['premium'] * s, co['later'] * s))
