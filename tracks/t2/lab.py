"""Saved weeks on ankka -> one row per request. Reads files only."""
import collections, gzip, json
INDEX = '/var/lib/amp-runner/src/bahn-data/data/runs.jsonl'

def weeks(label, prefix='dev-'):
    out = {}
    for line in open(INDEX):
        row = json.loads(line)
        if row['label'] == label and row['seed'].startswith(prefix) and not row.get('board'):
            out[row['seed']] = row
    return dict(sorted(out.items()))

def reveal(d): return json.load(gzip.open(d + '/reveal.json.gz'))
def events(d): return [json.loads(l) for l in gzip.open(d + '/events.jsonl.gz', 'rt')]

def declined(req, quote):
    first = req['options'][0]
    return not quote or (len(quote) == 1 and quote.get(first['kind']) == first['listPriceCents'] * 5)

def rows(label, prefix='dev-'):
    """One row per request of the label's weeks, with the order's ledger when won and the dealer's trust at the quote."""
    out = []
    for seed, w in weeks(label, prefix).items():
        ev = events(w['folder'])
        led = collections.defaultdict(collections.Counter)
        won_at, lost, trust_at, lates_at, lates = {}, set(), {}, {}, collections.Counter()
        trust, on_time, late, dealer_of, rev_at, late_at = collections.Counter(), set(), set(), {}, {}, {}
        req = {}
        for e in ev:
            k = e['kind']
            if k == 'price_request':
                r = e['request']; req[r['id']] = (r, e['at']); trust_at[r['id']] = trust[r['dealerId']]; lates_at[r['id']] = lates[r['dealerId']]
            elif k == 'order_won':
                won_at[e['order']['id']] = e['order']; dealer_of[e['order']['id']] = e['order']['dealerId']
            elif k == 'order_lost': lost.add(e['requestId'])
            elif k == 'ledger' and e['line'].get('orderId'):
                o, lk = e['line']['orderId'], e['line']['kind']
                led[o][lk] += e['line']['cents']
                if lk == 'revenue': rev_at.setdefault(o, e['at'])
                if o in dealer_of:
                    d = dealer_of[o]
                    if lk == 'revenue' and o not in late and o not in on_time:
                        on_time.add(o); trust[d] = min(25, trust[d] + 1)
                    elif lk in ('late_refund', 'undelivered_penalty') and o not in late:
                        late.add(o); late_at[o] = e['at']; lates[d] += 1; trust[d] = (trust[d] - (1 if o in on_time else 0)) // 2
        quotes = {x['request']['id']: x for x in reveal(w['folder'])['requests']}
        for rid, (r, at) in req.items():
            q = quotes.get(rid, {})
            quote = q.get('quote') or {}
            kinds = [o['kind'] for o in r['options']]
            base = next((o for o in r['options'] if o['kind'] != 'same_day'), r['options'][0])
            o = won_at.get(rid)
            l = led[rid]
            row = dict(label=label, seed=seed, rid=rid, at=at, day=at // 1440, hour=at % 1440 / 60, dealer=r['dealerId'], legs=len(r['legs']),
                       opts='+'.join(k[:4] for k in kinds), list=base['listPriceCents'] / 100, ref=r['referenceFeeCents'] / 100,
                       declined=declined(r, quote), won=o is not None, trust=trust_at[rid], lates=lates_at[rid], sd_quoted='same_day' in quote, batch=r.get('batchId') is not None,
                       pickup=r['legs'][0]['pickup']['placeId'], delivery=r['legs'][0]['delivery']['placeId'], note=bool(r.get('note')),
                       markup=(quote.get(base['kind'], 0) / base['listPriceCents']) if quote else 0.0)
            if o is not None:
                row.update(opt=o['option'], price=o['priceCents'] / 100, rev=l['revenue'] / 100, fee=-l['driver_fee'] / 100,
                           refund=-(l['late_refund'] + l['undelivered_penalty']) / 100,
                           other=-sum(v for k, v in l.items() if k not in ('revenue', 'driver_fee', 'late_refund', 'undelivered_penalty')) / 100,
                           isLate=rid in late, rev_at=rev_at.get(rid, float('nan')), deadline=o['deadline'])
            out.append(row)
    return out
