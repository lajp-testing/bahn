"""Late cars: for the orders that the `late` repair posted again past their last pickup minute, what they
cost (fees, refund tier) in a label against the same orders in another label. Reads saved weeks only.

    python3 tracks/t3/late_cars.py b26-fix-wol b26-fix-wo
"""
import collections, gzip, json, os, sys

DATA = "/home/agent/.t3/projects/bahn/data"


def weeks(label):
    rows = [json.loads(l) for l in open(os.path.join(DATA, "runs.jsonl"))]
    out = {}
    for r in rows:
        if r.get("label") == label:
            out[r["seed"]] = os.path.join(DATA, "runs", os.path.basename(r["folder"]))
    return out


def orders(folder):
    """order id -> facts: price, deadline, last pickup minute, fees, refund, tier, late minutes, the late reposts."""
    ev = [json.loads(l) for l in gzip.open(os.path.join(folder, "events.jsonl.gz"))]
    acts = [json.loads(l) for l in gzip.open(os.path.join(folder, "actions.jsonl.gz"))]
    snap = json.load(gzip.open(os.path.join(folder, "snapshot.json.gz")))
    o = {}
    lpa = {}
    gig_orders = collections.defaultdict(set)
    for g in snap["gigs"]:
        for s in g["stops"]:
            gig_orders[g["id"]].add(s["orderId"])
    warn = collections.Counter()
    for e in ev:
        if e["kind"] in ("order_won", "order_changed"):
            lpa[e["order"]["id"]] = e["order"]["lastPickupAt"]
        if e["kind"] == "deadline_close":
            warn[e["orderId"]] += 1
    for od in snap["orders"]:
        o[od["id"]] = dict(price=od["priceCents"], deadline=od["deadline"], lpa=od["lastPickupAt"], status=od["status"],
                           delivered=od["deliveredAt"], fee=0, refund=0, tier="", late_posts=[], warns=warn[od["id"]], booked=[])
    for e in ev:
        if e["kind"] == "ledger":
            ln = e["line"]
            if ln["kind"] == "driver_fee" and ln.get("gigId"):
                members = [m for m in gig_orders.get(ln["gigId"], ()) if m in o]
                for m in members:
                    o[m]["fee"] += ln["cents"] / len(members)
            elif ln["kind"] == "late_refund" and ln.get("orderId") in o:
                o[ln["orderId"]]["refund"] += ln["cents"]
                o[ln["orderId"]]["tier"] = ln["detail"].split(",")[-1].strip()
            elif ln["kind"] not in ("revenue", "driver_fee") and ln.get("orderId") in o:
                o[ln["orderId"]]["refund"] += ln["cents"]
                o[ln["orderId"]]["tier"] = o[ln["orderId"]]["tier"] or ln["kind"]
        if e["kind"] == "gig_booked":
            for m in gig_orders.get(e["gigId"], ()):
                if m in o:
                    o[m]["booked"].append((e["at"], e["feeCents"], e["gigId"]))
    # the late reposts: a post with no windows at a minute past the order's last pickup minute, in the same batch as a withdraw
    by_minute = collections.defaultdict(list)
    for a in acts:
        by_minute[a["at"]].append(a)
    post_gig = {}
    for a in acts:
        if a["action"]["type"] == "post" and a["result"].get("ok"):
            post_gig[a["result"]["id"]] = a
    for minute, batch in by_minute.items():
        withdrawn = any(a["action"]["type"] == "withdraw" for a in batch)
        for a in batch:
            act = a["action"]
            if act["type"] != "post" or not withdrawn:
                continue
            ids = {s["orderId"] for s in act["stops"]}
            if len(ids) == 1 and not any("window" in s for s in act["stops"]):
                oid = next(iter(ids))
                if oid in o and minute > o[oid]["lpa"] - 1 and a["result"].get("ok"):
                    o[oid]["late_posts"].append((minute, act["schedule"][0]["feeCents"], a["result"]["id"]))
    return o


def main(a, b):
    A, B = weeks(a), weeks(b)
    rows = []
    for seed in sorted(A):
        if seed not in B:
            continue
        oa, ob = orders(A[seed]), orders(B[seed])
        for oid, x in oa.items():
            if x["late_posts"]:
                y = ob.get(oid)
                rows.append((seed, oid, x, y))
    print(f"{len(rows)} orders posted again late in {a}")
    tot = collections.Counter()
    print(f"{'seed':7} {'order':7} {'price':>6} | {a[-4:]}: {'fee':>6} {'late h':>6} {'refund':>7} {'net':>7} | {b[-4:]}: {'fee':>6} {'late h':>6} {'refund':>7} {'net':>7}")
    for seed, oid, x, y in rows:
        def show(z):
            if z is None:
                return "   (not won)                     "
            late = (max(z["delivered"]) - z["deadline"]) / 60 if None not in z["delivered"] else 999
            return f"{z['fee']/100:6.0f} {late:6.1f} {z['refund']/100:7.0f} {(z['price']+z['refund']-z['fee'])/100:7.0f}"
        if len(tot) < 1 or tot["n"] < 30:
            print(f"{seed:7} {oid:7} {x['price']/100:6.0f} | {show(x)} | {show(y)}")
        tot["n"] += 1
        tot["fa"] += x["fee"]; tot["ra"] += x["refund"]
        if y is not None:
            tot["fb"] += y["fee"]; tot["rb"] += y["refund"]; tot["both"] += 1
    print({k: (round(v / 100) if k not in ("n", "both") else v) for k, v in tot.items()})
    # first-step fee of the late repost relative to typical, from the reveal-free source: compare with the dead gig's last fee
    tiers = collections.Counter((x["tier"], (y or {}).get("tier", "notwon")) for _, _, x, y in rows)
    for k, v in tiers.most_common(12):
        print(v, k)


if __name__ == "__main__":
    main(*sys.argv[1:3])
