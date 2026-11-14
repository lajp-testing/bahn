"""How many of a week's won orders could share a gig with another won order? Reads saved weeks of one label."""
import gzip, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from dispatch.context import Context

label, dead_max = sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 30
rows = {}
for line in open('data/runs.jsonl'):
    r = json.loads(line)
    if r['label'] == label: rows[r['seed']] = r
world_map = json.load(open(next(Path('data').glob('map*.json')))) if list(Path('data').glob('map*.json')) else None
tot = dict(orders=0, paired=0, round=0, saved_home=0.0)
for seed, r in sorted(rows.items()):
    folder = Path('data/runs') / Path(r['folder']).name
    if world_map is None:
        from harness.play import world_map as wm
        raise SystemExit('no saved map')
    ctx = Context.build(8, world_map, [])
    won = {}; booked_at = {}; gig_order = {}
    for line in gzip.open(folder / 'events.jsonl.gz', 'rt'):
        e = json.loads(line)
        if e['kind'] == 'order_won' and len(e['order']['legs']) == 1: won[e['order']['id']] = (e['at'], e['order'])
    def fits(x, y, now):
        a, b = x['legs'][0], y['legs'][0]
        dx = ctx.minutes(a['pickup']['placeId'], a['delivery']['placeId']); dy = ctx.minutes(b['pickup']['placeId'], b['delivery']['placeId'])
        dead = 0 if a['delivery']['placeId'] == b['pickup']['placeId'] else ctx.minutes(a['delivery']['placeId'], b['pickup']['placeId'])
        if dead > dead_max or dx + dead + dy > 720: return None
        at = max(now + 120, a['pickup']['window']['from'])
        if at > min(a['pickup']['window']['to'], x['lastPickupAt']): return None
        at = max(at + dx + dead, b['pickup']['window']['from'])
        if at > min(b['pickup']['window']['to'], y['lastPickupAt']) or at + dy > b['delivery']['window']['to']: return None
        return dead
    cands = []
    ids = list(won)
    for i in ids:
        for j in ids:
            if i == j: continue
            now = max(won[i][0], won[j][0])
            d = fits(won[i][1], won[j][1], now)
            if d is not None:
                a, b = won[i][1]['legs'][0], won[j][1]['legs'][0]
                home = 0 if b['delivery']['placeId'] == a['pickup']['placeId'] else ctx.km(b['delivery']['placeId'], a['pickup']['placeId'])
                cands.append((d + home / 10, i, j, home))
    cands.sort(); used = set(); pairs = 0; rounds = 0
    for _, i, j, home in cands:
        if i in used or j in used: continue
        used |= {i, j}; pairs += 1; rounds += home <= 30
    print(seed, 'single-car orders', len(won), 'in pairs', 2 * pairs, 'of them round trips (home within 30 km)', 2 * rounds)
    tot['orders'] += len(won); tot['paired'] += 2 * pairs; tot['round'] += 2 * rounds
print(tot)
