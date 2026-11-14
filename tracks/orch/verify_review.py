"""Checks the review's claims (docs/reviews/2026-11-14-whole-repo-review.md) on a label's saved weeks."""
import gzip, json, sys
from collections import Counter
from pathlib import Path
label = sys.argv[1]
rows = [json.loads(l) for l in open('data/runs.jsonl')]
c = Counter(); drop_fee = []; reasons = Counter()
for x in {r['seed']: r for r in rows if r['label'] == label}.values():
    folder = Path('data/runs') / Path(x['folder']).name
    ev = [json.loads(l) for l in gzip.open(folder / 'events.jsonl.gz', 'rt')]
    acts = [json.loads(l) for l in gzip.open(folder / 'actions.jsonl.gz', 'rt')]
    c['weeks'] += 1
    typ = {e['request']['id']: e['request']['referenceFeeCents'] for e in ev if e['kind'] == 'price_request'}
    orders = {}
    for e in ev:
        if e['kind'] in ('order_won', 'order_changed'): orders[e['order']['id']] = e['order']
    gig_orders = {}; sched = {}
    for a in acts:
        act, res = a['action'], a['result']
        if act['type'] == 'post':
            ids = list(dict.fromkeys(s['orderId'] for s in act['stops']))
            if res.get('ok'): gig_orders[res['id']] = ids; sched[res['id']] = act['schedule']
            else:
                c['refused posts'] += 1; reasons[res.get('reason', '')[:40]] += 1
                if len(ids) == 1: c['refused one-order posts'] += 1
        if act['type'] == 'reprice' and res.get('ok'): sched[act['gigId']] = act['schedule']
    # 1/2: orders never delivered
    pen = {e['line']['orderId'] for e in ev if e['kind'] == 'ledger' and e['line']['kind'] == 'undelivered_penalty'}
    c['undelivered orders'] += len(pen)
    c['undelivered penalty €'] += -sum(e['line']['cents'] for e in ev if e['kind'] == 'ledger' and e['line']['kind'] == 'undelivered_penalty') / 100
    # 3: gigs that expired more than an hour after their order's last pickup minute
    for e in ev:
        if e['kind'] == 'gig_expired' and e['gigId'] in gig_orders:
            o = orders.get(gig_orders[e['gigId']][0])
            if o and e['at'] - o['lastPickupAt'] > 60: c['expired >1h after lastPickupAt'] += 1; c['dead hours'] += (e['at'] - o['lastPickupAt']) / 60
    # 4: fee before and after a drop
    last_fee = {}
    for e in ev:
        if e['kind'] == 'gig_booked' and e['gigId'] in gig_orders:
            g = e['gigId']; t = sum(typ.get(o, 0) for o in gig_orders[g]) or 1
            if g in last_fee and last_fee[g][1]:
                top = max(s['feeCents'] for s in sched[g]); drop_fee.append((last_fee[g][0] / t, e['feeCents'] / t, e['feeCents'] >= top))
            last_fee[g] = (e['feeCents'], False)
        if e['kind'] == 'gig_dropped' and e['gigId'] in last_fee: last_fee[e['gigId']] = (last_fee[e['gigId']][0], True); c['drops'] += 1
    # 5: orders with two or more deadline warnings
    warn = Counter(e['orderId'] for e in ev if e['kind'] == 'deadline_close')
    c['warned orders'] += len(warn); c['warned twice or more'] += sum(1 for n in warn.values() if n >= 2)
print(label, dict(c))
print('refusal reasons', reasons.most_common(5))
if drop_fee:
    n = len(drop_fee)
    print(f'rebooked drops {n}: fee/typical before {sum(a for a,b,t in drop_fee)/n:.2f}, after {sum(b for a,b,t in drop_fee)/n:.2f}, at the top step {sum(t for a,b,t in drop_fee)}')
