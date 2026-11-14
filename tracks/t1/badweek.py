"""One seed under two labels: which cars went late, when they were won, and how long the unbooked queue was then.

    python3 tracks/t1/badweek.py rob-18 t1s11-base t1s13-safe80q-car95
"""
import collections, gzip, json, os, sys
sys.path.insert(0, os.getcwd())
from harness import config
from harness.orders import orders_of
from harness.play import read_index

seed, labels = sys.argv[1], sys.argv[2:]
for label in labels:
    row = [r for r in read_index() if r["label"] == label and r["seed"] == seed][-1]
    folder = os.path.join(config.RUNS, os.path.basename(row["folder"]))
    ev = [json.loads(l) for l in gzip.open(os.path.join(folder, "events.jsonl.gz"), "rt")]
    acts = [json.loads(l) for l in gzip.open(os.path.join(folder, "actions.jsonl.gz"), "rt")]
    gig_orders = {a["result"]["id"]: {s["orderId"] for s in a["action"]["stops"]} for a in acts if a["action"]["type"] == "post" and a["result"].get("ok")}
    won_at = {e["order"]["id"]: e["at"] for e in ev if e["kind"] == "order_won"}
    booked = {}; warned = set(); drops = collections.defaultdict(list)
    for e in ev:
        if e["kind"] == "gig_booked":
            for o in gig_orders.get(e["gigId"], ()): booked.setdefault(o, e["at"])
        if e["kind"] in ("gig_dropped", "no_show"):
            for o in gig_orders.get(e["gigId"], ()): drops[o].append(e["at"])
        if e["kind"] == "deadline_close": warned.add(e["orderId"])
    queue = lambda t: sum(1 for o, w in won_at.items() if w < t and booked.get(o, 10**9) > t)
    rows = orders_of(folder)
    for r in rows:
        r["won"] = won_at.get(r["id"], 0); r["q"] = queue(r["won"]); r["safe"] = not r["private"] and r["km"] < 300
        r["cause"] = "dropped" if drops.get(r["id"]) else "no driver till warning" if r["id"] in warned else "driven late"
    n = len(rows); late = [r for r in rows if r["late"]]
    print(f"\n== {label} {seed}: {n} orders, {len(late)} late, on time {1 - len(late) / n:.1%}, margin €{row['marginCents'] / 100:,.0f}")
    def show(title, key):
        g = collections.defaultdict(lambda: [0, 0])
        for r in rows: g[key(r)][0] += 1; g[key(r)][1] += r["late"]
        print(f"  {title}: " + "; ".join(f"{k} {a[0]}/{a[1]} late" for k, a in sorted(g.items())))
    band = lambda v, edges: next((f"<{e}" for e in edges if v < e), f">={edges[-1]}")
    show("km", lambda r: band(r["km"], [100, 300, 500]))
    show("private", lambda r: r["private"])
    show("option", lambda r: r["option"])
    show("day won", lambda r: r["won"] // 1440)
    show("queue at win", lambda r: band(r["q"], [20, 35, 50, 80]))
    show("safe & q>=35 (past limit)", lambda r: ("safe" if r["safe"] else "unsafe") + ("/past" if r["q"] >= 35 else "/under"))
    print("  late cause:", dict(collections.Counter(r["cause"] for r in late)))
    # deadline day of late orders
    dl = {e["order"]["id"]: e["order"]["deadline"] // 1440 for e in ev if e["kind"] in ("order_won", "order_changed")}
    print("  late by deadline day:", dict(sorted(collections.Counter(dl[r["id"]] for r in late).items())), " all by deadline day:", dict(sorted(collections.Counter(dl[r["id"]] for r in rows).items())))
    # queue by day at noon and 18:00
    print("  queue at 12:00/18:00:", " ".join(f"d{d}:{queue(d*1440+720)}/{queue(d*1440+1080)}" for d in range(7)))
    print("  wins per day:", dict(sorted(collections.Counter(r["won"] // 1440 for r in rows).items())))
