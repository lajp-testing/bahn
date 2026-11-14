"""The place tables. (A) the limit: an effect per pickup place and per delivery place, fitted on the study weeks, on the
dev weeks and on all 30. (B) the cost of a won order in typical fees, by place, by drivers near and by drive time:
fitted on one set of weeks, R2 on the other."""
import sys, pickle, json, gzip, math; sys.path.insert(0, '/var/lib/amp-runner/src/alt-lab/t2')
import lab, pandas as pd, numpy as np
from fitlib import design, logit
T = '/var/lib/amp-runner/src/alt-lab/t2/'; pd.set_option('display.width', 250)
import os
if os.path.exists(T + 'rows8.pkl'): df = pd.read_pickle(T + 'rows8.pkl')
else:
    df = pd.read_pickle(T + 'rows7.pkl'); feat = {}
    for label in df.label.unique():
        for prefix in ('dev-', 't2-study-'):
            for seed, row in lab.weeks(label, prefix).items():
                if (seed, 'R00001') in feat: continue
                for e in lab.events(row['folder']):
                    if e['kind'] != 'price_request': continue
                    r = e['request']; pu = r['legs'][0]['pickup']
                    feat[(seed, r['id'])] = dict(later=(pu['window']['from'] // 1440 > e['at'] // 1440) * 1.0, private=any(l[s]['privateAddress'] for l in r['legs'] for s in ('pickup', 'delivery')) * 1.0,
                                                 premium=r['legs'][0]['car']['premium'] * 1.0, electric=r['legs'][0]['car']['electric'] * 1.0)
    extra = pd.DataFrame([feat[(s, r)] for s, r in zip(df.seed, df.rid)], index=df.index); df = pd.concat([df, extra], axis=1); df.to_pickle(T + 'rows8.pkl')
M = json.load(open('/var/lib/amp-runner/src/bahn-data/data/map.json')); P = {p['id']: p for p in M['places']}; MIN = {(r['from'], r['to']): r['minutes'] for r in M['roads']}
def km(a, b):
    p, q = P[a], P[b]; la1, la2 = math.radians(p['lat']), math.radians(q['lat'])
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin(math.radians(q['lon'] - p['lon']) / 2) ** 2
    return 2 * 6371 * math.asin(math.sqrt(h))
df['pick'] = df.pickup; df['deliv'] = df.delivery
dev_all = df.seed.str.startswith('dev')
if 'A' in sys.argv[1:] or len(sys.argv) == 1:
    q = df[~df.declined & (df.markup > 1.0) & (df.markup < 3)].copy().reset_index(drop=True); dev = q.seed.str.startswith('dev')
    BASE = [('lm', 'num', 0), ('lt', 'num', 0), ('sd', 'cat', 0), ('nosd', 'num', 0), ('llist', 'num', 0), ('legs2', 'num', 0), ('lates', 'num', 0), ('pick', 'cat', 2.0), ('deliv', 'cat', 2.0)]
    out = {}
    for name, mask in (('study', ~dev), ('dev', dev), ('all', dev | ~dev)):
        g = q[mask]
        f = pd.DataFrame(dict(lm=np.log(g.markup), lt=np.log(1 + g.trust / 100), sd=g.seed + '/' + g.day.astype(str), nosd=(~g.opts.str.startswith('same')) * 1.0, llist=np.log(g['list'] / g.legs / 60),
            legs2=(g.legs == 2) * 1.0, lates=np.minimum(g.lates, 3) * 1.0, pick=g.pick, deliv=g.deliv))
        X, names, pen = design(f, BASE); b, nll = logit(X, g.won.values * 1.0, pen); co = dict(zip(names, b)); s = -1 / co['lm']
        out[name] = dict(pick={k[5:]: round(v * s, 3) for k, v in co.items() if k.startswith('pick_')}, deliv={k[6:]: round(v * s, 3) for k, v in co.items() if k.startswith('deliv_')}, scale=s,
                         nosd=co['nosd'] * s, llist=co['llist'] * s, lt=co['lt'] * s, legs2=co['legs2'] * s)
        print(name, 'scale %.4f nosd %.3f llist %.3f trust %.3f legs2 %.3f' % (s, co['nosd'] * s, co['llist'] * s, co['lt'] * s, co['legs2'] * s))
    a, b = out['study'], out['dev']
    print('pickup effects, study against dev: corr', np.corrcoef([a['pick'][k] for k in P], [b['pick'][k] for k in P])[0, 1].round(2), ' delivery:', np.corrcoef([a['deliv'][k] for k in P], [b['deliv'][k] for k in P])[0, 1].round(2))
    pickle.dump(out, open(T + 'place8.pkl', 'wb'))
# (B) the cost
w = df[df.won & (df.legs == 1)].copy()
near = {}
for label in w.label.unique():
    for prefix in ('dev-', 't2-study-'):
        for seed, row in lab.weeks(label, prefix).items():
            if seed in near: continue
            roster = json.load(gzip.open(row['folder'] + '/roster.json.gz')); roster = roster.get('drivers', roster) if isinstance(roster, dict) else roster
            homes = [d['homePlaceId'] for d in roster]
            near[seed] = {p: (sum(km(p, h) <= 30 for h in homes), sum(km(p, h) <= 60 for h in homes)) for p in P}
w['cost'] = w.fee + w.refund + w.other; w['basis'] = w.ref; w['ratio'] = w.cost / w.basis; w['fratio'] = w.fee / w.basis
w['sd'] = w.opts.str.startswith('same') * 1.0; w['nx'] = 1 - w.sd; w['rl'] = np.log(w.basis / w['list'])
w['d30'] = [near[s][p][0] for s, p in zip(w.seed, w.delivery)]; w['p30'] = [near[s][p][0] for s, p in zip(w.seed, w.pickup)]
w['d60'] = [near[s][p][1] for s, p in zip(w.seed, w.delivery)]; w['p60'] = [near[s][p][1] for s, p in zip(w.seed, w.pickup)]
w['mins'] = [MIN[(a, b)] for a, b in zip(w.pickup, w.delivery)]; w['north'] = [(P[a]['lat'] > 64.5 or P[b]['lat'] > 64.5) * 1.0 for a, b in zip(w.pickup, w.delivery)]
w['dfew'] = (w.d30 < 20) * 1.0; w['pfew'] = (w.p30 < 20) * 1.0; w['mid'] = ((w.mins >= 150) & (w.mins < 300)) * 1.0; w['long'] = (w.mins >= 300) * 1.0
w['ld30'] = np.log(1 + w.d30); w['lp30'] = np.log(1 + w.p30); w['ld60'] = np.log(1 + w.d60); w['lp60'] = np.log(1 + w.p60); w['lmins'] = np.log(w.mins / 120)
dev = w.seed.str.startswith('dev'); print('orders', len(w), 'dev', int(dev.sum()), 'cost/typical', (w.cost.sum() / w.basis.sum()).round(3), 'fee/typical', (w.fee.sum() / w.basis.sum()).round(3))
for c, bins in (('d30', [-1, 5, 10, 20, 40, 80, 999]), ('p30', [-1, 5, 10, 20, 40, 80, 999]), ('mins', [0, 60, 150, 300, 999])):
    print(w.groupby(pd.cut(w[c], bins), observed=True).apply(lambda g: pd.Series(dict(n=len(g), fee=g.fee.sum() / g.basis.sum(), cost=g.cost.sum() / g.basis.sum(), late=g.isLate.mean(), price=g.price.sum() / g.basis.sum(), typical=g.basis.mean()))).round(3).T.to_string())
def X_of(ww, cols, cats):
    X = pd.DataFrame({'sd': ww.sd, 'nx': ww.nx, **{c: ww[c] for c in cols}}); pen = [0.0] * X.shape[1]
    for c in cats:
        d = pd.get_dummies(ww[c], prefix=c, dtype=float).reindex(columns=[c + '_' + p for p in P], fill_value=0.0); X = pd.concat([X, d], axis=1); pen += [300.0] * d.shape[1]
    return X, np.array(pen)
def fit(cols, cats, mask, y='ratio'):
    ww = w[mask]; X, pen = X_of(ww, cols, cats); wt = ww.basis.values
    A = X.values.T @ (X.values * wt[:, None]) + np.diag(pen); b = np.linalg.solve(A, X.values.T @ (ww[y].values * wt)); return dict(zip(X.columns, b))
def r2(co, cols, cats, mask, y='ratio'):
    ww = w[mask]; X, _ = X_of(ww, cols, cats); pred = X.values @ np.array([co[c] for c in X.columns])
    base = np.where(ww.sd == 1, (ww[ww.sd == 1][y] * ww[ww.sd == 1].basis).sum() / ww[ww.sd == 1].basis.sum(), (ww[ww.sd == 0][y] * ww[ww.sd == 0].basis).sum() / ww[ww.sd == 0].basis.sum())
    return 1 - ((ww[y] - pred) ** 2 * ww.basis).sum() / ((ww[y] - base) ** 2 * ww.basis).sum()
three = ['private', 'later', 'rl']
for y in ('ratio', 'fratio'):
    for name, cols, cats in [('three', three, []), ('+classes', three + ['dfew', 'pfew', 'mid', 'long', 'premium', 'north'], []), ('+logs', three + ['ld30', 'lp30', 'lmins', 'premium'], []), ('+logs60', three + ['ld60', 'lp60', 'lmins', 'premium'], []),
                             ('+places', three + ['premium'], ['pick', 'deliv']), ('+places logs', three + ['premium', 'ld30', 'lp30', 'lmins'], ['pick', 'deliv'])]:
        a, b = fit(cols, cats, dev, y), fit(cols, cats, ~dev, y)
        print(f'--- {y} {name}: fitted on study, R2 on study {r2(b, cols, cats, ~dev, y):.3f}, on dev {r2(b, cols, cats, dev, y):.3f}; fitted on dev, R2 on study {r2(a, cols, cats, ~dev, y):.3f}')
        if not cats: print('  study', {k: round(float(v), 3) for k, v in b.items()}); print('  dev  ', {k: round(float(v), 3) for k, v in a.items()})
cols, cats = three + ['premium'], ['pick', 'deliv']
out = {}
for name, mask in (('study', ~dev), ('dev', dev), ('all', dev | ~dev)):
    out[name] = fit(cols, cats, mask)
print('cost place effects on all:', {k: round(float(v), 2) for k, v in sorted(out['all'].items(), key=lambda kv: kv[1])})
pickle.dump(out, open(T + 'cost8.pkl', 'wb'))
# (C) the cost detail for the quoter: on all weeks, with the means over the orders, weighted by the typical fee
cols = three + ['premium', 'ld60', 'lp60', 'lmins']
for name, mask in (('study', ~dev), ('dev', dev), ('all', dev | ~dev)):
    co = fit(cols, [], mask); print('C', name, {k: round(float(v), 3) for k, v in co.items()}, 'means', {c: round(float(np.average(w[mask][c], weights=w[mask].basis)), 3) for c in cols})
co = fit(cols, [], dev | ~dev); X, _ = X_of(w, cols, []); pred = X.values @ np.array([co[c] for c in X.columns]); print('sd of the predicted cost ratio', pred.std().round(3), 'quantiles', np.quantile(pred, [0.05, 0.25, 0.5, 0.75, 0.95]).round(2))
