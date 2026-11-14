"""Does the posting-to-booking delay climb before the late orders? Reads saved weeks of one label.

    python3 tracks/t1/bookdelay.py b26-fix-wo dev-07 rob-14 rob-08 dev-01 ...
Prints, per 12-hour block Mon..Fri: median minutes from posting to booking of gigs booked in the block,
open gigs older than 2 hours at the block's end, and late orders by their deadline's block.
"""
import gzip, json, statistics, sys
from pathlib import Path

DATA = Path("/home/agent/.t3/projects/bahn/data")


def week(folder):
    posted, booked, closed, deadline, done = {}, {}, {}, {}, {}
    for line in gzip.open(folder / "actions.jsonl.gz", "rt"):
        a = json.loads(line)
        if a["action"]["type"] == "post" and a["result"].get("ok"):
            posted[a["result"]["id"]] = a["at"]
        if a["action"]["type"] == "withdraw":
            closed.setdefault(a["action"]["gigId"], a["at"])
    for line in gzip.open(folder / "events.jsonl.gz", "rt"):
        e = json.loads(line)
        k = e["kind"]
        if k == "gig_booked":
            booked.setdefault(e["gigId"], e["at"])
        elif k in ("gig_expired",):
            closed.setdefault(e["gigId"], e["at"])
        elif k == "order_won":
            deadline[e["order"]["id"]] = e["order"]["deadline"]
        elif k == "order_changed" and "deadline" in e.get("order", {}):
            deadline[e["order"]["id"]] = e["order"]["deadline"]
        elif k == "delivered":
            done[e["orderId"]] = max(done.get(e["orderId"], 0), e["at"])
    return posted, booked, closed, deadline, done


def blocks(folder, size=720, n=10):
    posted, booked, closed, deadline, done = week(folder)
    med, old, late = [], [], [0] * n
    for b in range(n):
        lo, hi = b * size, (b + 1) * size
        d = [booked[g] - posted[g] for g in booked if g in posted and lo <= booked[g] < hi]
        med.append(round(statistics.median(d)) if d else -1)
        old.append(sum(1 for g, t in posted.items() if t < hi - 120 and booked.get(g, 1e9) >= hi and closed.get(g, 1e9) >= hi))
    for o, dl in deadline.items():
        if done.get(o, 1e9) > dl and dl // size < n:
            late[dl // size] += 1
    return med, old, late


if __name__ == "__main__":
    label, seeds = sys.argv[1], sys.argv[2:]
    rows = {}
    for line in open(DATA / "runs.jsonl"):
        r = json.loads(line)
        if r["label"] == label and r["seed"] in seeds:
            rows[r["seed"]] = r
    print("blocks: Mon am, Mon pm, ... Fri pm")
    for s in seeds:
        r = rows[s]
        med, old, late = blocks(DATA / "runs" / Path(r["folder"]).name)
        print(f"{s} {r['onTimeShare']*100:.1f}%  med {med}\n{'':13}old {old}\n{'':13}late{late}")
