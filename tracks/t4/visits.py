"""Summarize failed visits and account costs for paired indexed runs."""
import gzip
import json
import sys
from collections import Counter
from pathlib import Path

index = Path('/home/agent/.t3/projects/bahn/data/runs.jsonl')
rows = [json.loads(line) for line in index.open()]
labels = sys.argv[1:]
seeds = set.intersection(*[{r['seed'] for r in rows if r['label'] == label and (Path(r['folder']) / 'events.jsonl.gz').stat().st_size > 0} for label in labels])
print('paired seeds:', ', '.join(sorted(seeds)))
for label in labels:
    selected = {r['seed']: r for r in rows if r['label'] == label and r['seed'] in seeds}
    counts, costs = Counter(), Counter()
    for row in selected.values():
        with gzip.open(Path(row['folder']) / 'events.jsonl.gz', 'rt') as f:
            for line in f:
                event = json.loads(line)
                if event['kind'] == 'visit_failed':
                    counts[event['reason']] += 1
                elif event['kind'] == 'ledger' and event['line']['kind'] in ('failed_visit', 'waiting', 'fine'):
                    costs[event['line']['kind']] += event['line']['cents']
    print(label, 'visits', dict(counts), 'ledger cents', dict(costs))
