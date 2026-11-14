"""Counts a label's direct offers in its saved weeks: sent, read (viewed in its 10 minutes), answers, and the
fee relative to the typical fee of the gig's cars and to the app's fee then. Run here, on saved weeks.

    python3 tracks/t5/offer_counts.py t2s9-offers
"""
import gzip, json, sys
from collections import Counter
from pathlib import Path

DATA = Path('/home/agent/.t3/projects/bahn/data')


def read(folder, name):
    with gzip.open(folder / name, 'rt') as f:
        return [json.loads(line) for line in f]


def main(label):
    rows = {}
    for line in (DATA / 'runs.jsonl').read_text().splitlines():
        row = json.loads(line)
        if row['label'] == label:
            rows[row['seed']] = row
    total, ratios, acc_ratios, app_ratios, acc_app = Counter(), [], [], [], []
    for seed, row in sorted(rows.items()):
        folder = DATA / 'runs' / Path(row['folder']).name
        events, actions = read(folder, 'events.jsonl.gz'), read(folder, 'actions.jsonl.gz')
        typical, sched, posts = {}, {}, {}
        requests = {e['request']['id']: e['request'] for e in events if e['kind'] == 'price_request'}
        for a in actions:
            act, res = a['action'], a['result']
            if act['type'] == 'post' and res.get('ok'):
                t = 0
                for s in act['stops']:
                    if s['kind'] == 'pickup':
                        r = requests[s['orderId']]
                        t += r['referenceFeeCents'] / len(r['legs'])
                typical[res['id']] = t
                sched[res['id']] = act['schedule']
            elif act['type'] == 'reprice' and res.get('ok'):
                sched[act['gigId']] = act['schedule']
            elif act['type'] == 'offer':
                key = (act['gigId'], act['driverId'])
                steps = [s['feeCents'] for s in sched.get(act['gigId'], []) if s['at'] <= a['at']]
                posts[key] = (a['at'], act['feeCents'], typical.get(act['gigId'], 0), steps[-1] if steps else 0, res.get('ok'))
        views = {}
        for e in events:
            if e['kind'] == 'gig_viewed':
                views.setdefault((e['gigId'], e['driverId']), []).append(e['at'])
        answers = {(e['gigId'], e['driverId']): e['answer'] for e in events if e['kind'] == 'offer_answered'}
        c = Counter()
        for key, (at, fee, t, app, ok) in posts.items():
            c['sent'] += 1
            c['refused'] += not ok
            c['read'] += any(at <= v <= at + 10 for v in views.get(key, []))
            ans = answers.get(key, 'none')
            c[ans] += 1
            if t:
                ratios.append(fee / t)
                if app:
                    app_ratios.append(fee / app)
                if ans == 'accepted':
                    acc_ratios.append(fee / t)
                    acc_app.append(fee / app if app else 0)
        total.update(c)
        print(seed, dict(c))
    med = lambda xs: sorted(xs)[len(xs) // 2] if xs else None
    print('total', dict(total))
    print('fee/typical median', med(ratios), 'accepted fee/typical', sorted(round(x, 2) for x in acc_ratios), 'fee/app median', med(app_ratios))


if __name__ == '__main__':
    main(sys.argv[1])
