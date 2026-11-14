"""One row per won order from the saved weeks: the features the desk knew at quote time, and what the order cost.

    python3 tracks/ml/rows.py                 # every saved level 8 week; writes data/ml/rows.csv.gz
    python3 tracks/ml/rows.py --jobs 16

Each week is replayed through a desk that only keeps the books (no decisions): the events and the
desk's own actions in the order they happened. At each won request's arrival, `dispatch.features`
reads the desk as it was then. The targets are those of tracks/t3/cost.py (fee model 2's fit):

    fee     the order's driver fees, waiting, failed visits and release fees, over its typical fee
            (a gig's fees are split equally between the orders it carried)
    late    1 when the order paid a late refund or an undelivered penalty
    refund  those refunds and penalties, over the order's price

Fee models 1 and 2 are evaluated on the same request at the same moment, for the baselines.
Rows of each week are cached under data/ml/weeks/, so a rerun reads only new weeks. Standard library only.
"""
from __future__ import annotations

import argparse
import collections
import csv
import gzip
import json
import os
import statistics
import sys
from multiprocessing import Pool

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
if "SPREAD_HOME" not in os.environ and not os.path.exists("/home/agent/.t3/projects/bahn"):
    os.environ["SPREAD_HOME"] = ROOT  # a checkout without the shared folder reads its own data/

from dispatch.bundles import orders_in  # noqa: E402
from dispatch.context import Context  # noqa: E402
from dispatch.desk import Desk  # noqa: E402
from dispatch.features import NAMES, features  # noqa: E402
from dispatch.fees import MeasuredFees  # noqa: E402
from dispatch.policies.main import build  # noqa: E402
from harness import config  # noqa: E402

COST_KINDS = ("driver_fee", "waiting", "failed_visit", "release_fee")
LATE_KINDS = ("late_refund", "undelivered_penalty")
META = ("week", "seed", "label", "version", "option", "price", "list", "typical", "fee", "late", "refund", "m1_fee", "m1_late", "m2_fee", "m2_late")
OUT = os.path.join(config.DATA, "ml")
_MAP = None


def world_map() -> dict:
    global _MAP
    if _MAP is None:
        for path in (os.path.join(config.DATA, "map.json"), os.path.join(ROOT, "tracks", "t2", "map.json")):
            if os.path.exists(path):
                _MAP = json.load(open(path, encoding="utf-8"))
                break
    return _MAP


def read_lines(path: str) -> list[dict]:
    with gzip.open(path, "rt", encoding="utf-8") as file:
        return [json.loads(line) for line in file]


def read_json(path: str):
    with gzip.open(path, "rt", encoding="utf-8") as file:
        return json.load(file)


def first_schedules(actions: list[dict], typical: dict[str, float]) -> tuple[dict[str, tuple[float, float]], tuple[float, float]]:
    """Each order's first posted fee schedule, opening and cap as multiples of the typical fee of the cars it carries;
    and the week's median of those for gigs of one car, for the cars whose first gig was a bundle."""
    first: dict[str, tuple[float, float]] = {}
    alone: list[tuple[float, float]] = []
    for line in actions:
        action = line["action"]
        if action["type"] != "post" or not line["result"].get("ok") or not action["schedule"]:
            continue
        members = orders_in(action["stops"])
        cars = sum(1 for stop in action["stops"] if stop["kind"] == "pickup")
        base = sum(typical.get(member, 0) for member in members) * cars / max(1, len(members))
        if base <= 0:
            continue
        fees = [step["feeCents"] for step in action["schedule"]]
        value = (fees[0] / base, max(fees) / base)
        if len(members) == 1 and members[0] not in first:
            alone.append(value)
        for member in members:
            first.setdefault(member, value if len(members) == 1 else None)
    median = (statistics.median(v[0] for v in alone), statistics.median(v[1] for v in alone)) if alone else (1.0, 1.5)
    return {k: v or median for k, v in first.items()}, median


def week_rows(folder: str) -> list[list]:
    """The rows of one saved week."""
    result = json.load(open(os.path.join(folder, "result.json"), encoding="utf-8"))
    events = read_lines(os.path.join(folder, "events.jsonl.gz"))
    actions = read_lines(os.path.join(folder, "actions.jsonl.gz"))
    roster = read_json(os.path.join(folder, "roster.json.gz"))
    snapshot = read_json(os.path.join(folder, "snapshot.json.gz"))
    ctx = Context.build(8, world_map(), roster)
    bundled = any(len(orders_in(line["action"]["stops"])) > 1 for line in actions if line["action"]["type"] == "post")
    desk = Desk(None, ctx, build(ctx, bundle=3 if bundled else 1), 0)
    model1, model2 = MeasuredFees(model=1), MeasuredFees(model=2)

    requests = {e["request"]["id"]: e["request"] for e in events if e["kind"] == "price_request"}
    won = {e["order"]["id"] for e in events if e["kind"] == "order_won"}
    typical = {rid: requests[rid]["referenceFeeCents"] / len(requests[rid]["legs"]) for rid in won if rid in requests}
    schedules, _ = first_schedules(actions, typical)

    # the money of each order, from the ledger
    gig_orders = {gig["id"]: orders_in(gig["stops"]) for gig in snapshot["gigs"]}
    money: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
    for event in events:
        if event["kind"] == "ledger":
            line = event["line"]
            owners = [line["orderId"]] if line["orderId"] else gig_orders.get(line["gigId"] or "", [])
            for owner in owners:
                money[owner][line["kind"]] -= line["cents"] / len(owners)
    final = {order["id"]: order for order in snapshot["orders"]}

    seen: dict[str, list[float]] = {}
    baselines: dict[str, tuple[float, float, float, float]] = {}
    timeline = sorted([(e["at"], 0, i, e) for i, e in enumerate(events)] + [(a["at"], 1, i, a) for i, a in enumerate(actions)], key=lambda x: x[:3])
    for minute, kind, _, item in timeline:
        desk.now = minute
        if kind == 1:
            action, answer = item["action"], item["result"]
            if answer.get("ok") is not True:
                continue
            if action["type"] == "post":
                desk.carry(action, answer["id"])
            elif action["type"] == "withdraw":
                unlink(desk, action["gigId"])
            continue
        what = item["kind"]
        if what == "price_request":
            request = item["request"]
            desk.requests[request["id"]] = request
            if request["id"] in won:
                seen[request["id"]] = features(request, desk, schedules.get(request["id"]))
                ref = request["referenceFeeCents"]
                baselines[request["id"]] = (model1.expected(request, desk) / ref, model1.late_risk(request, desk),
                                            model2.expected(request, desk) / ref, model2.late_risk(request, desk))
        elif what in ("order_won", "order_changed"):
            if what == "order_won" or item["order"]["id"] in desk.orders:
                desk.orders[item["order"]["id"]] = item["order"]
        elif what == "order_cancelled":
            desk.orders.pop(item["orderId"], None)
            desk.leg_gigs.pop(item["orderId"], None)
        elif what == "gig_booked":
            desk.booked.add(item["gigId"])
        elif what in ("gig_dropped", "no_show"):
            desk.booked.discard(item["gigId"])
        elif what == "delivered":
            desk.delivered(item["orderId"], item["leg"], item["at"])
        elif what == "deadline_close":
            desk.urgent.add(item["orderId"])
        elif what == "gig_expired":
            unlink(desk, item["gigId"])
        elif what == "visit_failed":
            desk.leg_gigs.get(item["orderId"], {}).pop(item["leg"], None)

    name = os.path.basename(folder)
    rows = []
    for rid, x in seen.items():
        order = final.get(rid)
        if order is None or order["status"] == "cancelled":
            continue
        lines, request = money[rid], requests[rid]
        fee = sum(lines[k] for k in COST_KINDS) / request["referenceFeeCents"]
        late = float(any(lines[k] for k in LATE_KINDS))
        refund = sum(lines[k] for k in LATE_KINDS) / max(1, order["priceCents"])
        rows.append([name, result["seed"], result["label"], result.get("version", ""), order["option"], order["priceCents"],
                     next((o["listPriceCents"] for o in request["options"] if o["kind"] == order["option"]), request["options"][0]["listPriceCents"]),
                     request["referenceFeeCents"], round(fee, 5), late, round(refund, 5), *(round(b, 5) for b in baselines[rid])]
                    + [round(v, 4) for v in x])
    return rows


def unlink(desk: Desk, gig_id: str) -> None:
    """A gig left the app: the legs it carried have no gig until the desk posts them again."""
    for order_id, legs in list(desk.leg_gigs.items()):
        for leg, gig in list(legs.items()):
            if gig == gig_id:
                legs.pop(leg)


def cached(folder: str) -> list[list]:
    path = os.path.join(OUT, "weeks", os.path.basename(folder) + ".json.gz")
    if os.path.exists(path):
        return read_json(path)
    try:
        rows = week_rows(folder)
    except Exception as error:  # a week whose files are incomplete or from an old format
        print(f"skip {os.path.basename(folder)}: {type(error).__name__}: {error}", file=sys.stderr)
        rows = []
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with gzip.open(path + ".tmp", "wt", encoding="utf-8") as file:
        json.dump(rows, file)
    os.replace(path + ".tmp", path)
    return rows


def weeks() -> list[str]:
    """The saved level 8 practice weeks with every file the replay needs."""
    out = []
    for name in sorted(os.listdir(config.RUNS)):
        folder = os.path.join(config.RUNS, name)
        if not all(os.path.exists(os.path.join(folder, f)) for f in ("result.json", "events.jsonl.gz", "actions.jsonl.gz", "roster.json.gz", "snapshot.json.gz")):
            continue
        try:
            result = json.load(open(os.path.join(folder, "result.json"), encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if result.get("level") == 8 and not result.get("board"):
            out.append(folder)
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--jobs", type=int, default=max(1, (os.cpu_count() or 2) - 2))
    parser.add_argument("--limit", type=int, default=0, help="only the first N weeks (a smoke run)")
    args = parser.parse_args()
    folders = weeks()[: args.limit or None]
    print(f"{len(folders)} weeks", file=sys.stderr)
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, "rows.csv.gz")
    count = 0
    with gzip.open(path + ".tmp", "wt", encoding="utf-8", newline="") as file, Pool(args.jobs) as pool:
        writer = csv.writer(file)
        writer.writerow(META + NAMES)
        for i, rows in enumerate(pool.imap_unordered(cached, folders, chunksize=4)):
            writer.writerows(rows)
            count += len(rows)
            if (i + 1) % 200 == 0:
                print(f"{i + 1} weeks, {count} rows", file=sys.stderr)
    os.replace(path + ".tmp", path)
    print(f"{count} rows from {len(folders)} weeks -> {path}", file=sys.stderr)


if __name__ == "__main__":
    main()
