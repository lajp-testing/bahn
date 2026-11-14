"""The per-request cost for the quoter: cost / (typical fee x legs), by what the request shows, within the two groups
of the quoter's cost (same_day offered or not). Prints coefficients and the feature means to centre them."""
import sys, json, gzip, math; sys.path.insert(0, '/var/lib/amp-runner/src/alt-lab/t2')
import lab, pandas as pd, numpy as np
T = '/var/lib/amp-runner/src/alt-lab/t2/'; pd.set_option('display.width', 250)
df = pd.read_pickle(T + 'rows_all.pkl')
labels = sys.argv[1:] or ['base@f5a6b3b', 'dial-c1@a13aa1c', 'dial-c2@a13aa1c', 'dial-c3@a13aa1c']
w = df[df.label.isin(labels) & df.won].copy(); w['cost'] = w.fee + w.refund + w.other
feat = {}
for seed, row in lab.weeks('base@f5a6b3b').items():
    for e in lab.events(row['folder']):
        if e['kind'] != 'price_request': continue
        r = e['request']; leg = r['legs'][0]; pu, de = leg['pickup'], leg['delivery']
        feat[(seed, r['id'])] = dict(later=(pu['window']['from'] // 1440 > e['at'] // 1440) * 1.0, private=any(l[s]['privateAddress'] for l in r['legs'] for s in ('pickup', 'delivery')) * 1.0,
                                     ready=pu['window']['from'] - e['at'], afternoon=(e['at'] % 1440 >= 13 * 60) * 1.0)
f = pd.DataFrame([feat[k] for k in zip(w.seed, w.rid)], index=w.index); w = pd.concat([w, f], axis=1)
w['sd'] = w.opts.str.startswith('same') * 1.0; w['legs2'] = (w.legs == 2) * 1.0
w['basis'] = w.ref * w.legs; w['ratio'] = w.cost / w.basis; w['rl'] = np.log(w.ref * w.legs / w.list)
print('orders', len(w), 'two legs', int(w.legs2.sum()), ' cost/basis: same', round(w[w.sd == 1].cost.sum() / w[w.sd == 1].basis.sum(), 3), 'next', round(w[w.sd == 0].cost.sum() / w[w.sd == 0].basis.sum(), 3))
print(w.groupby(['sd', 'legs2']).apply(lambda g: pd.Series(dict(n=len(g), ratio=g.cost.sum() / g.basis.sum(), late=g.isLate.mean(), rl=g.rl.mean()))).round(3).to_string())
def fit(cols, name):
    X = pd.DataFrame({'sd': w.sd, 'next': 1 - w.sd, **{c: w[c] for c in cols}})
    wt = np.sqrt(w.basis.values)
    b, *_ = np.linalg.lstsq(X.values * wt[:, None], w.ratio.values * wt, rcond=None)
    pred = X.values @ b
    r2 = 1 - ((w.ratio - pred) ** 2 * w.basis).sum() / ((w.ratio - np.where(w.sd == 1, w[w.sd == 1].cost.sum() / w[w.sd == 1].basis.sum(), w[w.sd == 0].cost.sum() / w[w.sd == 0].basis.sum())) ** 2 * w.basis).sum()
    means = {c: float(np.average(w[c], weights=w.basis)) for c in cols}
    print(f'--- {name}: R2 over the two groups {r2:.3f}'); print('coef ', {k: round(float(v), 3) for k, v in zip(X.columns, b)}); print('means', {k: round(v, 3) for k, v in means.items()})
    return dict(zip(X.columns, b))
fit(['private', 'later', 'rl'], 'three')
fit(['private', 'later', 'rl', 'legs2'], 'four')
fit(['private', 'later', 'rl', 'legs2', 'afternoon'], 'five')
fit(['private', 'later'], 'two')
# stability: by seed halves and by label
for name, mask in [('dev-01..05', w.seed <= 'dev-05'), ('dev-06..10', w.seed > 'dev-05')] + [(l, w.label == l) for l in labels]:
    ww = w[mask]; X = pd.DataFrame({'sd': ww.sd, 'next': 1 - ww.sd, 'private': ww.private, 'later': ww.later, 'rl': ww.rl}); wt = np.sqrt(ww.basis.values)
    b, *_ = np.linalg.lstsq(X.values * wt[:, None], ww.ratio.values * wt, rcond=None); print(f'{name:18s}', len(ww), {k: round(float(v), 3) for k, v in zip(X.columns, b)})
