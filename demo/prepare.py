#!/usr/bin/env python3
"""Regenerates demo/assets/*.json from the saved 18:00 test final. Run from the repo root:

    python3 demo/prepare.py

Reads only files on disk (no server): the test final's events, journal, reveal, leaderboard
feed and the world's own driver list, and the shared map. The desk replay uses the settings
that actually played the week (commit fc3e132's mainline), so the internals it captures are
the ones the live desk computed; see README for what is exact.
"""
from __future__ import annotations

import gzip
import heapq
import os
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dispatch.context import Context
from dispatch.desk import Desk
from dispatch.policies import load
from dispatch.quote import decline

FINAL = ROOT / "tracks/orch/finals/testfinal-20261114-1800"
DATA = Path(os.environ.get("SPREAD_DATA", "/home/agent/.t3/projects/bahn/data"))
OUT = ROOT / "demo/assets"
EVENTS = FINAL / "events-1794678337.jsonl.gz"
JOURNAL = FINAL / "journal.jsonl.gz"
REVEAL = FINAL / "reveal.json.gz"
FEED = FINAL / "leaderboard-feed.sse.gz"
ROSTER = FINAL / "roster.json.gz"

# The mainline settings that played the 18:00 test final (fc3e132), passed as `--set` would:
# fee model 4, cost tilt 1.1 on every lane (no short-lane tilt yet), flat-fee floors 0.85/1.15,
# intake limits 35/45 with the safe-car allowance to 80, same-day quoted at 8 h of slack.
AS_PLAYED = dict(fee_model=4, car=1.1, car_short=0, fee_flat_floor=0.85, fee_flat_short=1.15,
                 limit=35, morning_limit=45, safe_limit=80, same_day_slack=480, same_day_drivers=0)

# Finland's real border (Natural Earth via datasets/geo-countries, public domain):
# demo/assets/finland.geojson, a MultiPolygon — the mainland ring and the islands.
# prepare.py simplifies each ring (points closer than MIN_DEG are dropped) and writes
# it as lat/lon rings into assets/map.json; the browser projects it like the towns.
MIN_DEG = 0.008


def load_border() -> list[list[list[float]]]:
    geo = json.loads((ROOT / "demo/assets/finland.geojson").read_text())["geometry"]
    rings = []
    for poly in geo["coordinates"]:
        for ring in poly:
            keep = []
            for lon, lat in ring:   # GeoJSON rings are [lon, lat]
                if not keep or abs(lat - keep[-1][0]) + abs(lon - keep[-1][1]) >= MIN_DEG:
                    keep.append([round(lat, 4), round(lon, 4)])
            if len(keep) > 3:
                rings.append(keep)
    rings.sort(key=len, reverse=True)
    return rings


BORDER = load_border()


def read_jsonl(path: Path):
    with gzip.open(path, "rt") as fh:
        for line in fh:
            yield json.loads(line)


def main() -> None:
    OUT.mkdir(exist_ok=True)
    world_map = json.loads((DATA / "map.json").read_text())
    events = list(read_jsonl(EVENTS))
    journal = list(read_jsonl(JOURNAL))
    reveal = json.loads(gzip.open(REVEAL, "rt").read())

    write_map(world_map)
    week, orders, ledger_lines = build_week(world_map, events, journal, reveal)
    (OUT / "week.json").write_text(json.dumps(week, separators=(",", ":")))
    print(f"week.json: {len(week['requests'])} requests, {len(week['moves'])} moves")
    build_decisions(world_map, events, journal, reveal, orders, ledger_lines)
    build_race()
    summarize(week, ledger_lines)


# --------------------------------------------------------------------------- map


def write_map(world_map: dict) -> None:
    roads, seen = [], set()
    for road in world_map["roads"]:
        pair = (road["from"], road["to"]) if road["from"] <= road["to"] else (road["to"], road["from"])
        if road["from"] == road["to"] or pair in seen:
            continue
        seen.add(pair)
        roads.append([road["from"], road["to"], road["km"]])
    data = {"places": world_map["places"], "roads": roads, "border": BORDER}
    (OUT / "map.json").write_text(json.dumps(data, separators=(",", ":")))
    print(f"map.json: {len(world_map['places'])} places, {len(roads)} roads")


def shortest_path(world_map: dict, src: str, dst: str) -> list[str]:
    """The fastest road route between two places, by the map's minutes (Dijkstra)."""
    minutes = {}
    for road in world_map["roads"]:
        minutes[(road["from"], road["to"])] = road["minutes"]
    heap, best, back = [(0, src, [])], {}, {}
    while heap:
        d, place, _ = heapq.heappop(heap)
        if place in best:
            continue
        best[place] = d
        if place == dst:
            break
        for other in {b for a, b in minutes if a == place}:
            if other not in best:
                step = d + minutes[(place, other)]
                if step < best.get(other, 1 << 60):
                    best[other] = step
                    back[other] = place
                    heapq.heappush(heap, (step, other, []))
    path, at = [dst], dst
    while at != src:
        at = back[at]
        path.append(at)
    return path[::-1]


# --------------------------------------------------------------------------- replay


class NoWorld:
    """The desk only uses its world to send actions; the replay feeds recorded ones."""


def build_week(world_map: dict, events: list, journal: list, reveal: dict):
    places = {p["id"]: p for p in world_map["places"]}
    requests = {e["request"]["id"]: e["request"] for e in events if e["kind"] == "price_request"}

    won, lost, orders = {}, {}, {}
    for e in events:
        if e["kind"] == "order_won":
            won[e["order"]["id"]] = e
            orders[e["order"]["id"]] = e["order"]
        elif e["kind"] == "order_lost":
            lost[e["requestId"]] = e
        elif e["kind"] == "order_changed":
            orders[e["order"]["id"]] = e["order"]
        elif e["kind"] == "order_cancelled":
            orders.pop(e["orderId"], None)

    # an order is late exactly when the account refunded it (or never delivered it)
    late_orders = {e["line"]["orderId"] for e in events
                   if e["kind"] == "ledger" and e["line"]["kind"] in ("late_refund", "undelivered_penalty")
                   and e["line"].get("orderId")}
    cancelled = [[e["at"], e["orderId"]] for e in events if e["kind"] == "order_cancelled"]

    gigs, bookings, drops, posts = {}, {}, [], {}
    for line in journal:
        action, result = line["action"], line["result"]
        if action["type"] == "post" and result.get("ok"):
            gigs[result["id"]] = line
            posts[result["id"]] = line["at"]
    for e in events:
        if e["kind"] == "gig_booked":
            bookings[e["gigId"]] = e
        elif e["kind"] in ("gig_dropped", "no_show"):
            drops.append(e)

    picked, delivered = {}, {}
    for e in events:
        if e["kind"] == "picked_up":
            picked[(e["orderId"], e["leg"])] = e
        elif e["kind"] == "delivered":
            delivered[(e["orderId"], e["leg"])] = e

    ledger_lines = [e for e in events if e["kind"] == "ledger"]

    # one move per leg of each live order, with its road path for the animation
    moves = []
    for oid, order in sorted(orders.items()):
        for leg, spec in enumerate(order["legs"]):
            pu, de = picked.get((oid, leg)), delivered.get((oid, leg))
            if pu is None:
                continue
            path = shortest_path(world_map, spec["pickup"]["placeId"], spec["delivery"]["placeId"])
            moves.append({
                "rid": oid, "leg": leg, "gid": pu["gigId"],
                "pu": pu["at"], "de": de["at"] if de else None,
                "p": spec["pickup"]["placeId"], "d": spec["delivery"]["placeId"],
                "path": [[places[p]["lat"], places[p]["lon"]] for p in path],
                "late": oid in late_orders,
            })

    week = {
        "requests": [{
            "id": r["id"], "at": r["arrivedAt"], "k": r["dealerId"],
            "p": r["legs"][0]["pickup"]["placeId"], "d": r["legs"][0]["delivery"]["placeId"],
            "n": len(r["legs"]), "t": r["referenceFeeCents"],
            "priv": any(l[s]["privateAddress"] for l in r["legs"] for s in ("pickup", "delivery")),
            "o": [[o["kind"], o["deadline"], o["listPriceCents"]] for o in r["options"]],
            "note": r["note"]["text"] if r["note"] else None,
        } for r in requests.values()],
        "won": [[e["at"], e["order"]["id"]] for e in won.values()],
        "lost": [[e["at"], r] for r, e in lost.items()],
        "posts": [[at, gid] for gid, at in sorted(posts.items(), key=lambda kv: kv[1])],
        "bookings": [[e["at"], e["gigId"], e["feeCents"]] for e in bookings.values()],
        "drops": [[e["at"], e["gigId"]] for e in drops],
        "moves": moves,
        "ledger": [[e["at"], e["line"]["kind"], e["line"]["cents"], e["line"].get("orderId")]
                   for e in ledger_lines],
        "gigOrders": {gid: sorted({s["orderId"] for s in line["action"]["stops"]})
                      for gid, line in gigs.items()},
        "deadline": {oid: o["deadline"] for oid, o in orders.items()},
        "lateOrders": sorted(late_orders),
        "cancelled": sorted(cancelled),
    }
    return week, orders, ledger_lines


def summarize(week: dict, ledger: list) -> None:
    kinds = {}
    for _, kind, cents, _ in week["ledger"]:
        total, n = kinds.get(kind, (0, 0))
        kinds[kind] = (total + cents, n + 1)
    print("ledger kinds:", {k: (round(v[0] / 100, 2), v[1]) for k, v in sorted(kinds.items())})


# --------------------------------------------------------------------------- decisions


def build_decisions(world_map: dict, events: list, journal: list, reveal: dict, orders: dict, ledger_lines: list):
    """Replays the whole week through the real desk and parts, feeding the recorded events and
    actions, and captures each part's state at the moment of every quote."""
    roster = json.loads(gzip.open(ROSTER, "rt").read())  # the final world's own driver list
    ctx = Context.build(8, world_map, roster)
    parts = load("main")(ctx, **AS_PLAYED)
    desk = Desk(NoWorld(), ctx, parts, now=0)

    requests = {e["request"]["id"]: e["request"] for e in events if e["kind"] == "price_request"}
    quotes = {}  # request id -> its journal quote line (one per request in this week)
    for line in journal:
        if line["action"]["type"] == "quote":
            quotes[line["action"]["requestId"]] = line

    # money per order, from the account
    gig_orders = {}
    for line in journal:
        a, res = line["action"], line["result"]
        if a["type"] == "post" and res.get("ok"):
            gig_orders[res["id"]] = sorted({s["orderId"] for s in a["stops"]})
    money = {}
    for e in ledger_lines:
        line = e["line"]
        oid = line.get("orderId")
        if line["kind"] == "revenue" and oid:
            money.setdefault(oid, {})["price"] = money.get(oid, {}).get("price", 0) + line["cents"]
        elif line["kind"] == "late_refund" and oid:
            money.setdefault(oid, {})["refund"] = money.get(oid, {}).get("refund", 0) - line["cents"]
        elif line["kind"] == "driver_fee":
            cost = -line["cents"]
            if oid:
                money.setdefault(oid, {})["fees"] = money.get(oid, {}).get("fees", 0) + cost
            else:
                for member in gig_orders.get(line.get("gigId"), []):
                    share = cost / len(gig_orders[line["gigId"]])
                    money.setdefault(member, {})["fees"] = money.get(member, {}).get("fees", 0) + share
        elif line["kind"] in ("failed_visit", "waiting", "fine", "release_fee", "undelivered_penalty") and oid:
            # every cost line is negative in the ledger; keep costs positive, by kind
            costs = money.setdefault(oid, {}).setdefault("otherCosts", {})
            kind = {"waiting": "waiting at a closed site", "failed_visit": "failed visit",
                    "fine": "fine", "release_fee": "release fee"}.get(line["kind"], line["kind"])
            costs[kind] = costs.get(kind, 0) - line["cents"]

    attributed = sum((m.get("price", 0) - m.get("fees", 0) - m.get("refund", 0)
                      - sum(m.get("otherCosts", {}).values())) for m in money.values())
    ledger_total = sum(e["line"]["cents"] for e in ledger_lines)
    loose = ledger_total - attributed
    assert abs(loose) <= 1, f"per-order money is off by {loose} cents"
    print(f"money: per-order nets {attributed / 100:.2f} + unattributed {loose / 100:.2f} = {ledger_total / 100:.2f}")

    late_orders = {e["line"]["orderId"] for e in ledger_lines
                   if e["line"]["kind"] in ("late_refund", "undelivered_penalty") and e["line"].get("orderId")}
    won_at, lost_at, cancelled = {}, set(), set()
    for e in events:
        if e["kind"] == "order_won":
            won_at[e["order"]["id"]] = e
        elif e["kind"] == "order_lost":
            lost_at.add(e["requestId"])
        elif e["kind"] == "order_cancelled":
            cancelled.add(e["orderId"])
    booked_at, booked_fee, booked_by = {}, {}, {}
    for e in events:
        if e["kind"] == "gig_booked":
            booked_at[e["gigId"]], booked_fee[e["gigId"]], booked_by[e["gigId"]] = e["at"], e["feeCents"], e["driverId"]
    views = {}
    for e in events:
        if e["kind"] == "gig_viewed":
            views.setdefault(e["gigId"], []).append(e["at"])
    views_before = {gid: sum(1 for at in times if at <= booked_at.get(gid, 1 << 60))
                    for gid, times in views.items()}
    picked, delivered = {}, {}
    for e in events:
        if e["kind"] == "picked_up":
            picked[(e["orderId"], e["leg"])] = e["at"]
        elif e["kind"] == "delivered":
            delivered[(e["orderId"], e["leg"])] = e["at"]
    gig_of = {}  # order -> the gig that moved it (the one that picked it up)
    for e in events:
        if e["kind"] == "picked_up":
            gig_of[e["orderId"]] = e["gigId"]
    gig_posts = {}  # gig id -> its post's minute and fee schedule, from the journal
    gig_history = {}  # order id -> its gigs' story, in minute order
    def gig_line(oid, at, kind, gig, fee=None, info=None):
        gig_history.setdefault(oid, []).append(
            {"at": at, "kind": kind, "gig": gig, "fee": fee, "info": info})
    for line in journal:
        a, res = line["action"], line["result"]
        members = sorted({s["orderId"] for s in a.get("stops", [])})
        if a["type"] == "post":
            for oid in members:
                if res.get("ok"):
                    gig_line(oid, line["at"], "posted", res["id"], a["schedule"][0]["feeCents"],
                             f"{len(members)} car{'s' if len(members) > 1 else ''}")
                else:
                    gig_line(oid, line["at"], "refused", None, None, res.get("reason", "")[:90])
        elif a["type"] == "reprice" and res.get("ok"):
            for oid in gig_orders.get(a["gigId"], []):
                gig_line(oid, line["at"], "repriced", a["gigId"], a["schedule"][0]["feeCents"])
        elif a["type"] == "withdraw" and res.get("ok"):
            for oid in gig_orders.get(a["gigId"], []):
                gig_line(oid, line["at"], "withdrawn", a["gigId"])
        if a["type"] == "post" and res.get("ok"):
            gig_posts[res["id"]] = {"at": line["at"], "schedule": a["schedule"]}
    for e in events:
        if e["kind"] == "gig_booked":
            for oid in gig_orders.get(e["gigId"], []):
                gig_line(oid, e["at"], "booked", e["gigId"], e["feeCents"], e["driverId"])
        elif e["kind"] == "gig_dropped":
            for oid in gig_orders.get(e["gigId"], []):
                gig_line(oid, e["at"], "dropped", e["gigId"])
        elif e["kind"] == "gig_expired":
            for oid in gig_orders.get(e["gigId"], []):
                gig_line(oid, e["at"], "expired", e["gigId"])
    for oid in gig_history:
        gig_history[oid].sort(key=lambda x: x["at"])
    out = {}
    matches = 0
    timeline = [(e["at"], 0, i, e) for i, e in enumerate(events)]
    timeline += [(line["at"], 1, i, line) for i, line in enumerate(journal)]
    timeline.sort(key=lambda row: row[:3])
    for at, kind, _, item in timeline:
        desk.now = at
        if kind == 0:
            apply_event(desk, parts, item)
        else:
            action, result = item["action"], item["result"]
            if action["type"] == "quote":
                request = requests.get(action["requestId"])
                if request is not None:
                    row, match = capture(desk, parts, request, action, orders, money,
                                         won_at, lost_at, cancelled, booked_at, booked_fee,
                                         booked_by, views_before, picked, delivered, gig_of,
                                         gig_posts, gig_history, late_orders)
                    out[request["id"]] = row
                    matches += match
                intake = parts.intake
                if hasattr(intake, "pending"):
                    intake.pending = {k: v for k, v in intake.pending.items() if v > at}
                    if request is not None and action["prices"] != decline(request):
                        intake.pending[request["id"]] = request["respondBy"]
            elif action["type"] == "post" and result.get("ok"):
                desk.posts[result["id"]] = action
                desk.schedules[result["id"]] = action["schedule"]
                for stop in action["stops"]:
                    desk.leg_gigs.setdefault(stop["orderId"], {})[stop["leg"]] = result["id"]
                members = sorted({s["orderId"] for s in action["stops"]})
                if len(members) == 1:
                    desk.clock[members[0]] = action["schedule"]
            elif action["type"] == "reprice" and result.get("ok"):
                desk.schedules[action["gigId"]] = action["schedule"]
            elif action["type"] == "withdraw" and result.get("ok"):
                desk.posts.pop(action["gigId"], None)
            for part in parts.all():
                part.result(action, result, desk)
    close = sum(1 for r in out.values() if r["replay"]["match"])
    (OUT / "decisions.json").write_text(json.dumps(out, separators=(",", ":")))
    settings = {
        "asPlayed": AS_PLAYED,
        "floors": [parts.fees.flat_floor, parts.fees.flat_short],
        "match": [close, len(out)],
        "model": AS_PLAYED["fee_model"],
    }
    (OUT / "settings.json").write_text(json.dumps(settings, separators=(",", ":")))
    print(f"decisions.json: {len(out)} requests; replayed prices match the sent quote "
          f"on {close} ({close / max(1, len(out)):.0%})")


def apply_event(desk: Desk, parts, e: dict) -> None:
    kind = e["kind"]
    if kind == "price_request":
        desk.requests[e["request"]["id"]] = e["request"]
    for part in parts.all():
        part.observe(e, desk, replay=True)
    if kind == "order_won" and e["order"]["id"] not in desk.orders:
        desk.orders[e["order"]["id"]] = e["order"]
    elif kind == "order_lost":
        desk.lost.add(e["requestId"])
    elif kind == "order_changed" and e["order"]["id"] in desk.orders:
        desk.orders[e["order"]["id"]] = e["order"]
    elif kind == "order_cancelled":
        desk.orders.pop(e["orderId"], None)
        desk.leg_gigs.pop(e["orderId"], None)
    elif kind == "gig_booked":
        desk.booked.add(e["gigId"])
        desk.booked_fee[e["gigId"]] = e["feeCents"]
    elif kind in ("gig_dropped", "no_show"):
        desk.booked.discard(e["gigId"])
    elif kind == "delivered":
        desk.delivered(e["orderId"], e["leg"], e["at"])
    elif kind == "deadline_close":
        desk.urgent.add(e["orderId"])


def capture(desk, parts, request: dict, action: dict, orders: dict, money: dict,
            won_at, lost_at, cancelled, booked_at, booked_fee, booked_by, views,
            picked, delivered, gig_of, gig_posts, gig_history, late_orders):
    quoter, intake, fees, notes = parts.quoter, parts.intake, parts.fees, parts.notes
    lists = {o["kind"]: o["listPriceCents"] for o in request["options"]}
    typical = request["referenceFeeCents"]
    facts = notes.facts(request)
    leg = request["legs"][0]
    drive = desk.ctx.minutes(leg["pickup"]["placeId"], leg["delivery"]["placeId"])
    km = desk.ctx.km(leg["pickup"]["placeId"], leg["delivery"]["placeId"])

    # what the parts would say now, at the recorded minute (the cost model's driver-supply
    # inputs are the world's own driver list, so they are exact)
    try:
        recomputed = quoter.prices(request, desk)
        admitted = intake.admit(request, dict(recomputed), desk)
    except Exception:
        recomputed, admitted = {}, {}
    try:
        expected = fees.expected(request, desk)
        risk = fees.late_risk(request, desk)
    except Exception:
        expected, risk = 0, 0.0
    factor = quoter.factor(request["dealerId"]) * quoter.region(request, desk)
    sent = action["prices"]
    chances = {k: quoter.chance(c / lists[k] / factor) for k, c in sent.items() if k in lists}
    from dispatch.intake import unbooked
    queue = unbooked(desk) + intake.pending_weight * len(intake.pending)
    limit = intake.morning_limit if intake.morning_limit and desk.now % 1440 < 720 else intake.limit
    slack = {}
    for o in request["options"]:
        start = max(desk.now, notes.earliest_pickup(request))
        slack[o["kind"]] = round((notes.latest_delivery(request, o["deadline"]) - start - drive) / 60, 1)
    tilt = (quoter.car_short if quoter.car_short and km < quoter.short_km else quoter.car) \
        if getattr(quoter, "car", 0) else 0
    # why the intake would decline, in the intake's own order: the slack filter,
    # private addresses, then the queue; None when the recording does not say
    reason = None
    declined = any(c > 4 * lists[k] for k, c in sent.items() if k in lists)
    if declined:
        passable = []
        for o in request["options"]:
            need = intake.same_day_slack if o["kind"] == "same_day" and intake.same_day_slack >= 0 else intake.slack
            if notes.latest_delivery(request, o["deadline"]) - start - drive >= need:
                passable.append(o["kind"])
        if not passable:
            reason = "no option had enough slack"
        elif not intake.private and any(l[s]["privateAddress"] for l in request["legs"] for s in ("pickup", "delivery")):
            reason = "a private address"
        else:
            from dispatch.intake import unbooked
            waiting = unbooked(desk) + getattr(intake, "pending_weight", 1.0) * len(intake.pending)
            limit = intake.morning_limit if intake.morning_limit and desk.now % 1440 < 12 * 60 else intake.limit
            reason = "the queue of orders without a driver was full" if waiting >= limit else None

    rid = request["id"]
    row = {
        "at": request["arrivedAt"],
        "km": round(km),
        "typical": typical,
        "noteFacts": None if not request["note"] else {
            "ready": facts.ready, "deadline": facts.deadline, "manual": facts.manual,
            "plates": facts.plates, "hours": list(facts.pickup_hours) if facts.pickup_hours else None,
            "deliveryHours": list(facts.delivery_hours) if facts.delivery_hours else None,
            "summerTyres": facts.summer_tyres, "sure": facts.sure},
        "declined": declined,
        "declineReason": reason,
        "slack": slack,
        "queue": [round(queue, 1), limit],
        "cost": [expected, round(expected / typical, 3) if typical else 0, round(risk, 3), tilt],
        "level": round(quoter.level, 3),
        "trust": round(quoter.counts.get(request["dealerId"], 0)),
        "chance": {k: round(v, 3) for k, v in chances.items()},
        "quote": sent,
        "replay": {"prices": {k: int(v) for k, v in admitted.items()} if admitted else None,
                   "match": bool(admitted) and all(
                       abs(admitted.get(k, 0) - sent.get(k, 0)) <= 1 for k in set(sent) | set(admitted))},
    }
    # the outcome and the money, all exact from the saved week
    if rid in won_at and rid not in cancelled:
        order = orders[rid]
        gid = gig_of.get(rid)
        post = gig_posts.get(gid)
        row["won"] = {
            "option": order["option"], "price": order["priceCents"], "deadline": order["deadline"],
            "late": rid in late_orders, "gigs": gig_history.get(rid, []),
            "gig": None if gid is None else {
                "posted": post["at"] if post else None,
                "schedule": post["schedule"] if post else [],
                "fee": booked_fee.get(gid), "by": booked_by.get(gid),
                "at": booked_at.get(gid), "views": views.get(gid, 0)},
            "pickedUp": [picked.get((rid, l)) for l in range(len(order["legs"]))],
            "delivered": [delivered.get((rid, l)) for l in range(len(order["legs"]))],
        }
        row["money"] = money.get(rid)
    elif rid in cancelled:
        row["cancelled"] = True
    else:
        row["lost"] = True
    return row, 1 if row["replay"]["match"] else 0


# --------------------------------------------------------------------------- race


def build_race() -> None:
    us_margin, us_orders = 1744275, 356  # our account and order count at the end
    frames, last = [], None
    with gzip.open(FEED, "rt") as fh:
        for line in fh:
            if not line.startswith("data: "):
                continue
            data = json.loads(line[6:])
            teams = {t["team"]: t for t in data.get("teams", [])}
            if len(teams) < 2:
                continue
            last = data
            frames.append(data)
    if not frames:
        return
    final = {t["team"]: t for t in last["teams"]}
    ours = [t for t in final.values()
            if t["marginCents"] == us_margin and t["wonOrders"] == us_orders]
    assert ours, "our team not found in the feed"
    us = ours[0]["team"]
    ranked = [t for t in final.values() if t.get("ranked")]
    top = max(ranked or final.values(), key=lambda t: t["marginCents"])["team"]
    series = []
    for i, data in enumerate(frames):
        if i % 8 and data is not frames[-1]:
            continue  # every ~16 s of the live feed
        teams = {t["team"]: t for t in data["teams"]}
        if us in teams and top in teams:
            a, b = teams[us], teams[top]
            series.append([data["now"], a["marginCents"], a["wonOrders"], b["marginCents"], b["wonOrders"]])
    out = {"series": series, "end": last["now"], "topEnd": final[top]["marginCents"],
           "usEnd": final[us]["marginCents"], "topOrders": final[top]["wonOrders"],
           "usOrders": final[us]["wonOrders"], "teams": len(final)}
    (OUT / "race.json").write_text(json.dumps(out, separators=(",", ":")))
    print(f"race.json: {len(series)} points, {len(final)} teams")


if __name__ == "__main__":
    main()
