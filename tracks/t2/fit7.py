"""Does the competitor's lane factor hold across worlds? The limit of each quoted request, fitted with an effect per
pickup place, delivery place and lane on one set of weeks, and used as a single feature on the other set."""
import sys, pickle, os; sys.path.insert(0, '/var/lib/amp-runner/src/alt-lab/t2')
import lab, pandas as pd, numpy as np
from fitlib import design, logit
T = '/var/lib/amp-runner/src/alt-lab/t2/'; pd.set_option('display.width', 250)
labels = ['c1n@1e30321', 'c2n@1e30321', 'c0n@1e30321']
cache = T + 'rows7.pkl'
if os.path.exists(cache): df = pd.read_pickle(cache)
else:
    df = pd.DataFrame([r for l in labels for p in ('dev-', 't2-study-') for r in lab.rows(l, p)]); df.to_pickle(cache)
q = df[~df.declined & (df.markup > 1.0) & (df.markup < 3)].copy().reset_index(drop=True)
print('quoted', len(q), 'won', q.won.mean().round(3))
q['pick'] = q.pickup; q['deliv'] = q.delivery; q['lane'] = q.pickup + '>' + q.delivery
def feats(q):
    return pd.DataFrame(dict(lm=np.log(q.markup), lt=np.log(1 + q.trust / 100), sd=q.seed + '/' + q.day.astype(str), nosd=(~q.opts.str.startswith('same')) * 1.0, llist=np.log(q['list'] / q.legs / 60),
        legs2=(q.legs == 2) * 1.0, lates=np.minimum(q.lates, 3) * 1.0, pick=q.pickup, deliv=q.delivery, lane=q.lane, dealer=q.dealer), index=q.index)
BASE = [('lm', 'num', 0), ('lt', 'num', 0), ('sd', 'cat', 0), ('nosd', 'num', 0), ('llist', 'num', 0), ('legs2', 'num', 0), ('lates', 'num', 0)]
dev = q.seed.str.startswith('dev')
def fit(mask, parts, extra=None):
    f = feats(q[mask])
    if extra is not None: f['x'] = extra[mask].values; parts = parts + [('x', 'num', 0)]
    X, names, pen = design(f, parts); b, nll = logit(X, q[mask].won.values * 1.0, pen)
    return dict(zip(names, b)), nll
for pen_p, pen_l in ((2.0, 1e9), (2.0, 8.0), (2.0, 3.0), (1e9, 3.0)):
    for name, a, b in (('fit study, test dev', ~dev, dev), ('fit dev, test study', dev, ~dev)):
        co, nll_a = fit(a, BASE + [('pick', 'cat', pen_p), ('deliv', 'cat', pen_p), ('lane', 'cat', pen_l)])
        s = -1 / co['lm']
        table = lambda col: q[col].map(lambda v: co.get(col + '_' + v, 0.0)) * s
        x = table('pick') + table('deliv') + table('lane')
        co0, nll0 = fit(b, BASE); co1, nll1 = fit(b, BASE, x)
        s1 = -1 / co1['lm']
        print(f'pen place {pen_p:g} lane {pen_l:g} | {name}: sd of the lane effect {x[a].std():.3f} (log markup); on the other set: nll {nll0:.1f} -> {nll1:.1f}, weight {co1["x"] * s1:.2f}, scale {-1 / co0["lm"]:.3f} -> {s1:.3f}')
# the full table, on all 30 weeks, for the quoter
co, _ = fit(q.index == q.index, BASE + [('pick', 'cat', 2.0), ('deliv', 'cat', 2.0), ('lane', 'cat', 8.0)]); s = -1 / co['lm']
pk = {k[5:]: v * s for k, v in co.items() if k.startswith('pick_')}; dl = {k[6:]: v * s for k, v in co.items() if k.startswith('deliv_')}; ln = {k[5:]: v * s for k, v in co.items() if k.startswith('lane_')}
print('scale', round(s, 4), 'pickup effects', {k: round(v, 3) for k, v in sorted(pk.items(), key=lambda kv: kv[1])})
print('delivery effects', {k: round(v, 3) for k, v in sorted(dl.items(), key=lambda kv: kv[1])})
print('lanes', len(ln), 'sd', np.std(list(ln.values())).round(3), 'nosd', co['nosd'] * s, 'llist', co['llist'] * s, 'lt', co['lt'] * s)
pickle.dump(dict(pick=pk, deliv=dl, lane=ln, scale=s), open(T + 'lane7.pkl', 'wb'))
