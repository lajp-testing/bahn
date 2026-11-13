"""Probe one open request with one sequential fork per quote."""
from harness import config, slots

client = config.client()
with slots.create(client, level=8, seed='t2-fork-1') as world:
    step = world.advance(until=['price_request'], max=1440)
    request = next(e['request'] for e in step['events'] if e['kind'] == 'price_request')
    option = request['options'][0]
    print('request', request['id'], 'option', option['kind'], 'list', option['listPriceCents'], flush=True)
    for multiplier in [1.0, 1.2, 1.4, 1.6, 1.8, 1.4, 1.2, 1.6]:
        with slots.fork(world) as copy:
            action = {'type': 'quote', 'requestId': request['id'], 'prices': {option['kind']: round(option['listPriceCents'] * multiplier)}}
            result = copy.advance(to=request['respondBy'], actions=[action])
            outcomes = [e['kind'] for e in result['events'] if e['kind'] in ('order_won', 'order_lost') and (e.get('requestId') == request['id'] or e.get('order', {}).get('id') == request['id'])]
            print(multiplier, result['results'], outcomes, flush=True)
print('requests', client.requests)
