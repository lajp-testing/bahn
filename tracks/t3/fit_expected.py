"""Fit on dev-01–06; validate on dev-07–10. Run with nix develop."""
import os
import numpy as np
from harness import config
from harness.play import read_index
from harness.orders import orders_of

rows = []
for run in read_index():
    if run['label'] == 't3-main-low20-v1' and run['seed'] in config.SEEDS['dev']:
        for row in orders_of(os.path.join(config.RUNS, os.path.basename(run['folder']))):
            row['seed'] = run['seed']
            rows.append(row)
def features(r):
    return [1, r['near_pickup'] < 30, r['near_delivery'] < 10, r['km'] >= 500, r['private']]
train = [r for r in rows if r['seed'] <= 'dev-06']
test = [r for r in rows if r['seed'] > 'dev-06']
x = np.array([features(r) for r in train], dtype=float)
typ = np.array([r['typical'] for r in train])
fee = np.array([r['fee'] for r in train])
coef = np.linalg.lstsq(x * typ[:, None], fee, rcond=None)[0]
late = np.linalg.lstsq(x, np.array([r['late'] for r in train], dtype=float), rcond=None)[0]
print('fit',len(train),'feature counts',x.sum(axis=0),'fee coefficients',coef,'late coefficients',late)
for name, group in [('fit',train),('test',test)]:
    xx = np.array([features(r) for r in group], dtype=float)
    pred = xx @ coef * np.array([r['typical'] for r in group])
    actual = np.array([r['fee'] for r in group])
    print(name,len(group),'MAE EUR',np.mean(abs(pred-actual)),'total actual/pred',sum(actual),sum(pred))
    for i, label in enumerate(['all','pickup<30','delivery<10','km>=500','private']):
        mask = xx[:,i].astype(bool)
        print(label,'n',sum(mask),'actual/pred',round(sum(actual[mask])),round(sum(pred[mask])),'late actual/pred',round(np.mean([r['late'] for r,m in zip(group,mask) if m]),3),round(np.mean(np.clip((xx @ late)[mask],0,1)),3))
