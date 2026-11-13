"""Summarise driver fees and drops for saved experiment labels."""
import collections, gzip, json, sys
from pathlib import Path
from harness.play import read_index
for label in sys.argv[1:]:
    rows={r['seed']:r for r in read_index() if r['label']==label and r['seed'].startswith('dev-')}
    fee=delivered=drops=books=0
    for r in rows.values():
        path = Path(r['folder'])/'events.jsonl.gz'
        if not path.stat().st_size:
            print(label, r['seed'], 'empty events: excluded', file=sys.stderr)
            continue
        with gzip.open(path,'rt') as f:
            for line in f:
                e=json.loads(line)
                if e['kind']=='ledger' and e['line']['kind']=='driver_fee': fee-=e['line']['cents']
                elif e['kind']=='delivered': delivered+=1
                elif e['kind']=='gig_dropped': drops+=1
                elif e['kind']=='gig_booked': books+=1
    print(label, 'weeks',len(rows),'fees €',round(fee/100,2),'delivered legs',delivered,'fee €/leg',round(fee/100/delivered,2) if delivered else None,'drops',drops,'bookings',books)
