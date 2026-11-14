"""Late cars whose gig was dropped: how long it sat open after the drop, and how many drivers looked and passed.

    python3 tracks/t1/dropwait.py <label> [seed prefix]
"""
import collections, gzip, json, os, sys
sys.path.insert(0, os.getcwd())
from harness import config
from harness.orders import orders_of
from harness.play import read_index

label, prefix = sys.argv[1], (sys.argv[2:] or ["dev", "rob"])
tot = collections.Counter()
for row in [r for r in read_index() if r["label"] == label and r["seed"].startswith(tuple(prefix))]:
    folder = os.path.join(config.RUNS, os.path.basename(row["folder"]))
    ev = [json.loads(l) for l in gzip.open(os.path.join(folder, "events.jsonl.gz"), "rt")]
    acts = [json.loads(l) for l in gzip.open(os.path.join(folder, "actions.jsonl.gz"), "rt")]
    gig_orders = {a["result"]["id"]: {s["orderId"] for s in a["action"]["stops"]} for a in acts if a["action"]["type"] == "post" and a["result"].get("ok")}
    last = {}; drop = {}; views = collections.Counter(); rebook = {}
    for e in ev:
        if e["kind"] in ("order_won", "order_changed"): last[e["order"]["id"]] = e["order"]["lastPickupAt"]
        g = e.get("gigId")
        for o in gig_orders.get(g, ()):
            if e["kind"] == "gig_dropped": drop[o] = e["at"]; rebook.pop(o, None); views[o] = 0
            elif e["kind"] == "gig_viewed" and o in drop and o not in rebook: views[o] += 1
            elif e["kind"] == "gig_booked" and o in drop: rebook.setdefault(o, e["at"])
    late = {r["id"] for r in orders_of(folder) if r["late"]}
    for o, t in drop.items():
        lastday = last[o] - t < 24 * 60
        k = ("late" if o in late else "ok") + ("/lastday" if lastday else "/earlier")
        tot[k] += 1; tot[k + " views"] += views[o]
    tot["weeks"] += 1; tot["late"] += len(late)
print(label, dict(tot))
