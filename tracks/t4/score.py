"""Score explicit reader claims against won-order leg truth in JSONL corpus."""
import json
import sys
from collections import Counter
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from dispatch.notes import read_note

fields = {'earliest_pickup': 'readyAt', 'pickup_hours': 'pickupHours', 'release': 'releasedAt', 'delivery_hours': 'deliveryHours', 'deadline': 'noteDeadline', 'manual': 'manualGearbox', 'plates': 'needsPlates', 'summer_tyres': 'summerTyres'}
counts = {field: Counter() for field in fields}
notes = Counter()
for line in sys.stdin:
    row = json.loads(line)
    if row['truth'] is None:
        continue
    facts = read_note(row['request'])
    notes['sure' if facts.sure else 'unsure'] += 1
    for leg in row['truth']:
        for field, truth in fields.items():
            value = getattr(facts, field)
            if value is None:
                counts[field]['unsure'] += 1
            else:
                counts[field]['right' if value == leg[truth] else 'wrong'] += 1
print('notes', dict(notes))
for field, count in counts.items():
    print(field, *(f'{k}={count[k]}' for k in ('right', 'wrong', 'unsure')))
