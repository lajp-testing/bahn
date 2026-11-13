"""Check fixed and monotone outcomes on the first 30 requests."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from harness import config, slots

client = config.client()
count = bad_repeat = bad_monotone = 0
with slots.create(client, level=8, seed='t2-scan-check') as world:
    step = world.advance(until=['price_request'], max=7000)
    while count < 30:
        requests = [e['request'] for e in step['events'] if e['kind'] == 'price_request']
        if not requests:
            break
        results = {r['id']: [] for r in requests}
        for m in (0.8, 1.0, 1.2, 1.4, 1.6, 1.8, 2.0, 1.4):
            actions = [{'type': 'quote', 'requestId': r['id'], 'prices': {r['options'][0]['kind']: round(r['options'][0]['listPriceCents'] * m)}} for r in requests]
            with slots.fork(world) as copy:
                out = copy.advance(to=max(r['respondBy'] for r in requests), actions=actions)
                assert all(x.get('ok') for x in out['results']), out['results']
                outcomes = {(e['order']['id'] if e['kind']=='order_won' else e['requestId']): e['kind'] for e in out['events'] if e['kind'] in ('order_won','order_lost')}
                for r in requests:
                    results[r['id']].append(outcomes[r['id']] == 'order_won')
        for row in results.values():
            count += 1
            bad_repeat += row[3] != row[7]
            bad_monotone += any(not a and b for a,b in zip(row[:7],row[1:7]))
        print('count', count, 'repeat failures', bad_repeat, 'monotone failures', bad_monotone, flush=True)
        actions = [{'type':'quote','requestId':r['id'],'prices':{r['options'][0]['kind']:5*r['options'][0]['listPriceCents']}} for r in requests]
        step = world.advance(until=['price_request'], max=7000, actions=actions)
print('HTTP requests', client.requests, flush=True)
