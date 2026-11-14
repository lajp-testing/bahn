"""How the bundles of a label's saved weeks did: by cars per gig, the share booked, the fee paid, drops and late cars."""
import gzip, json, sys
from pathlib import Path

label = sys.argv[1]
rows = {}
for line in open('data/runs.jsonl'):
    r = json.loads(line)
    if r['label'] == label: rows[r['seed']] = r
stat = {}
for seed, r in sorted(rows.items()):
    folder = Path('data/runs') / Path(r['folder']).name
    acts = [json.loads(l) for l in gzip.open(folder / 'actions.jsonl.gz', 'rt')]
    ev = [json.loads(l) for l in gzip.open(folder / 'events.jsonl.gz', 'rt')]
    typ = {e['request']['id']: e['request']['referenceFeeCents'] for e in ev if e['kind'] == 'price_request'}
    gigs = {}
    for a in acts:
        act = a['action']
        if act['type'] == 'post' and a['result'].get('ok'):
            orders = list(dict.fromkeys(s['orderId'] for s in act['stops']))
            gigs[a['result']['id']] = dict(at=a['at'], orders=orders, cars=sum(s['kind'] == 'pickup' for s in act['stops']), many=len(orders) > 1)
    late = {e['line']['orderId'] for e in ev if e['kind'] == 'ledger' and e['line']['kind'] == 'late_refund'}
    final = {}  # order -> the gig that delivered it
    booked = {}; fee = {}
    for e in ev:
        g = e.get('gigId')
        if g not in gigs: continue
        if e['kind'] == 'gig_booked': booked[g] = e['at']; fee[g] = e['feeCents']
        if e['kind'] in ('gig_dropped', 'no_show'):
            s = stat.setdefault(gigs[g]['cars'] if gigs[g]['many'] else 1, {}); s['drops'] = s.get('drops', 0) + 1
            booked.pop(g, None)
        if e['kind'] == 'delivered': final[e['orderId']] = g
    for g, info in gigs.items():
        s = stat.setdefault(info['cars'] if info['many'] else 1, {})
        s['posted'] = s.get('posted', 0) + 1
        if g in booked:
            s['booked'] = s.get('booked', 0) + 1
            s['fee'] = s.get('fee', 0) + fee[g]; s['typ'] = s.get('typ', 0) + sum(typ[o] for o in info['orders']) * (info['cars'] / max(1, len(info['orders'])) if not info['many'] else 1)
            s['mins'] = s.get('mins', []) + [booked[g] - info['at']]
    for order, g in final.items():
        s = stat.setdefault(gigs[g]['cars'] if gigs[g]['many'] else 1, {})
        s['delivered'] = s.get('delivered', 0) + 1; s['late'] = s.get('late', 0) + (order in late)
print(label, len(rows), 'weeks')
print('cars  gigs posted  kept a driver  drops  fee/typical  median min to booking  cars delivered  late')
for cars, s in sorted(stat.items()):
    m = sorted(s.get('mins', [0]))
    print(f"{cars:>4} {s.get('posted',0):>12} {s.get('booked',0):>14} {s.get('drops',0):>6} {s.get('fee',0)/max(1,s.get('typ',1)):>12.2f} {m[len(m)//2]:>22} {s.get('delivered',0):>15} {s.get('late',0)/max(1,s.get('delivered',1)):>5.1%}")
