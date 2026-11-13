"""Scan independent single-option switching prices in a no-wins parent world."""
import argparse
import json
import sys
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from harness import config, slots


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seed', required=True)
    parser.add_argument('--level', type=int, default=8)
    parser.add_argument('--all-options', action='store_true')
    args = parser.parse_args()
    client = config.client()
    started = time.monotonic()
    path = Path('tracks/t2') / f'scan-{args.seed}-l{args.level}.jsonl'
    with path.open('w') as output, slots.create(client, level=args.level, seed=args.seed) as world:
        step = world.advance(until=['price_request'], max=7000)
        seen = set()
        while step['now'] < 7000:
            requests = [e['request'] for e in step['events'] if e['kind'] == 'price_request' and e['request']['id'] not in seen]
            seen.update(r['id'] for r in requests)
            for option_index in range(max((len(r['options']) if args.all_options else 1 for r in requests), default=0)):
                batch = [r for r in requests if len(r['options']) > option_index]
                low = {r['id']: 0.0 for r in batch}
                high = {r['id']: 4.0 for r in batch}
                # Check brackets explicitly; fail rather than silently censor.
                for iteration in range(9):
                    trial = {r['id']: (0.0 if iteration == 0 else 4.0 if iteration == 1 else (low[r['id']] + high[r['id']]) / 2) for r in batch}
                    actions = [{'type':'quote', 'requestId':r['id'], 'prices':{r['options'][option_index]['kind']:max(1, round(r['options'][option_index]['listPriceCents']*trial[r['id']]))}} for r in batch]
                    with slots.fork(world) as copy:
                        result = copy.advance(to=max(r['respondBy'] for r in batch), actions=actions)
                        if not all(x.get('ok') for x in result['results']):
                            raise RuntimeError(result['results'])
                        outcomes = {(e['order']['id'] if e['kind']=='order_won' else e['requestId']): e['kind'] for e in result['events'] if e['kind'] in ('order_won','order_lost')}
                        for r in batch:
                            rid = r['id']
                            won = outcomes[rid] == 'order_won'
                            if iteration == 0 and not won or iteration == 1 and won:
                                raise RuntimeError(f'unbracketed {rid} at {trial[rid]}: {won}')
                            if iteration >= 2:
                                (low if won else high)[rid] = trial[rid]
                for r in batch:
                    row = {'seed':args.seed, 'level':args.level, 'arrival':step['now'], 'option':r['options'][option_index]['kind'], 'listPriceCents':r['options'][option_index]['listPriceCents'], 'referenceFeeCents':r['referenceFeeCents'], 'switch_low':low[r['id']], 'switch_high':high[r['id']], 'request':r}
                    output.write(json.dumps(row, separators=(',', ':'))+'\n')
                output.flush()
            if len(seen) % 50 < len(requests):
                print('requests',len(seen),'http',client.requests,'seconds',round(time.monotonic()-started),flush=True)
            actions = [{'type':'quote','requestId':r['id'],'prices':{r['options'][0]['kind']:5*r['options'][0]['listPriceCents']}} for r in requests]
            step = world.advance(until=['price_request'], max=7000, **({'actions':actions} if actions else {}))
    print('done',len(seen),client.requests,round(time.monotonic()-started),flush=True)

if __name__ == '__main__':
    main()
