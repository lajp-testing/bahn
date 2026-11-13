"""Shows notes of one kind with what was true: python3 tracks/t4/show.py <kind> [count] [seed-filter]"""
import json, random, sys
sys.path.insert(0, 'tracks/t4')
from delta import delta
DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
def hm(t): return f"{DAYS[t // 1440 % 7]}{t // 1440}+{t % 1440 // 60:02d}:{t % 60:02d}"
def hours(h): return None if h is None else f"{h['opens']//60:02d}:{h['opens']%60:02d}-{h['closes']//60:02d}:{h['closes']%60:02d}"
kind, count = sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 40
rows = [json.loads(l) for l in open('data/notes_corpus.jsonl')]
rows = [r for r in rows if r['truth'] and r['seed'].startswith('dev-0') and r['seed'] <= 'dev-08']
random.seed(7); random.shuffle(rows)
n = 0
for r in rows:
    q = r['request']; d = delta(q, r['truth'])
    if (kind == 'none' and d) or (kind != 'none' and kind not in d): continue
    leg = q['legs'][0]; t = r['truth'][0]
    info = f"arr {hm(q['arrivedAt'])} win {hm(leg['pickup']['window']['from'])}..{hm(leg['pickup']['window']['to'])} opts {[(o['kind'][:4], hm(o['deadline'])) for o in q['options']]}"
    if kind == 'ready': val = {i: hm(v) for i, v in d['ready'].items()}
    elif kind == 'release': val = {i: hm(v) for i, v in d['release'].items()}
    elif kind == 'deadline': val = {i: hm(v) for i, v in d['deadline'].items()}
    elif kind == 'pickup_hours': val = f"stated {hours(leg['pickup']['hours'])} real {hours(t['pickupHours'])}"
    elif kind == 'delivery_hours': val = f"stated {hours(leg['delivery']['hours'])} real {hours(t['deliveryHours'])}"
    else: val = d.get(kind, '')
    print(f"{q['note']['text']!r}\n    => {val} | {info} legs={len(q['legs'])} priv={leg['pickup']['privateAddress']}/{leg['delivery']['privateAddress']}")
    n += 1
    if n >= count: break
