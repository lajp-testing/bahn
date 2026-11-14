"""Does a week show how scarce its drivers are? The fee at each booking over the order's typical fee, by seed and day,
for a label; beside what the dearer costs of c2 gained over c1 on that seed."""
import sys, collections; sys.path.insert(0, '/var/lib/amp-runner/src/alt-lab/t2')
import lab, pandas as pd, numpy as np
pd.set_option('display.width', 250)
def table(label, prefix='dev-'):
    out = {}
    for seed, row in lab.weeks(label, prefix).items():
        ev = lab.events(row['folder'])
        ref = {e['request']['id']: e['request']['referenceFeeCents'] * len(e['request']['legs']) for e in ev if e['kind'] == 'price_request'}
        gig_order = {e['line']['gigId']: e['line']['orderId'] for e in ev if e['kind'] == 'ledger' and e['line'].get('gigId') and e['line']['kind'] == 'driver_fee'}
        r = collections.defaultdict(list); warn = collections.Counter(); late = collections.Counter(); won = collections.Counter(); exp = collections.Counter(); drop = collections.Counter()
        for e in ev:
            d = min(e['at'] // 1440, 5)
            if e['kind'] == 'gig_booked' and e['gigId'] in gig_order: r[d].append(e['feeCents'] / ref[gig_order[e['gigId']]])
            elif e['kind'] == 'deadline_close': warn[d] += 1
            elif e['kind'] == 'ledger' and e['line']['kind'] in ('late_refund', 'undelivered_penalty'): late[d] += 1
            elif e['kind'] == 'order_won': won[d] += 1
            elif e['kind'] == 'gig_expired': exp[d] += 1
            elif e['kind'] == 'gig_dropped': drop[d] += 1
        allr = [x for v in r.values() for x in v]
        out[seed] = dict(margin=row['marginCents'] / 100, orders=row['wonOrders'], fee_mon=np.mean(r[0]), fee_tue=np.mean(r[1]), fee_wed=np.mean(r[2]), fee_thu=np.mean(r[3]), fee_fri=np.mean(r[4]), fee_all=np.mean(allr),
                         at_open=np.mean([x < 0.87 for x in allr]), won_mon=won[0], won_tue=won[1], warn_mon_tue=warn[0] + warn[1], warn=sum(warn.values()), late=sum(late.values()), expired=sum(exp.values()), dropped=sum(drop.values()))
    return pd.DataFrame(out).T
if __name__ == '__main__':
    a, b = sys.argv[1], sys.argv[2]; prefix = sys.argv[3] if len(sys.argv) > 3 else 'dev-'
    ta, tb = table(a, prefix), table(b, prefix)
    ta['gain_b'] = tb.margin - ta.margin
    print(a, 'then the gain of', b); print(ta.round(3).to_string())
    print('correlation with the gain:'); print(ta.corr().gain_b.round(2).to_string())
