"""Scores the note reader against the reveals' truth, per noted request that we won.

    python3 tracks/t4/score2.py train        the weeks used while writing the rules (dev-01 to dev-08)
    python3 tracks/t4/score2.py test         every other saved week
    python3 tracks/t4/score2.py train -v     also print each note read wrong or unsure

A note is right when every fact matches what was true: the first minute the car could be collected,
the real hours of both sites, the note's deadline, gearbox, plates and tyres. Facts that the note
states but that equal the request (the stated hours, the normal deadline) count as no change.
"""
from __future__ import annotations

import collections
import json
import os
import sys

sys.path.insert(0, os.getcwd())
from dispatch.reader import read  # noqa: E402
from harness import config  # noqa: E402

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def hm(t):
    return None if t is None else f"{DAYS[t // 1440 % 7]}{t // 1440}+{t % 1440 // 60:02d}:{t % 60:02d}"


def truth_of(request: dict, truth: list[dict]) -> dict:
    leg, t = request["legs"][0], truth[0]
    earliest = max(t["readyAt"], t["releasedAt"] or 0)
    def hours(real, stated):
        return None if real is None or stated is None or (real["opens"], real["closes"]) == (stated["opens"], stated["closes"]) else (real["opens"], real["closes"])
    return {
        "ready": earliest if earliest > leg["pickup"]["window"]["from"] else None,
        "pickup_hours": hours(t["pickupHours"], leg["pickup"]["hours"]),
        "delivery_hours": hours(t["deliveryHours"], leg["delivery"]["hours"]),
        "deadline": t["noteDeadline"],
        "manual": t["manualGearbox"], "plates": t["needsPlates"], "summer_tyres": t["summerTyres"],
    }


def read_of(request: dict) -> tuple[dict, bool]:
    facts = read(request["note"]["text"], request["note"]["language"], request["arrivedAt"])
    leg = request["legs"][0]
    def hours(span, stated):
        if span is None or stated is None:
            return None
        got = (span[0] if span[0] is not None else stated["opens"], span[1] if span[1] is not None else stated["closes"])
        return None if got == (stated["opens"], stated["closes"]) else got
    latest = max(option["deadline"] for option in request["options"])
    return {
        "ready": facts.ready if facts.ready is not None and facts.ready > leg["pickup"]["window"]["from"] else None,
        "pickup_hours": hours(facts.pickup_hours, leg["pickup"]["hours"]),
        "delivery_hours": hours(facts.delivery_hours, leg["delivery"]["hours"]),
        "deadline": facts.deadline if facts.deadline is not None and facts.deadline < latest else None,
        "manual": facts.manual, "plates": facts.plates, "summer_tyres": facts.summer_tyres,
    }, facts.sure


def main() -> None:
    which, verbose = sys.argv[1], "-v" in sys.argv
    rows = [json.loads(line) for line in open(os.path.join(config.DATA, "notes_corpus.jsonl"), encoding="utf-8")]
    train = lambda row: row["seed"].startswith("dev-0") and row["seed"] <= "dev-08"
    rows = [row for row in rows if row["truth"] and (train(row) if which == "train" else not train(row))]
    total = collections.Counter()
    fields = collections.defaultdict(collections.Counter)
    for row in rows:
        request = row["request"]
        want, (got, sure) = truth_of(request, row["truth"]), read_of(request)
        wrong = [key for key in want if want[key] != got[key]]
        outcome = "unsure" if not sure else "wrong" if wrong else "right"
        total[outcome] += 1
        if not sure:
            total["unsure, and the reading was " + ("wrong" if wrong else "right")] += 1
        if any(want.values()):
            total["notes that change something"] += 1
            total["  of these " + outcome] += 1
        for key in want:
            if want[key] or got[key]:
                fields[key]["right" if want[key] == got[key] else "wrong"] += 1
        if verbose and (wrong or not sure):
            show = lambda v: hm(v) if isinstance(v, int) and not isinstance(v, bool) else v
            print(f"{outcome.upper()} [{row['seed']} arr {hm(request['arrivedAt'])}] {request['note']['text']!r}")
            for key in wrong:
                print(f"      {key}: read {show(got[key])}, true {show(want[key])}")
    print(f"{which}: {len(rows)} noted requests with truth, {len({row['seed'] for row in rows})} weeks")
    for key in sorted(total):
        print(f"  {key:<42} {total[key]:>5}  {total[key] / len(rows):6.1%}")
    print("  per fact, where the note or the reader says something:")
    for key, count in fields.items():
        print(f"    {key:<15} right {count['right']:>4}  wrong {count['wrong']:>4}")


if __name__ == "__main__":
    main()
