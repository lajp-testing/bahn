"""Builds sim.pkl: per dev seed, the quoted requests with their fitted limits, the bracket that seven played weeks put
on each request's own luck, and the cost, lateness and delivery minute of the order where a week won it."""
import sys, pickle, collections; sys.path.insert(0, '/var/lib/amp-runner/src/alt-lab/t2')
import lab, pandas as pd, numpy as np
from fitlib import design, logit
T = '/var/lib/amp-runner/src/alt-lab/t2/'
labels = ['base@f5a6b3b', 'm155@f5a6b3b', 'm1.7@e7bf4da', 'm1.85@e7bf4da', 'm2.0@e7bf4da', 'dial@a13aa1c', 'm1.3@e7bf4da'] + sys.argv[1:]
df = pd.DataFrame([r for l in labels for r in lab.rows(l)]); df.to_pickle(T + 'rows_all.pkl')
q = df[~df.declined & (df.markup > 1.0) & (df.markup < 3)].copy().reset_index(drop=True)
feats = pd.DataFrame(dict(lm=np.log(q.markup), lt=np.log(1 + q.trust / 100), sd=q.seed + '/' + q.day.astype(str), opts=q.opts, lrl=np.log(q.ref / q.list), llist=np.log(q.list / q.legs / 60),
    legs2=(q.legs == 2) * 1.0, lates=np.minimum(q.lates, 3) * 1.0, dealer=q.dealer, sdq=q.sd_quoted * 1.0, pick=q.pickup, deliv=q.delivery))
parts = [('lm', 'num', 0), ('lt', 'num', 0), ('sd', 'cat', 0), ('opts', 'cat', 0), ('lrl', 'num', 0), ('llist', 'num', 0), ('legs2', 'num', 0), ('lates', 'num', 0), ('sdq', 'num', 0), ('dealer', 'cat', 1.0), ('pick', 'cat', 1.0), ('deliv', 'cat', 1.0)]
X, names, pen = design(feats, parts); b, nll = logit(X, q.won.values * 1.0, pen)
co = dict(zip(names, b)); s = -1 / co['lm']; kt, kl = co['lt'] * s, co['lates'] * s
print('scale', s, 'trust', kt, 'lates', kl)
q['theta'] = (X @ b - co['lm'] * np.log(q.markup)) * s          # with the trust and lates the request had in that week
q['theta0'] = q.theta - kt * feats['lt'].values - kl * feats['lates'].values  # without them
q['cost'] = q.fee + q.refund + q.other
volume = {'base@f5a6b3b': 1.0, 'm155@f5a6b3b': 1.0, 'm1.7@e7bf4da': 1.0, 'm1.85@e7bf4da': 1.0, 'm2.0@e7bf4da': 1.0, 'dial@a13aa1c': 1.073, 'm1.3@e7bf4da': 1.08}
rank = {l: i for i, l in enumerate(labels)}
sim = {'scale': s, 'kt': kt, 'kl': kl, 'seeds': {}}
for seed, g in q.groupby('seed'):
    reqs = {e['request']['id']: e['request'] for e in lab.events(lab.weeks('base@f5a6b3b')[seed]['folder']) if e['kind'] == 'price_request'}
    out = []
    for rid, x in g.groupby('rid'):
        x = x.sort_values('label', key=lambda c: c.map(rank))
        gap = np.log(x.markup) - x.theta
        lo = gap[x.won].max() if x.won.any() else -np.inf; hi = gap[~x.won].min() if (~x.won).any() else np.inf
        wonrow = x[x.won].iloc[0] if x.won.any() else None
        first = x.iloc[0]
        out.append(dict(request=reqs[rid], at=first['at'], theta0=x.theta0.mean(), lo=lo, hi=hi, list=first['list'] * 100, ref=first['ref'] * 100, opts=first['opts'], day=first['day'],
                        cost=None if wonrow is None else wonrow['cost'] * 100 / volume.get(wonrow['label'], 1.0), late=None if wonrow is None else bool(wonrow['isLate']),
                        paid=None if wonrow is None or pd.isna(wonrow['rev_at']) else int(wonrow['rev_at'] - wonrow['at'])))
    sim['seeds'][seed] = sorted(out, key=lambda r: r['at'])
    n = len(out); bad = sum(r['lo'] > r['hi'] for r in out)
    print(seed, n, 'requests', bad, 'with crossed brackets', sum(r['cost'] is not None for r in out), 'with a cost')
pickle.dump(sim, open(T + 'sim.pkl', 'wb'))
