<img src="assets/icon.svg" width="64" height="64" alt="">

# bahn

A dispatcher for [Spread](https://spread.bahnexpress.com/llms.txt), Bahn's challenge at Junction 2026: it quotes car dealers and pays freelance drivers for one simulated week in Finland.

- `CLAUDE.md`: how the code is laid out and how to run practice weeks.
- `PLAN.md`: the approaches under test and the schedule.
- `docs/kit/`: the challenge's handbook, rules and API reference.

```sh
nix develop                                        # Python, numpy, pandas, pytest, ruff; loads the team key from .env
SPREAD_TRACK=orch python -m harness.run --policy base --seed spread-1
python -m pytest -q tests
```
