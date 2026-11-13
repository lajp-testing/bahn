"""Over the dev and the study weeks: which signals of the control's week go with the gain of another label?"""
import sys; sys.path.insert(0, '/var/lib/amp-runner/src/alt-lab/t2')
import pandas as pd, numpy as np, json, gzip, lab
from scarce import table
pd.set_option('display.width', 280); pd.set_option('display.max_rows', 100)
a, b = sys.argv[1], sys.argv[2]
ta = pd.concat([table(a, 'dev-'), table(a, 't2-study-')]); tb = pd.concat([table(b, 'dev-'), table(b, 't2-study-')])
drv = {}
for prefix in ('dev-', 't2-study-'):
    for seed, row in lab.weeks(a, prefix).items():
        roster = json.load(gzip.open(row['folder'] + '/roster.json.gz')); roster = roster.get('drivers', roster) if isinstance(roster, dict) else roster
        drv[seed] = len(roster)
ta['drivers'] = pd.Series(drv); ta['per_driver'] = ta.orders / ta.drivers; ta['m_order'] = ta.margin / ta.orders
ta['gain_b'] = tb.margin - ta.margin; ta['b_orders'] = tb.orders
print(ta.round(3).to_string())
for name, m in (('all 30', ta.index == ta.index), ('dev', ta.index.str.startswith('dev')), ('study', ta.index.str.startswith('t2'))):
    print('correlation with the gain,', name); print(ta[m].corr().gain_b.round(2).to_frame().T.to_string())
print('means dev  ', ta[ta.index.str.startswith('dev')].mean().round(3).to_frame().T.to_string())
print('means study', ta[ta.index.str.startswith('t2')].mean().round(3).to_frame().T.to_string())
