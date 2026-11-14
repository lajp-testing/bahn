"""Summarise the handoff's paired weeks; reject incomplete seed sets."""
import json
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[2]
G = defaultdict(dict)
for line in (ROOT / 'data/runs.jsonl').read_text().splitlines():
    row = json.loads(line)
    if not row.get('board'):
        G[row['label']][row['seed']] = row

CASES = [
    ('Baseline', 'b17-unsent3', 'b17-unsent3-rob'),
    ('Earlier fees 300', 'b18-early300', 'b18-early300-rob'),
    ('Earlier fees 480', 'b18-early480', 'b18-early480-rob'),
    ('Outage 0.25', 'b20-outage25', 'b20-outage25-rob'),
    ('Limit 35/45 (older code)', 'b15-bundle3-limit35', 'b16-bundle3-limit35-rob'),
    ('Car 1.0 (older code)', 'b15-bundle3-car10', 'b16-bundle3-car10-rob'),
    ('Patience 120 (older code)', 'b15-bundle3-patience120', 'b16-bundle3-patience120-rob'),
    ('Bundle 5 (older code)', 'b15-bundle5', 'b16-bundle5-rob'),
]
EXPECTED = {f'dev-{i:02}' for i in range(1, 11)} | {f'rob-{i:02}' for i in range(1, 21)}

def summary(rows):
    orders = sum(r['wonOrders'] for r in rows)
    return dict(margin=sum(r['marginCents'] for r in rows)/100,
                ontime=sum(r['wonOrders']*r['onTimeShare'] for r in rows)/orders*100,
                lowest=[(r['seed'], r['onTimeShare']*100) for r in sorted(rows, key=lambda r:r['onTimeShare'])[:3]],
                ranked=sum(bool(r['ranked']) for r in rows), weeks=len(rows))

out=[]
for name, dev, rob in CASES:
    rows=G[dev] | G[rob]
    assert set(rows)==EXPECTED, (name, EXPECTED-set(rows))
    out.append(dict(name=name, labels=[dev,rob], **summary(list(rows.values()))))
base=out[0]['margin']
lines=['| Setting (same 30 seeds) | Margin | Change | On time | Three lowest weeks | Ranked |',
       '|---|---:|---:|---:|---|---:|']
for r in out:
    lowest=', '.join(f'{s}: {p:.2f}%' for s,p in r['lowest'])
    lines.append(f"| {r['name']} | €{r['margin']:,.2f} | €{r['margin']-base:+,.2f} | {r['ontime']:.2f}% | {lowest} | {r['ranked']}/{r['weeks']} |")
print('\n'.join(lines))
for name, labels in [('Baseline 40', ['b17-unsent3','b17-unsent3-rob','b21-bundle3-holdout']), ('Earlier 300 40',['b18-early300','b18-early300-rob','b21-early300-holdout'])]:
    rows={s:r for label in labels for s,r in G[label].items()}
    assert len(rows)==40
    print(name, summary(list(rows.values())))
(ROOT/'tracks/orch/handoff-comparison.json').write_text(json.dumps(out,indent=2)+'\n')
(ROOT/'tracks/orch/handoff-comparison.md').write_text('\n'.join(lines)+'\n')
