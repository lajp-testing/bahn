"""Reproduce the first request whose one-cent quote did not win."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from harness import config, slots
client = config.client()
with slots.create(client,level=8,seed='t2-scan-1') as world:
    step=world.advance(until=['price_request'],max=7000)
    while True:
        requests=[e['request'] for e in step['events'] if e['kind']=='price_request']
        target=next((r for r in requests if r['id']=='R00604'),None)
        if target:
            for oi,o in enumerate(target['options']):
                for price in [1,1,round(o['listPriceCents']*.5),o['listPriceCents'],o['listPriceCents']*2]:
                    with slots.fork(world) as copy:
                        out=copy.advance(to=target['respondBy'],actions=[{'type':'quote','requestId':target['id'],'prices':{o['kind']:price}}])
                        ev=[e for e in out['events'] if e['kind'] in ('order_won','order_lost') and (e.get('requestId')==target['id'] or e.get('order',{}).get('id')==target['id'])]
                        print(o['kind'],price,out['results'],ev,flush=True)
            break
        actions=[{'type':'quote','requestId':r['id'],'prices':{r['options'][0]['kind']:5*r['options'][0]['listPriceCents']}} for r in requests]
        if any(e['kind']=='order_won' for e in step['events']): raise RuntimeError('parent won')
        step=world.advance(until=['price_request'],max=7000,**({'actions':actions} if actions else {}))
