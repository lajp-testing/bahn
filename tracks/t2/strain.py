"""The quoter's strain signal on the control's weeks: (orders warned of their deadline or late) / (orders won), as it
stands at the end of each day, against what dearer costs (c2) and cheaper costs (c0) gained on that week."""
import sys; sys.path.insert(0, '/var/lib/amp-runner/src/alt-lab/t2')
import lab, pandas as pd, numpy as np
pd.set_option('display.width', 250); pd.set_option('display.max_rows', 100)
a = sys.argv[1]; others = sys.argv[2:]
out = {}
for prefix in ('dev-', 't2-study-'):
    for seed, row in lab.weeks(a, prefix).items():
        won = 0; strained = set(); r = {}
        day = 0
        for e in lab.events(row['folder']):
            while e['at'] >= (day + 1) * 1440 and day < 6:
                r[f's{day}'] = (len(strained) + 40 * 0.09) / (won + 40) - 0.09; r[f'raw{day}'] = len(strained) / max(won, 1); day += 1
            if e['kind'] == 'order_won': won += 1
            elif e['kind'] == 'deadline_close': strained.add(e['orderId'])
            elif e['kind'] == 'ledger' and e['line']['kind'] in ('late_refund', 'undelivered_penalty'): strained.add(e['line']['orderId'])
        r['end'] = len(strained) / won; r['margin'] = row['marginCents'] / 100
        for o in others:
            w = lab.weeks(o, prefix).get(seed)
            if w: r['gain ' + o.split('@')[0]] = w['marginCents'] / 100 - r['margin']
        out[seed] = r
t = pd.DataFrame(out).T
print(t.round(3).to_string()); print('mean share at the end', round(t.end.mean(), 4))
print(t.corr().filter(like='gain').round(2).to_string())
