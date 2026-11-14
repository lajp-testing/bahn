"""Where our delivery capacity goes: drivers, chains, fees and losses in saved weeks.

    python3 tracks/t2/capacity.py [label]        # default b26-fix-wo

Reads only saved weeks (no worlds). A gig is a posted stop list; its driver is
the one who started it, its fee the driver_fee ledger lines with its id.
"""
from __future__ import annotations

import collections
import gzip
import json
import statistics as st
import sys
from pathlib import Path

DATA = Path("/home/agent/.t3/projects/bahn/data")
MAP = json.load(open(DATA / "map.json"))
MIN = {(r["from"], r["to"]): r["minutes"] for r in MAP["roads"]}
KM = {(r["from"], r["to"]): r["km"] for r in MAP["roads"]}


def load(folder):
    d = DATA / "runs" / folder
    ev = [json.loads(line) for line in gzip.open(d / "events.jsonl.gz")]
    ac = [json.loads(line) for line in gzip.open(d / "actions.jsonl.gz")]
    roster = json.load(gzip.open(d / "roster.json.gz"))
    reveal = json.load(gzip.open(d / "reveal.json.gz"))
    return ev, ac, roster, reveal


def week(folder):
    ev, ac, roster, reveal = load(folder)
    home = {r["id"]: r["homePlaceId"] for r in roster}
    req = {e["request"]["id"]: e["request"] for e in ev if e["kind"] == "price_request"}
    won = {e["order"]["id"]: e["order"] for e in ev if e["kind"] == "order_won"}
    quotes = {a["action"]["requestId"]: a["action"]["prices"] for a in ac if a["action"]["type"] == "quote"}
    gigs = {}
    for a in ac:
        if a["action"]["type"] == "post" and a["result"].get("ok"):
            gigs[a["result"]["id"]] = {"stops": a["action"]["stops"], "posted": a["at"],
                                       "first_fee": a["action"]["schedule"][0]["feeCents"]}
    fee = collections.Counter()
    for e in ev:
        if e["kind"] == "ledger" and e["line"]["kind"] == "driver_fee" and e["line"]["gigId"]:
            fee[e["line"]["gigId"]] -= e["line"]["cents"]
    first_book = {}
    for e in ev:
        if e["kind"] == "gig_booked":
            first_book.setdefault(e["gigId"], e["at"])
    started, booked_fee, ups, dels = {}, {}, collections.defaultdict(list), collections.defaultdict(list)
    for e in ev:
        k = e["kind"]
        if k == "gig_started":
            started[e["gigId"]] = (e["driverId"], e["at"])
        elif k == "gig_booked":
            booked_fee[e["gigId"]] = e["feeCents"]
        elif k == "picked_up":
            ups[e["gigId"]].append((e["at"], e["placeId"], e["orderId"]))
        elif k == "delivered":
            dels[e["gigId"]].append((e["at"], e["placeId"], e["orderId"]))
    viewers = {v["driverId"] for v in reveal["views"]}
    done = []  # one row per gig that delivered at least one car
    for g, (drv, t0) in started.items():
        if not dels.get(g):
            continue
        orders = {o for _, _, o in dels[g]}
        typical = sum(req[o]["referenceFeeCents"] for o in orders if o in req)
        p0 = min(ups[g])[1] if ups.get(g) else None
        d1 = max(dels[g])
        drive = 0
        for o in orders:
            lg = req[o]["legs"]
            drive += sum(MIN[(x["pickup"]["placeId"], x["delivery"]["placeId"])] for x in lg)
        done.append(dict(gig=g, drv=drv, home=home.get(drv), start=t0, first_up=min(ups[g])[0] if ups.get(g) else t0,
                         p0=p0, end=d1[0], dend=d1[1], cars=len(dels[g]), fee=fee[g], typ=typical, drive=drive,
                         orders=orders, pk={req[o]["legs"][0]["pickup"]["placeId"] for o in orders if o in req},
                         dl={req[o]["legs"][-1]["delivery"]["placeId"] for o in orders if o in req}))
    return dict(first_book=first_book, ev=ev, roster=roster, home=home, req=req, won=won, quotes=quotes, gigs=gigs, done=done, viewers=viewers)


def pct(xs, q):
    xs = sorted(xs)
    return xs[int(q * (len(xs) - 1))] if xs else float("nan")


def main():
    label = sys.argv[1] if len(sys.argv) > 1 else "b26-fix-wo"
    rows, seen = [], set()
    for line in open(DATA / "runs.jsonl"):
        r = json.loads(line)
        if r["label"] == label and r["seed"] not in seen and (DATA / "runs" / Path(r["folder"]).name).exists():
            seen.add(r["seed"])
            rows.append(r)
    print(f"{label}: {len(rows)} weeks")
    W = [week(Path(r["folder"]).name) for r in rows]
    n = len(W)

    # 1. Drivers
    used = [len({d["drv"] for d in w["done"]}) for w in W]
    roster = [len(w["roster"]) for w in W]
    views = [len(w["viewers"]) for w in W]
    gigs = [len(w["done"]) for w in W]
    cars = [sum(d["cars"] for d in w["done"]) for w in W]
    print("\n1. Drivers a week (median over weeks)")
    print(f"  roster {st.median(roster):.0f}  viewed one of our gigs {st.median(views):.0f}  "
          f"did one {st.median(used):.0f}  gigs {st.median(gigs):.0f}  cars {st.median(cars):.0f}")
    per_dd = collections.Counter()
    per_d = collections.Counter()
    for i, w in enumerate(W):
        for d in w["done"]:
            per_dd[(i, d["drv"], d["start"] // 1440)] += 1
            per_d[(i, d["drv"])] += 1
    dist = collections.Counter(min(v, 4) for v in per_dd.values())
    tot = sum(dist.values())
    print("  gigs per driver-day: " + "  ".join(f"{k}{'+' if k == 4 else ''}: {v / tot:.0%}" for k, v in sorted(dist.items())))
    dw = collections.Counter(min(v, 6) for v in per_d.values())
    tw = sum(dw.values())
    print("  gigs per driver-week: " + "  ".join(f"{k}{'+' if k == 6 else ''}: {v / tw:.0%}" for k, v in sorted(dw.items())))
    print(f"  driver-days worked for us {tot / n:.0f}/week; days of the week each driver works for us: "
          f"{tot / tw:.2f}")
    # bundle size
    bc = collections.Counter(min(d["cars"], 3) for w in W for d in w["done"])
    print("  cars per gig: " + "  ".join(f"{k}{'+' if k == 3 else ''}: {v / sum(bc.values()):.0%}" for k, v in sorted(bc.items())))

    # 2. Chains: same driver, consecutive gigs
    print("\n2. Same driver, next gig of ours (all consecutive pairs)")
    gaps_km, idle, same_day = [], [], 0
    pairs = 0
    for w in W:
        by = collections.defaultdict(list)
        for d in w["done"]:
            by[d["drv"]].append(d)
        for lst in by.values():
            lst.sort(key=lambda d: d["first_up"])
            for a, b in zip(lst, lst[1:]):
                pairs += 1
                if b["first_up"] // 1440 == a["end"] // 1440:
                    same_day += 1
                    gaps_km.append(KM[(a["dend"], b["p0"])])
                    idle.append(b["first_up"] - a["end"])
    print(f"  pairs {pairs / n:.1f}/week, same day {same_day / n:.1f}/week")
    if gaps_km:
        z = sum(1 for g in gaps_km if g <= 12)
        print(f"  same-day: next pickup km from last delivery median {st.median(gaps_km):.0f} "
              f"(same town {z / len(gaps_km):.0%}, <=30 km {sum(g <= 30 for g in gaps_km) / len(gaps_km):.0%}); "
              f"idle min median {st.median(idle):.0f}, p25 {pct(idle, .25)}, p75 {pct(idle, .75)}")

    # Driver hours: drive minutes per driver-day
    dd_drive = collections.Counter()
    dd_span = {}
    for i, w in enumerate(W):
        for d in w["done"]:
            k = (i, d["drv"], d["start"] // 1440)
            dd_drive[k] += d["drive"]
            s, e = dd_span.get(k, (10 ** 9, 0))
            dd_span[k] = (min(s, d["first_up"]), max(e, d["end"]))
    dv = list(dd_drive.values())
    print(f"  car-at-wheel minutes per driver-day: median {st.median(dv):.0f}, p75 {pct(dv, .75)}, p90 {pct(dv, .9)}")

    # 3. Fees per car over typical
    print("\n3. Fee paid / typical fee (gigs that delivered), median and count")
    def ratio(d):
        return d["fee"] / d["typ"] if d["typ"] else None
    groups = collections.defaultdict(list)
    for w in W:
        for d in w["done"]:
            r = ratio(d)
            if r is None or d["fee"] <= 0:
                continue
            groups[("cars", min(d["cars"], 3))].append(r)
            km = max(KM[(p, q)] for p in d["pk"] for q in d["dl"]) if d["pk"] and d["dl"] else 0
            groups[("lane km", "<60" if km < 60 else "60-200" if km < 200 else "200+")].append(r)
            h = d["home"]
            where = ("home=pickup" if h in d["pk"] else "home=delivery" if h in d["dl"] else
                     "home<=30km pickup" if any(KM[(h, p)] <= 30 for p in d["pk"]) else
                     "home<=30km delivery" if any(KM[(h, q)] <= 30 for q in d["dl"]) else "neither")
            groups[("driver", where)].append(r)
    for k in sorted(groups, key=str):
        v = groups[k]
        print(f"  {k[0]:8} {str(k[1]):22} {st.median(v):.2f}  n={len(v)}")
    fee_tot = sum(d["fee"] for w in W for d in w["done"])
    typ_tot = sum(d["typ"] for w in W for d in w["done"])
    print(f"  all: fee/typical {fee_tot / typ_tot:.2f}, fee per car EUR {fee_tot / sum(cars) / 100:.0f}")

    # 4. Requests by where drivers live
    print("\n4. Requests by drivers living at pickup / delivery (roster), single-car only")
    tab = collections.defaultdict(lambda: [0, 0, 0, []])  # requests, quoted, won, won price/list
    for w in W:
        homes = collections.Counter(w["home"].values())
        rost = len(w["roster"])
        for rid, rq in w["req"].items():
            if len(rq["legs"]) != 1:
                continue
            p, q = rq["legs"][0]["pickup"]["placeId"], rq["legs"][0]["delivery"]["placeId"]
            share = lambda pl: homes.get(pl, 0) / rost
            cp = "P+" if share(p) >= 0.03 else "P-"
            cd = "D+" if share(q) >= 0.03 else "D-"
            key = cp + cd
            t = tab[key]
            t[0] += 1
            qt = w["quotes"].get(rid, {})
            lst = {o["kind"]: o["listPriceCents"] for o in rq["options"]}
            if any(v <= 3 * lst.get(k, 1e9) for k, v in qt.items()):
                t[1] += 1
            if rid in w["won"]:
                t[2] += 1
                o = w["won"][rid]
                t[3].append(o["priceCents"] / lst[o["option"]])
    print("  (P+/D+ = town holds >=3% of the roster)   req/wk  quoted  won  win%  won price/list")
    for k in sorted(tab):
        r, qd, wn, pl = tab[k]
        print(f"  {k}   {r / n:6.0f}  {qd / n:6.0f}  {wn / n:4.0f}  {wn / max(qd, 1):4.0%}  {st.median(pl) if pl else 0:.2f}")
    # fee per car by the same split
    ft = collections.defaultdict(list)
    for w in W:
        homes = collections.Counter(w["home"].values())
        rost = len(w["roster"])
        for d in w["done"]:
            if d["cars"] != 1 or not d["typ"] or d["fee"] <= 0:
                continue
            p, q = next(iter(d["pk"])), next(iter(d["dl"]))
            key = ("P+" if homes.get(p, 0) / rost >= .03 else "P-") + ("D+" if homes.get(q, 0) / rost >= .03 else "D-")
            ft[key].append(d["fee"] / d["typ"])
    print("  single-car gig fee/typical: " + "  ".join(f"{k} {st.median(v):.2f}" for k, v in sorted(ft.items())))

    # 6. Backhauls: requests that start where a car of ours ends, soon after
    print("\n6. Requests whose pickup is within 30 km of a delivery of ours, open 30-180 min after it,\n   to within 30 km of that driver home (a ride home for our driver)")
    out = collections.Counter()
    plist = collections.defaultdict(list)
    for w in W:
        ends = [(d["end"], d["dend"], d["home"]) for d in w["done"] if d["home"]]
        for rid, rq in w["req"].items():
            if len(rq["legs"]) != 1:
                continue
            lg = rq["legs"][0]
            p, win = lg["pickup"]["placeId"], lg["pickup"]["window"]
            q = lg["delivery"]["placeId"]
            hit = any(KM[(x, p)] <= 30 and KM[(q, h)] <= 30 and KM[(x, h)] > 30 and rq["arrivedAt"] <= t + 120 and win["from"] <= t + 180 and win["to"] >= t + 30
                      for t, x, h in ends)
            qt = w["quotes"].get(rid, {})
            lst = {o["kind"]: o["listPriceCents"] for o in rq["options"]}
            kind = "won" if rid in w["won"] else "lost" if any(v <= 3 * lst.get(k, 1e9) for k, v in qt.items()) else "declined"
            out[(hit, kind)] += 1
            if kind == "lost" and qt:
                plist[hit].append(min(v / lst[k] for k, v in qt.items() if k in lst))
    for hit in (True, False):
        r = [out[(hit, k)] / n for k in ("won", "lost", "declined")]
        print(f"  {'backhaul' if hit else 'other   '}  won {r[0]:4.0f}  lost {r[1]:4.0f}  declined {r[2]:4.0f}  "
              f"win% of quoted {r[0] / max(r[0] + r[1], 1e-9):.0%}  lost at price/list {st.median(plist[hit]) if plist[hit] else 0:.2f}")

    # 7. Pair partners: a request that could join a gig of ours still unbooked when we quote
    print("\n7. Quoted requests with a partner among our gigs still open (unbooked) at the quote")
    print("   (next pickup within 30 km of the other car's delivery, windows overlap, either order)")
    out = collections.Counter()
    pl = collections.defaultdict(list)
    for w in W:
        open_gigs = []  # (posted, booked or inf, [(pickup, delivery, pwin, dwin)])
        for g, info in w["gigs"].items():
            legs = []
            for stp in info["stops"]:
                if stp["kind"] == "pickup" and stp["orderId"] in w["req"]:
                    lg = w["req"][stp["orderId"]]["legs"][stp["leg"]]
                    legs.append((lg["pickup"]["placeId"], lg["delivery"]["placeId"], lg["pickup"]["window"], lg["delivery"]["window"]))
            if len(legs) == 1:
                open_gigs.append((info["posted"], w["first_book"].get(g, 10 ** 9), legs[0]))
        for rid, rq in w["req"].items():
            if len(rq["legs"]) != 1:
                continue
            qt = w["quotes"].get(rid, {})
            lst = {o["kind"]: o["listPriceCents"] for o in rq["options"]}
            if not any(v <= 3 * lst.get(k, 1e9) for k, v in qt.items()):
                continue
            lg = rq["legs"][0]
            p, q, pw, dw = lg["pickup"]["placeId"], lg["delivery"]["placeId"], lg["pickup"]["window"], lg["delivery"]["window"]
            t = rq["respondBy"]
            hit = False
            for t0, t1, (op, oq, opw, odw) in open_gigs:
                if not (t0 <= t < t1):
                    continue
                after = KM[(oq, p)] <= 30 and pw["to"] >= opw["from"] + MIN[(op, oq)] and pw["from"] <= odw["to"] + 180
                before = KM[(q, op)] <= 30 and opw["to"] >= pw["from"] + MIN[(p, q)] and opw["from"] <= dw["to"] + 180
                if after or before:
                    hit = True
                    break
            kind = "won" if rid in w["won"] else "lost"
            out[(hit, kind)] += 1
            if kind == "lost":
                pl[hit].append(min(v / lst[k] for k, v in qt.items() if k in lst))
    for hit in (True, False):
        a, b = out[(hit, "won")] / n, out[(hit, "lost")] / n
        print(f"  {'partner   ' if hit else 'no partner'}  won {a:4.0f}  lost {b:4.0f}  win% {a / max(a + b, 1e-9):.0%}  "
              f"lost at price/list {st.median(pl[hit]) if pl[hit] else 0:.2f}")

    # 5. Ceiling: wheel minutes of the drivers who worked for us
    print("\n5. Capacity ceiling")
    wheel = sum(dv) / n
    dd = len(dv) / n
    print(f"  driver-days {dd:.0f}/week, wheel minutes {wheel:.0f}/week = {wheel / dd:.0f} per driver-day")
    per_car = st.median([d["drive"] / d["cars"] for w in W for d in w["done"]])
    print(f"  median wheel minutes per car {per_car:.0f}")
    for hrs in (4, 6):
        print(f"  if each driver-day carried {hrs} h at the wheel: {dd * hrs * 60 / per_car:.0f} cars/week "
              f"(now {st.median(cars):.0f})")


if __name__ == "__main__":
    main()
