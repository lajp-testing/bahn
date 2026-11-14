"""Late share by the day an order is due, over a label's saved weeks."""
import gzip, json, sys
from pathlib import Path
rows = [json.loads(l) for l in open('data/runs.jsonl')]
for label in sys.argv[1:]:
    due = {}; late = {}; fri = []
    for x in {r['seed']: r for r in rows if r['label'] == label}.values():
        ev = [json.loads(l) for l in gzip.open(Path('data/runs') / Path(x['folder']).name / 'events.jsonl.gz', 'rt')]
        won = {e['order']['id']: e['order'] for e in ev if e['kind'] == 'order_won'}
        for e in ev:
            if e['kind'] == 'order_changed' and e['order']['id'] in won: won[e['order']['id']] = e['order']
        lates = {e['line']['orderId'] for e in ev if e['kind'] == 'ledger' and e['line']['kind'] == 'late_refund'}
        f = [0, 0]
        for o, order in won.items():
            d = min(order['deadline'] // 1440, 7)
            due[d] = due.get(d, 0) + 1; late[d] = late.get(d, 0) + (o in lates)
            if d == 4: f[0] += 1; f[1] += o in lates
        fri.append((x['seed'], f[0], f[1], round(100 * x['onTimeShare'], 1)))
    print(label, 'weeks', len(fri))
    print('  due day   ', '  '.join(f"{d}: {due[d]:>4} due {100 * late[d] / due[d]:>4.1f}% late" for d in sorted(due)))
    fri.sort(key=lambda t: t[3])
    print('  weakest weeks (seed, due Friday, late of them, on time %):', fri[:5])
