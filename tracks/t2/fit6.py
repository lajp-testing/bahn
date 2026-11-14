"""The per-request cost again, on the control's and c2's weeks: fitted on the dev weeks, checked on the study weeks.
cost / (typical fee x legs) of each won order against what the request shows."""
import sys, json, gzip, math, pickle, os; sys.path.insert(0, '/var/lib/amp-runner/src/alt-lab/t2')
import lab, pandas as pd, numpy as np
T = '/var/lib/amp-runner/src/alt-lab/t2/'; pd.set_option('display.width', 250)
labels = sys.argv[1:] or ['c1n@1e30321', 'c2n@1e30321']
cache = T + 'rows6.pkl'
if os.path.exists(cache) and pickle.load(open(cache, 'rb'))[0] == labels:
    w = pickle.load(open(cache, 'rb'))[1]
else:
    rows = []
    for label in labels:
        for prefix in ('dev-', 't2-study-'):
            rs = [r for r in lab.rows(label, prefix) if r['won']]
            feat = {}
            for seed, row in lab.weeks(label, prefix).items():
                for e in lab.events(row['folder']):
                    if e['kind'] != 'price_request': continue
                    r = e['request']; pu = r['legs'][0]['pickup']
                    feat[(seed, r['id'])] = dict(later=(pu['window']['from'] // 1440 > e['at'] // 1440) * 1.0, private=any(l[s]['privateAddress'] for l in r['legs'] for s in ('pickup', 'delivery')) * 1.0,
                                                 ready=pu['window']['from'] - e['at'], premium=r['legs'][0]['car']['premium'] * 1.0, electric=r['legs'][0]['car']['electric'] * 1.0, noted=bool(r.get('note')) * 1.0)
            for r in rs: r.update(feat[(r['seed'], r['rid'])])
            rows += rs
    w = pd.DataFrame(rows); pickle.dump((labels, w), open(cache, 'wb'))
w = w[w.legs == 1].copy(); w['cost'] = w.fee + w.refund + w.other
w['sd'] = w.opts.str.startswith('same') * 1.0; w['basis'] = w.ref * w.legs; w['ratio'] = w.cost / w.basis; w['rl'] = np.log(w.basis / w.list)
for d in range(5): w[f'd{d}'] = (w.day == d) * 1.0
w['pm'] = (w.hour >= 13) * 1.0; w['small'] = (w.ref < 30) * 1.0; w['lref'] = np.log(w.ref / 60)
dev = w.seed.str.startswith('dev'); print('orders', len(w), 'dev', int(dev.sum()))
def fit(cols, mask):
    ww = w[mask]; X = pd.DataFrame({'sd': ww.sd, 'next': 1 - ww.sd, **{c: ww[c] for c in cols}}); wt = np.sqrt(ww.basis.values)
    b, *_ = np.linalg.lstsq(X.values * wt[:, None], ww.ratio.values * wt, rcond=None); return dict(zip(X.columns, b))
def r2(co, mask):
    ww = w[mask]; pred = sum(co[c] * (ww[c] if c not in ('next',) else 1 - ww.sd) for c in co)
    base = np.where(ww.sd == 1, ww[ww.sd == 1].cost.sum() / ww[ww.sd == 1].basis.sum(), ww[ww.sd == 0].cost.sum() / ww[ww.sd == 0].basis.sum())
    return 1 - ((ww.ratio - pred) ** 2 * ww.basis).sum() / ((ww.ratio - base) ** 2 * ww.basis).sum()
for name, cols in [('three', ['private', 'later', 'rl']), ('+days', ['private', 'later', 'rl', 'd1', 'd2', 'd3', 'd4']), ('+days pm', ['private', 'later', 'rl', 'd1', 'd2', 'd3', 'd4', 'pm']),
                   ('+fri', ['private', 'later', 'rl', 'd4']), ('+fri lref', ['private', 'later', 'rl', 'd4', 'lref']), ('+fri car note', ['private', 'later', 'rl', 'd4', 'premium', 'electric', 'noted'])]:
    a, b = fit(cols, dev), fit(cols, ~dev)
    print(f'--- {name}: fitted on dev, R2 on dev {r2(a, dev):.3f}, on study {r2(a, ~dev):.3f}; fitted on study, R2 on dev {r2(b, dev):.3f}')
    print('  dev  ', {k: round(float(v), 3) for k, v in a.items()}); print('  study', {k: round(float(v), 3) for k, v in b.items()})
cols = ['private', 'later', 'rl', 'd4']
print('means (weighted by typical fee), all:', {c: round(float(np.average(w[c], weights=w.basis)), 3) for c in cols})
print('late share: private', w[w.private == 1].isLate.mean().round(3), 'other', w[w.private == 0].isLate.mean().round(3), ' today', w[w.later == 0].isLate.mean().round(3), 'later', w[w.later == 1].isLate.mean().round(3), ' fri', w[w.d4 == 1].isLate.mean().round(3))
print(w.groupby('day').apply(lambda g: pd.Series(dict(n=len(g), ratio=g.cost.sum() / g.basis.sum(), late=g.isLate.mean(), price=g.price.sum() / g.basis.sum()))).round(3).T.to_string())
