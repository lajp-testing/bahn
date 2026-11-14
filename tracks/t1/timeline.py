"""Each late order's story in one saved week: won, deadline, every post (fee), booking, drop, delivery.

    python3 tracks/t1/timeline.py <seed> <label>
"""
import collections, gzip, json, os, sys
sys.path.insert(0, os.getcwd())
from harness import config
from harness.orders import orders_of
from harness.play import read_index

def hm(t): return f"{'MTWTFSS+++'[min(t // 1440, 9)]}{t % 1440 // 60:02d}:{t % 60:02d}"
seed, label = sys.argv[1], sys.argv[2]
row = [r for r in read_index() if r["label"] == label and r["seed"] == seed][-1]
folder = os.path.join(config.RUNS, os.path.basename(row["folder"]))
ev = [json.loads(l) for l in gzip.open(os.path.join(folder, "events.jsonl.gz"), "rt")]
acts = [json.loads(l) for l in gzip.open(os.path.join(folder, "actions.jsonl.gz"), "rt")]
gig_orders, story = {}, collections.defaultdict(list)
for a in acts:
    act = a["action"]
    if act["type"] == "post" and a["result"].get("ok"):
        g = a["result"]["id"]; gig_orders[g] = {s["orderId"] for s in act["stops"]}
        for o in gig_orders[g]: story[o].append((a.get("at", 0), f"post {g[-4:]} fee {act.get('fee', act.get('fees'))}"))
    elif act["type"] not in ("post", "quote"):
        for o in gig_orders.get(act.get("gigId", ""), ()): story[o].append((a.get("at", 0), f"{act['type']} {act.get('gigId','')[-4:]} {act.get('fee', act.get('fees', ''))}"))
dl = {}
for e in ev:
    k = e["kind"]
    if k in ("order_won", "order_changed"): dl[e["order"]["id"]] = e["order"]["deadline"]; story[e["order"]["id"]].append((e["at"], k))
    elif "gigId" in e and k.startswith("gig_") or k == "no_show":
        for o in gig_orders.get(e.get("gigId"), ()): story[o].append((e["at"], f"{k} {e['gigId'][-4:]}"))
    elif "orderId" in e and k not in ("ledger",):
        story[e["orderId"]].append((e["at"], k))
late = [r for r in orders_of(folder) if r["late"]]
for r in sorted(late, key=lambda r: dl[r["id"]]):
    print(f"\n{r['id'][-6:]} km {r['km']:.0f} {r['option']} deadline {hm(dl[r['id']])}")
    for t, s in sorted(story[r["id"]], key=lambda x: x[0]): print(f"   {hm(t)} {s}")
