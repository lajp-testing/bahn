"""What happened to the late orders of a label's saved weeks: dropped on the due day, never booked in time, or driven late."""
import gzip, json, sys
from collections import Counter
from pathlib import Path
rows = [json.loads(l) for l in open('data/runs.jsonl')]
for label in sys.argv[1:]:
    why = Counter(); n = 0; dropped_all = Counter()
    for x in {r['seed']: r for r in rows if r['label'] == label}.values():
        folder = Path('data/runs') / Path(x['folder']).name
        ev = [json.loads(l) for l in gzip.open(folder / 'events.jsonl.gz', 'rt')]
        acts = [json.loads(l) for l in gzip.open(folder / 'actions.jsonl.gz', 'rt')]
        gig_orders = {a['result']['id']: list(dict.fromkeys(s['orderId'] for s in a['action']['stops'])) for a in acts if a['action']['type'] == 'post' and a['result'].get('ok')}
        won = {e['order']['id']: e['order'] for e in ev if e['kind'] in ('order_won', 'order_changed')}
        lates = {e['line']['orderId'] for e in ev if e['kind'] == 'ledger' and e['line']['kind'] == 'late_refund'}
        drops = {}; books = {}; warned = {}
        for e in ev:
            for o in gig_orders.get(e.get('gigId'), []):
                if e['kind'] in ('gig_dropped', 'no_show'): drops.setdefault(o, []).append(e['at'])
                if e['kind'] == 'gig_booked': books.setdefault(o, []).append(e['at'])
            if e['kind'] == 'deadline_close': warned.setdefault(e['orderId'], e['at'])
        for o, order in won.items():
            day = order['deadline'] // 1440
            same_day_drop = any(at // 1440 == day for at in drops.get(o, []))
            dropped_all['dropped on due day'] += same_day_drop; dropped_all['of them late'] += same_day_drop and o in lates
        for o in lates:
            n += 1; order = won[o]; day = order['deadline'] // 1440
            if any(at // 1440 == day for at in drops.get(o, [])): why['driver dropped it on the due day'] += 1
            elif drops.get(o): why['driver dropped it earlier'] += 1
            elif o in warned: why['no driver until the deadline warning'] += 1
            else: why['booked in time, delivered late'] += 1
    print(label, 'late orders', n, dict(why.most_common()), dict(dropped_all))
