"""Replays the dev weeks' quoted requests against a quoter, offline. A request has a limit markup: the fitted
level of its day, dealer, places and options, plus its own luck, drawn inside the bracket that the played weeks
put on it, plus the dealer's trust as the replay earns it. Costs are the order's own from a played week where
one won it (at the base's volume), times a congestion factor for the replay's volume.
Usage: sim.py name=k:v,k:v ...   (k:v are DialQuoter parameters; `flat:1.5` is the plain quoter)."""
import sys, pickle, heapq, math, random
sys.path.insert(0, '/var/lib/amp-runner/src/bahn-t2')
import importlib
T = '/var/lib/amp-runner/src/alt-lab/t2/'
SIM = pickle.load(open(T + 'sim.pkl', 'rb'))
S, KT, KL = SIM['scale'], SIM['kt'], SIM['kl']
RATIO = {'next': [1.27, 1.17, 1.31, 1.14, 1.28], 'next+with': [1.05, 1.05, 1.13, 1.16, 1.16], 'same': [0.98, 1.01, 1.02, 1.02, 1.10]}
LATE = {'next': 0.10, 'next+with': 0.03, 'same': 0.02}
LAG = {'next': 1500, 'next+with': 2200, 'same': 1300}
CONGESTION = 0.118

class FakeDesk:
    now = 0

import json, gzip, os
sys.path.insert(0, T)
import lab
from dispatch.context import Context
MAP = json.load(open('/var/lib/amp-runner/src/bahn-data/data/map.json'))
CTX = {}
def ctx_of(seed):
    if seed not in CTX:
        roster = json.load(gzip.open(lab.weeks('base@f5a6b3b')[seed]['folder'] + '/roster.json.gz')); roster = roster.get('drivers', roster) if isinstance(roster, dict) else roster
        CTX[seed] = Context.build(8, MAP, roster)
    return CTX[seed]
if os.environ.get('LANES') == 'study':  # the place table fitted without the dev weeks that the replay plays
    import places_study, dispatch.quote as _q
    _q.PICKUP, _q.DELIVERY = places_study.PICKUP, places_study.DELIVERY

def group(opts): return 'same' if opts.startswith('same') else opts
def F(x): return 1 / (1 + math.exp(-x / S)) if abs(x / S) < 700 else (0.0 if x < 0 else 1.0)

def play(seed, make, draw):
    rng = random.Random(f'{seed}/{draw}')
    quoter, desk = make(), FakeDesk()
    desk.ctx = ctx_of(seed)
    trust, lates, late_orders, on_time = {}, {}, set(), set()
    heap, n = [], 0
    rows = SIM['seeds'][seed]
    for i, r in enumerate(rows):
        heapq.heappush(heap, (r['at'], 0, i, 'ask'))
    out = []
    while heap:
        at, _, i, what = heapq.heappop(heap); r = rows[i]; req = r['request']; d = req['dealerId']; desk.now = at
        if what == 'ask':
            lo, hi = F(r['lo']), F(r['hi'])
            u = rng.uniform(lo, hi) if lo < hi else (lo + hi) / 2
            u = min(max(u, 1e-9), 1 - 1e-9)
            r_eps = S * math.log(u / (1 - u))
            quoter.observe({'kind': 'price_request', 'at': at, 'request': req}, desk, False)
            prices = quoter.prices(req, desk)
            base = next((o for o in req['options'] if o['kind'] != 'same_day'), req['options'][0])
            markup = prices.get(base['kind'], 1e9) / base['listPriceCents']
            heapq.heappush(heap, (req['respondBy'], 1, i, ('answer', markup, r_eps)))
        elif what[0] == 'answer':
            _, markup, eps = what
            limit = r['theta0'] + KT * math.log(1 + trust.get(d, 0) / 100) + KL * min(lates.get(d, 0), 3) + eps
            if math.log(markup) < limit:
                quoter.observe({'kind': 'order_won', 'at': at, 'order': {'id': req['id'], 'dealerId': d}}, desk, False)
                g = group(r['opts'])
                cost = r['cost'] if r['cost'] is not None else RATIO[g][r['day']] * r['ref']
                late = r['late'] if r['late'] is not None else rng.random() < LATE[g]
                paid = r['paid'] if r['paid'] is not None else LAG[g]
                out.append((r, markup, cost, late))
                heapq.heappush(heap, (r['at'] + paid, 2, i, ('paid', late)))
            else:
                quoter.observe({'kind': 'order_lost', 'at': at, 'requestId': req['id']}, desk, False)
        else:
            late = what[1]
            quoter.observe({'kind': 'ledger', 'at': at, 'line': {'kind': 'revenue', 'orderId': req['id'], 'cents': 0}}, desk, False)
            if late:
                quoter.observe({'kind': 'ledger', 'at': at, 'line': {'kind': 'late_refund', 'orderId': req['id'], 'cents': 0}}, desk, False)
                trust[d] = trust.get(d, 0) // 2; lates[d] = lates.get(d, 0) + 1
            else:
                trust[d] = min(25, trust.get(d, 0) + 1)
    return out

BASE_N = {}
def score(make, draws=2, seeds=None):
    """(margin in € over the weeks, orders, mean markup won, late share, per-seed margins), averaged over the draws."""
    seeds = seeds or sorted(SIM['seeds']); per = {}
    tot = n = mk = late = 0.0
    for seed in seeds:
        m_seed = 0.0
        for draw in range(draws):
            won = play(seed, make, draw)
            mult = 1 + CONGESTION * (len(won) / BASE_N[seed] - 1) if seed in BASE_N else 1.0
            margin = sum(markup * r['list'] - cost * mult for r, markup, cost, _ in won) / 100
            m_seed += margin / draws; n += len(won) / draws; mk += sum(x[1] for x in won) / draws; late += sum(x[3] for x in won) / draws
        per[seed] = m_seed; tot += m_seed
    return tot, n, mk / max(n, 1), late / max(n, 1), per

def maker(spec):
    quote = importlib.import_module('dispatch.quote')
    params = {}
    for kv in filter(None, spec.split(',')):
        k, v = kv.split(':'); params[k] = v if k == 'cls' else float(v)
    if 'flat' in params:
        return lambda: quote.Quoter(markup=params['flat'], options='all')
    cls = getattr(quote, params.pop('cls', 'DialQuoter'))
    return lambda: cls(**params)

def calibrate():
    quote = importlib.import_module('dispatch.quote')
    for seed in sorted(SIM['seeds']):
        BASE_N[seed] = len(play(seed, lambda: quote.Quoter(markup=1.5, options='all'), 0))
calibrate()

if __name__ == '__main__':
    for arg in sys.argv[1:]:
        name, _, spec = arg.partition('=')
        tot, n, mk, late, per = score(maker(spec))
        print(f'{name:28s} €{tot:8.0f}  orders {n:6.0f}  markup {mk:.3f}  late {late:.3f}  ' + ' '.join(f'{v:6.0f}' for v in per.values()), flush=True)
