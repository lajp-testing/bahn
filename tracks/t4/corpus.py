"""Export requests and matching revealed truth as JSONL; pass run glob(s)."""
import glob
import gzip
import json
import sys

for pattern in sys.argv[1:]:
    for path in sorted(glob.glob(pattern)):
        with gzip.open(path, 'rt') as f:
            reveal = json.load(f)
        orders = {o['orderId']: o['legs'] for o in reveal['orders']}
        for item in reveal['requests']:
            request = item['request']
            if request.get('note'):
                print(json.dumps({'run': path, 'request': request, 'truth': orders.get(request['id'])}, ensure_ascii=False))
