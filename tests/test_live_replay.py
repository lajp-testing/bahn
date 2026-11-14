import gzip
import json
from pathlib import Path

import pytest

from dispatch.context import Context
from dispatch.desk import Desk
from dispatch.policies.main import build
from dispatch.quote import decline


def test_saved_week_replay():
    root = Path('/home/agent/.t3/projects/bahn/data')
    index = root / 'runs.jsonl'
    if not index.exists():
        pytest.skip('saved practice weeks unavailable')
    rows = (json.loads(line) for line in index.read_text().splitlines())
    row = next((row for row in rows if row.get('label', '').startswith('b13-bundle3')), None)
    if row is None:
        pytest.skip('bundle week unavailable')
    folder = root / 'runs' / Path(row['folder']).name
    if not all((folder / name).exists() for name in ('events.jsonl.gz', 'actions.jsonl.gz', 'roster.json.gz')):
        pytest.skip('saved week files unavailable')
    def read(name):
        with gzip.open(folder / name, 'rt') as file:
            return [json.loads(line) for line in file]
    events, actions = read('events.jsonl.gz'), read('actions.jsonl.gz')
    with gzip.open(folder / 'roster.json.gz', 'rt') as file:
        roster = json.load(file)
    ctx = Context.build(8, json.loads((root / 'map.json').read_text()), roster)
    def desk():
        return Desk(None, ctx, build(ctx, fee_model=2, bundle=3), 0)
    timeline = sorted([(e['at'], 0, i, e) for i, e in enumerate(events)] +
                      [(a['at'], 1, i, a) for i, a in enumerate(actions)], key=lambda x: x[:3])
    cutoff = 3 * 1440
    def feed(d, rows):
        for minute, kind, _, item in rows:
            d.now = minute
            if not kind:
                if item['kind'] == 'price_request':
                    d.requests[item['request']['id']] = item['request']
                for part in d.parts.all():
                    part.observe(item, d, replay=True)
            else:
                action = item['action']
                if action['type'] == 'quote':
                    intake = d.parts.intake
                    intake.pending = {k: v for k, v in intake.pending.items() if v > minute}
                    request = d.requests[action['requestId']]
                    if action['prices'] != decline(request):
                        intake.pending[request['id']] = request['respondBy']
                for part in d.parts.all():
                    part.result(action, item['result'], d)
    uninterrupted, restarted = desk(), desk()
    feed(uninterrupted, timeline)
    history = [e for e in events if e['at'] <= cutoff]
    journal = [a for a in actions if a['at'] <= cutoff]
    restarted.rejoin({'now': cutoff, 'orders': [], 'gigs': [], 'openRequests': []}, history, journal)
    feed(restarted, [x for x in timeline if x[0] > cutoff])
    assert vars(uninterrupted.parts.quoter) == vars(restarted.parts.quoter)
    assert vars(uninterrupted.parts.intake) == vars(restarted.parts.intake)
