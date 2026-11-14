"""Peak undelivered orders due on each day, per week of a label: how full each due day gets."""
import gzip, json, sys
from pathlib import Path
rows = [json.loads(l) for l in open('data/runs.jsonl')]
seeds = None if len(sys.argv) < 3 else set(sys.argv[2].split(','))
label = sys.argv[1]
out = []
for x in sorted({r['seed']: r for r in rows if r['label'] == label}.values(), key=lambda r: r['onTimeShare']):
    if seeds and x['seed'] not in seeds: continue
    ev = [json.loads(l) for l in gzip.open(Path('data/runs') / Path(x['folder']).name / 'events.jsonl.gz', 'rt')]
    due = {}; open_ = {}; peak = {}
    for e in ev:
        if e['kind'] == 'order_won':
            o = e['order']; d = min(o['deadline'] // 1440, 7); due[o['id']] = d
            open_[d] = open_.get(d, 0) + 1; peak[d] = max(peak.get(d, 0), open_[d])
        elif e['kind'] in ('delivered', 'order_cancelled') and e['orderId'] in due:
            d = due.pop(e['orderId']); open_[d] -= 1
    print(x['seed'], round(100 * x['onTimeShare'], 1), ' '.join(f"{d}:{peak.get(d,0)}" for d in range(8)))
