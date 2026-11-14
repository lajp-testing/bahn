"""Offline: where b68 (floor 0.75/0.95, car_short 0.85) still loses, vs b52.

Reads saved weeks only (reveal/events/actions), no server. Stdlib only.

Per label, over the 30 dev+rob weeks:
  1. win rate, requests, mean quote/list, margin per won order by road-km band
     of the first leg (ctx.km(pickup, delivery) from data/map.json);
  2. the same by option kind and by weekday;
  3. single-car gigs: opening fee / typical fee, minutes to booking, share booked.

Rules (stated so the numbers can be checked):
  - quote/list = min over quoted kinds of price / that option's list price;
    requests with no quote at all are excluded from the mean (counted as `no quote`).
  - option kind: won -> the option the dealer took; lost -> the cheapest quoted
    kind, or the request's only offered option when nothing was quoted.
  - margin per won order = sum of that order's ledger lines (revenue, driver fees,
    refunds) over reveal outcome == won; cancelled orders keep their net ~0.
  - single-car gig = a post whose stops carry one orderId; the first such post
    per order is its opening gig (fee = schedule[0]).
"""
from __future__ import annotations

import gzip
import json
import os
import statistics
from collections import defaultdict

DATA = "/home/agent/.t3/projects/bahn/data"
WEEKS = ("dev-%02d" % i for i in range(1, 11))
SEEDS = [f"dev-{i:02d}" for i in range(1, 11)] + [f"rob-{i:02d}" for i in range(1, 21)]
LABELS = ("b68-floor075-short095-carshort085", "b52-fee4-car110")
BANDS = [(0, 50), (50, 100), (100, 200), (200, 300), (300, 500), (500, 10**9)]
DAYS = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")

with open(os.path.join(DATA, "map.json")) as fh:
    _map = json.load(fh)
ROAD_KM = {(r["from"], r["to"]): r["km"] for r in _map["roads"]}


def km(a: str, b: str) -> float:
    if (a, b) in ROAD_KM:
        return ROAD_KM[(a, b)]
    return ROAD_KM[(b, a)]


def band(k: float) -> int:
    for i, (lo, hi) in enumerate(BANDS):
        if lo <= k < hi:
            return i
    return len(BANDS) - 1


def weeks_for(label: str) -> list[str]:
    out = []
    with open(os.path.join(DATA, "runs.jsonl")) as fh:
        for line in fh:
            row = json.loads(line)
            if row["label"] == label and row["seed"] in SEEDS:
                out.append(os.path.basename(row["folder"]))
    return out


def load_week(folder: str):
    d = os.path.join(DATA, "runs", folder)
    with gzip.open(os.path.join(d, "reveal.json.gz"), "rt") as fh:
        reveal = json.load(fh)
    events, actions = [], []
    with gzip.open(os.path.join(d, "events.jsonl.gz"), "rt") as fh:
        for line in fh:
            events.append(json.loads(line))
    with gzip.open(os.path.join(d, "actions.jsonl.gz"), "rt") as fh:
        for line in fh:
            actions.append(json.loads(line))
    return reveal, events, actions


def analyse(label: str) -> dict:
    reqs, gigs = [], []
    for folder in weeks_for(label):
        reveal, events, actions = load_week(folder)
        gig_orders = {}
        for a in actions:
            act = a["action"]
            if act["type"] == "post" and a.get("result", {}).get("ok"):
                gig_orders[a["result"]["id"]] = {s["orderId"] for s in act["stops"]}
        margins, booked_at, first_post = {}, {}, {}
        for line in events:
            if line["kind"] == "ledger":
                ln = line["line"]
                if ln.get("orderId") is None and ln.get("gigId") in gig_orders:
                    # a multi-order gig's fee is shared among its orders
                    share = ln["cents"] / len(gig_orders[ln["gigId"]])
                    for oid in gig_orders[ln["gigId"]]:
                        margins[oid] = margins.get(oid, 0) + share
                else:
                    oid = ln.get("orderId")
                    margins[oid] = margins.get(oid, 0) + ln["cents"]
            elif line["kind"] == "gig_booked":
                booked_at[line["gigId"]] = line["at"]
        for a in actions:
            act = a["action"]
            if act["type"] != "post":
                continue
            orders = {s["orderId"] for s in act["stops"]}
            if len(orders) != 1 or not a.get("result", {}).get("ok"):
                continue
            oid = act["stops"][0]["orderId"]
            if oid not in first_post:
                first_post[oid] = (a["at"], act["schedule"][0]["feeCents"],
                                   a["result"]["id"])
        week_reqs = []
        for e in reveal["requests"]:
            rq = e["request"]
            leg = rq["legs"][0]
            k = km(leg["pickup"]["placeId"], leg["delivery"]["placeId"])
            lists = {o["kind"]: o["listPriceCents"] for o in rq["options"]}
            ratios = {kind: p / lists[kind]
                      for kind, p in (e.get("quote") or {}).items() if kind in lists}
            if e["outcome"] == "won":
                kind = e["option"]
            elif ratios:
                kind = min(ratios, key=lambda kk: (e["quote"][kk], kk))
            elif len(lists) == 1:
                kind = next(iter(lists))
            else:
                kind = "none"
            week_reqs.append({
                "id": rq["id"], "km": k, "band": band(k),
                "day": rq["arrivedAt"] // 1440,
                "won": e["outcome"] == "won",
                "kind": kind,
                "ratio": min(ratios.values()) if ratios else None,
                "margin": margins.get(rq["id"], 0) if e["outcome"] == "won" else None,
                "typical": rq["referenceFeeCents"],
            })
        reqs.extend(week_reqs)
        by_id = {r["id"]: r for r in week_reqs}
        for oid, (at, fee, gid) in first_post.items():
            r = by_id.get(oid)
            if r is None:
                continue
            gigs.append({
                "ratio": fee / r["typical"], "booked": gid in booked_at,
                "mins": (booked_at[gid] - at) if gid in booked_at else None,
            })
    return {"reqs": reqs, "gigs": gigs}


def table(rows, keys, reqs):
    """rows: list of key tuples; prints win rate, n, mean quote/list, margin/won."""
    print(f"| {' / '.join(keys)} | Requests | Won | Win % | Mean quote/list | Margin/won |")
    print("|---|---|---|---|---|---|")
    for key in rows:
        sel = [r for r in reqs if all(r[k] == v for k, v in zip(keys, key))]
        n = len(sel)
        if not n:
            continue
        won = [r for r in sel if r["won"]]
        ratios = [r["ratio"] for r in sel if r["ratio"] is not None]
        mq = statistics.mean(ratios) if ratios else float("nan")
        mw = sum(r["margin"] for r in won) / len(won) if won else float("nan")
        name = " / ".join(str(v) for v in key)
        print(f"| {name} | {n} | {len(won)} | {100 * len(won) / n:.0f}% | "
              f"{mq:.2f} | €{mw / 100:.0f} |")


def main():
    results = {}
    for label in LABELS:
        results[label] = analyse(label)
        reqs = results[label]["reqs"]
        won = [r for r in reqs if r["won"]]
        ratios = [r["ratio"] for r in reqs if r["ratio"] is not None]
        noq = sum(1 for r in reqs if r["ratio"] is None)
        print(f"\n=== {label} ===")
        print(f"weeks=30 requests={len(reqs)} won={len(won)} "
              f"win={100 * len(won) / len(reqs):.1f}% mean quote/list="
              f"{statistics.mean(ratios):.3f} no-quote={noq} "
              f"margin/won=€{sum(r['margin'] for r in won) / len(won) / 100:.0f}")

    band_names = ["0-50", "50-100", "100-200", "200-300", "300-500", "500+"]
    for label in LABELS:
        print(f"\n--- {label}: by road km of first leg ---")
        table([(b,) for b in range(len(BANDS))], ["band"], results[label]["reqs"])
    print("\nband order:", band_names)

    for label in LABELS:
        print(f"\n--- {label}: by option kind ---")
        kinds = sorted({r["kind"] for r in results[label]["reqs"]})
        table([(k,) for k in kinds], ["kind"], results[label]["reqs"])

    for label in LABELS:
        print(f"\n--- {label}: by weekday ---")
        days = sorted({r["day"] for r in results[label]["reqs"]})
        table([(d,) for d in days], ["day"], results[label]["reqs"])
    print("\nday index:", DAYS)

    for label in LABELS:
        gigs = results[label]["gigs"]
        print(f"\n--- {label}: single-car opening gigs (n={len(gigs)}) ---")
        floors = {"0.75": (0.74, 0.76), "0.85": (0.84, 0.86), "0.95": (0.94, 0.96),
                  "1.15": (1.14, 1.16)}
        used = set()
        for name, (lo, hi) in floors.items():
            sel = [g for g in gigs if lo <= g["ratio"] <= hi]
            used |= {id(g) for g in sel}
            show_bucket(name, sel, len(gigs))
        other = [g for g in gigs if id(g) not in used]
        show_bucket("other", other, len(gigs))
        bk = [g for g in gigs if g["booked"]]
        print(f"| all | {len(gigs)} | {100 * len(bk) / len(gigs):.0f}% booked | "
              f"median mins={statistics.median(g['mins'] for g in bk):.0f} |")


def show_bucket(name, sel, total):
    if not sel:
        print(f"| at {name} | 0 | 0% | - | - |")
        return
    bk = [g for g in sel if g["booked"]]
    mins = statistics.median([g["mins"] for g in bk]) if bk else float("nan")
    print(f"| at {name} | {len(sel)} ({100 * len(sel) / total:.0f}%) | "
          f"{100 * len(bk) / len(sel):.0f}% booked | median mins={mins:.0f} |")


if __name__ == "__main__":
    main()
