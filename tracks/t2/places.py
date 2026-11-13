"""Writes dispatch/places.py: what the competitor asks more for a car picked up at a place, and delivered to one, as the
log of the markup that a dealer accepts. Fitted on the quoted requests of this track's saved weeks (rows8.pkl, from
fit8.py: the labels c1n, c2n and c0n@1e30321 on the dev and the study seeds), beside the week's day, the options, the
list price and the dealer's trust. `places.py study` fits on the study weeks only, for a replay of the dev weeks."""
import sys; sys.path.insert(0, '/var/lib/amp-runner/src/alt-lab/t2')
import pandas as pd, numpy as np
from fitlib import design, logit
T = '/var/lib/amp-runner/src/alt-lab/t2/'
df = pd.read_pickle(T + 'rows8.pkl'); df['pick'] = df.pickup; df['deliv'] = df.delivery
q = df[~df.declined & (df.markup > 1.0) & (df.markup < 3)].copy().reset_index(drop=True)
only = sys.argv[1] if len(sys.argv) > 1 else 'all'
if only == 'study': q = q[q.seed.str.startswith('t2-study')].reset_index(drop=True)
F = pd.DataFrame(dict(lm=np.log(q.markup), lt=np.log(1 + q.trust / 100), sd=q.seed + '/' + q.day.astype(str), nosd=(~q.opts.str.startswith('same')) * 1.0, llist=np.log(q['list'] / q.legs / 60),
    legs2=(q.legs == 2) * 1.0, lates=np.minimum(q.lates, 3) * 1.0, pick=q.pick, deliv=q.deliv))
X, names, pen = design(F, [('lm', 'num', 0), ('lt', 'num', 0), ('sd', 'cat', 0), ('nosd', 'num', 0), ('llist', 'num', 0), ('legs2', 'num', 0), ('lates', 'num', 0), ('pick', 'cat', 2.0), ('deliv', 'cat', 2.0)])
b, nll = logit(X, q.won.values * 1.0, pen); co = dict(zip(names, b)); s = -1 / co['lm']
def table(col):
    t = {k[len(col) + 1:]: v * s for k, v in co.items() if k.startswith(col + '_')}; mean = q[col].map(t).mean()
    return {k: round(float(v - mean), 3) for k, v in sorted(t.items())}
pick, deliv = table('pick'), table('deliv')
def lines(t):
    items = [f'"{k}": {v}' for k, v in t.items()]
    return "\n".join("    " + ", ".join(items[i:i + 5]) + "," for i in range(0, len(items), 5))
text = f'''"""What the competitor asks more for a car picked up at a place, and for one delivered there: the log of the markup
that a dealer accepts, against the week's level. The handbook: one part of the competitor's lane factor "is almost
the same in every world". Fitted on {len(q):,} quoted requests of {q.seed.nunique()} practice weeks; written by tracks/t2/places.py."""

PICKUP = {{
{lines(pick)}
}}

DELIVERY = {{
{lines(deliv)}
}}
'''
out = T + 'places_study.py' if only == 'study' else '/var/lib/amp-runner/src/bahn-t2/dispatch/places.py'
open(out, 'w').write(text); print(out, 'scale', round(s, 4), 'sd pickup', np.std(list(pick.values())).round(3), 'delivery', np.std(list(deliv.values())).round(3))
