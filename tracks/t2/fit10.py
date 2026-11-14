"""The limit by the request's set of options (instead of 'offers same_day or not'), fitted on dev and on study apart."""
import sys; sys.path.insert(0, '/var/lib/amp-runner/src/alt-lab/t2')
import pandas as pd, numpy as np
from fitlib import design, logit
T = '/var/lib/amp-runner/src/alt-lab/t2/'
df = pd.read_pickle(T + 'rows8.pkl'); df['pick'] = df.pickup; df['deliv'] = df.delivery
q = df[~df.declined & (df.markup > 1.0) & (df.markup < 3)].copy().reset_index(drop=True); dev = q.seed.str.startswith('dev')
F = pd.DataFrame(dict(lm=np.log(q.markup), lt=np.log(1 + q.trust / 100), sd=q.seed + '/' + q.day.astype(str), nosd=(~q.opts.str.startswith('same')) * 1.0, llist=np.log(q['list'] / q.legs / 60),
    legs2=(q.legs == 2) * 1.0, lates=np.minimum(q.lates, 3) * 1.0, pick=q.pick, deliv=q.deliv, opts=q.opts, later=q.later, private=q.private, hour=(q.hour >= 13) * 1.0,
    only_same=(q.opts == 'same') * 1.0, has_with=q.opts.str.endswith('with') * 1.0))
A = [('lm', 'num', 0), ('lt', 'num', 0), ('sd', 'cat', 0), ('llist', 'num', 0), ('legs2', 'num', 0), ('lates', 'num', 0), ('pick', 'cat', 2.0), ('deliv', 'cat', 2.0)]
for name, mask in (('dev', dev), ('study', ~dev), ('all', dev | ~dev)):
    for title, parts in (('nosd', A + [('nosd', 'num', 0)]), ('option sets', A + [('opts', 'cat', 0)]), ('nosd, only same, has within_3', A + [('nosd', 'num', 0), ('only_same', 'num', 0), ('has_with', 'num', 0)]),
                         ('+ later, afternoon', A + [('nosd', 'num', 0), ('only_same', 'num', 0), ('has_with', 'num', 0), ('later', 'num', 0), ('hour', 'num', 0)])):
        X, names, pen = design(F[mask], parts); b, nll = logit(X, q[mask].won.values * 1.0, pen); co = dict(zip(names, b)); s = -1 / co['lm']
        print(f'{name:5s} {title:32s} nll {nll:8.1f} scale {s:.4f} trust {co["lt"] * s:.2f} llist {co["llist"] * s:.3f} ', {k: round(v * s, 3) for k, v in co.items() if k.startswith('opts_') or k in ('nosd', 'only_same', 'has_with', 'later', 'hour')}, flush=True)
print(q.groupby('opts').apply(lambda g: pd.Series(dict(n=len(g), won=g.won.mean(), markup=g.markup.mean(), later=g.later.mean()))).round(3).to_string())
