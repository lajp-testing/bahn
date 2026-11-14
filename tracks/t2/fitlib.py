import numpy as np, pandas as pd
def logit(X, y, l2, iters=40):
    b = np.zeros(X.shape[1])
    for _ in range(iters):
        p = 1 / (1 + np.exp(-X @ b)); W = p * (1 - p) + 1e-9
        H = X.T @ (X * W[:, None]) + np.diag(l2 + 1e-4); g = X.T @ (y - p) - (l2 + 1e-4) * b
        step = np.linalg.solve(H, g); b += step
        if np.abs(step).max() < 1e-7: break
    p = 1 / (1 + np.exp(-X @ b))
    return b, -(y * np.log(p + 1e-12) + (1 - y) * np.log(1 - p + 1e-12)).sum()
def design(feats, parts):
    cols, names, pen = [], [], []
    for name, kind, penalty in parts:
        if kind == 'num':
            cols.append(feats[name].values[:, None]); names.append(name); pen.append(penalty)
        else:
            d = pd.get_dummies(feats[name], prefix=name, dtype=float)
            if penalty == 0: d = d.iloc[:, 1:]
            cols.append(d.values); names += list(d.columns); pen += [penalty] * d.shape[1]
    return np.hstack([np.ones((len(feats), 1))] + cols), ['const'] + names, np.array([0.0] + pen)
def run(feats, y, title, parts, show=()):
    X, names, pen = design(feats, parts); b, nll = logit(X, y, pen)
    bm = dict(zip(names, b))['lm']
    print(f'--- {title}: nll {nll:.1f}  scale {-1 / bm:.4f}  params {len(b)}')
    for n, v in zip(names, b):
        if any(n.startswith(s) for s in show): print(f'   {n:28s} {v:8.3f}  in log markup {v / -bm:7.3f}')
    return dict(zip(names, b)), X @ b
