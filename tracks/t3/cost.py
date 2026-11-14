"""What a won order costs, by what was known when the request arrived. Run with nix develop.

    python tracks/t3/cost.py t3s5-fit          # the tables of mean fee ratio (y1) and late share (y2)
    python tracks/t3/cost.py t3s5-fit t3s5-base   # tables, then the fit on the first label and the
                                              # out-of-sample check on the second
"""
from __future__ import annotations

import collections
import gzip
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import numpy as np

from harness import config
from harness.play import read_index

HOUR, DAY = 60, 1440
COST_KINDS = ("driver_fee", "waiting", "failed_visit", "release_fee")  # negative cents in the ledger
LATE_KINDS = ("late_refund", "undelivered_penalty")


def load(label: str) -> list[dict]:
    """One row per order won and not cancelled in the label's level-8 weeks."""
    rows = []
    for run in read_index():
        if run["label"] != label or run["level"] != 8 or run.get("board"):
            continue
        folder = os.path.join(config.RUNS, os.path.basename(run["folder"]))
        with gzip.open(os.path.join(folder, "roster.json.gz"), "rt") as file:
            roster = json.load(file)
        homes = collections.Counter(driver["homePlaceId"] for driver in roster)
        world_map = json.load(open(os.path.join(config.DATA, "map.json"), encoding="utf-8"))
        places = {place["id"]: place for place in world_map["places"]}
        roads = {(road["from"], road["to"]): road for road in world_map["roads"]}

        def straight(a: str, b: str) -> float:
            p, q = places[a], places[b]
            lat1, lat2, dlon = np.radians(p["lat"]), np.radians(q["lat"]), np.radians(q["lon"] - p["lon"])
            return 2 * 6371 * np.arcsin(np.sqrt(np.sin((lat2 - lat1) / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2))

        near = {town: sum(count for home, count in homes.items() if straight(town, home) <= 30) for town in places}
        with gzip.open(os.path.join(folder, "reveal.json.gz"), "rt") as file:
            reveal = json.load(file)
        requests = {item["request"]["id"]: item["request"] for item in reveal["requests"]}
        snapshot = json.load(gzip.open(os.path.join(folder, "snapshot.json.gz"), "rt", encoding="utf-8"))
        gig_orders = {gig["id"]: sorted({stop["orderId"] for stop in gig["stops"]}) for gig in snapshot["gigs"]}
        money: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
        with gzip.open(os.path.join(folder, "events.jsonl.gz"), "rt") as file:
            for text in file:
                event = json.loads(text)
                if event["kind"] != "ledger":
                    continue
                line = event["line"]
                owners = [line["orderId"]] if line["orderId"] else gig_orders.get(line["gigId"] or "", [])
                for owner in owners:
                    money[owner][line["kind"]] -= line["cents"] / len(owners)  # fees are negative: store positive
        for order in snapshot["orders"]:
            if order["status"] == "cancelled" or order["id"] not in requests:
                continue
            request, leg, lines = requests[order["id"]], order["legs"][0], money[order["id"]]
            option = next((o for o in request["options"] if o["kind"] == order["option"]), None)
            if option is None:
                continue
            road = roads[(leg["pickup"]["placeId"], leg["delivery"]["placeId"])]
            arrive, window_from = request["arrivedAt"], leg["pickup"]["window"]["from"]
            rows.append({
                "seed": run["seed"],
                "y1": sum(lines[kind] for kind in COST_KINDS) / request["referenceFeeCents"],
                "y2": float(any(lines[kind] for kind in LATE_KINDS)),
                "lead": max(0, window_from - arrive) / HOUR,           # hours until the pickup window opens
                "hour": arrive % DAY / HOUR,                            # hour of the day of arrival
                "kind": order["option"],
                "private": any(l[side]["privateAddress"] for l in order["legs"] for side in ("pickup", "delivery")),
                "km": road["km"],
                "minutes": road["minutes"],
                "near_pickup": near[leg["pickup"]["placeId"]],
                "near_delivery": near[leg["delivery"]["placeId"]],
                "slack": (option["deadline"] - max(arrive, window_from) - road["minutes"]) / HOUR,
            })
    return rows


def band(value: float, edges: list[float]) -> str:
    return next((f"<{edge}" for edge in edges if value < edge), f">={edges[-1]}")


def show(title: str, rows: list[dict], key) -> None:
    groups: dict = collections.defaultdict(list)
    for row in rows:
        groups[key(row)].append(row)
    print(f"\n{title}\n{'':16} {'n':>5} {'mean y1':>8} {'mean y2':>8}")
    for name in sorted(groups):
        g = groups[name]
        print(f"{str(name):16} {len(g):>5} {sum(r['y1'] for r in g) / len(g):>8.3f} {sum(r['y2'] for r in g) / len(g):>8.3f}")


def tables(rows: list[dict]) -> None:
    print(f"{len(rows)} orders; mean y1 {sum(r['y1'] for r in rows) / len(rows):.3f}, mean y2 {sum(r['y2'] for r in rows) / len(rows):.3f}")
    lead_band = lambda r: "0" if r["lead"] <= 0 else band(r["lead"], [3, 12, 24])
    hour_band = lambda r: "<12" if r["hour"] < 12 else ("12-15" if r["hour"] < 15 else "15+")
    show("lead x arrival hour", rows, lambda r: (lead_band(r), hour_band(r)))
    show("option kind", rows, lambda r: r["kind"])
    show("private address", rows, lambda r: r["private"])
    show("lane km", rows, lambda r: band(r["km"], [50, 150, 300, 500]))
    show("drivers within 30 km of pickup", rows, lambda r: band(r["near_pickup"], [10, 30, 80]))
    show("drivers within 30 km of delivery", rows, lambda r: band(r["near_delivery"], [10, 30, 80]))
    show("slack hours", rows, lambda r: band(r["slack"], [6, 12, 24]))
    show("arrival hour", rows, hour_band)
    show("lead hours", rows, lead_band)


# The models: yes/no features known when the request arrives, no option-dependent ones
# (`prices` asks for the fee once per request). Each is (name, predicate).
FEATURES = [  # the reference order: window opens 12-24h away, arrives before noon, no private address, lane under 500 km, 30+ drivers near each end
    ("lead<=3", lambda r: r["lead"] <= 3),
    ("lead3-12", lambda r: 3 < r["lead"] <= 12),
    ("lead>=24", lambda r: r["lead"] >= 24),
    ("hour>=15", lambda r: r["hour"] >= 15),
    ("hour12-15", lambda r: 12 <= r["hour"] < 15),
    ("private", lambda r: r["private"]),
    ("km>=500", lambda r: r["km"] >= 500),
    ("pickup<30", lambda r: r["near_pickup"] < 30),
    ("delivery<10", lambda r: r["near_delivery"] < 10),
]


def design(rows: list[dict]) -> np.ndarray:
    return np.array([[1.0] + [float(pred(r)) for _, pred in FEATURES] for r in rows])


def fit(train: list[dict], test: list[dict]) -> None:
    x = design(train)
    counts = x.sum(axis=0)
    keep = [i for i in range(1, len(FEATURES) + 1) if counts[i] >= 60]
    print(f"train {len(train)} orders; feature counts: " + ", ".join(f"{name}={int(counts[i + 1])}" for i, (name, _) in enumerate(FEATURES)))
    print("dropped for under 60 orders: " + ", ".join(name for i, (name, _) in enumerate(FEATURES) if i + 1 not in keep))
    used = [0] + keep
    fee_coef = np.linalg.lstsq(x[:, used], np.array([r["y1"] for r in train]), rcond=None)[0]
    late_coef = np.linalg.lstsq(x[:, used], np.array([r["y2"] for r in train]), rcond=None)[0]
    kept = [(name, k + 1) for k, (name, _) in enumerate(FEATURES) if k + 1 in keep]
    print("\nexpected2: base " + f"{fee_coef[0]:.4f}" + " + " + ", ".join(f"{name} {fee_coef[i]:+.4f}" for name, i in kept))
    print("late_risk2: base " + f"{late_coef[0]:.4f}" + " + " + ", ".join(f"{name} {late_coef[i]:+.4f}" for name, i in kept))

    # out of sample: the old model against the new, on the test label's weeks
    xt = design(test)[:, used]
    pred_fee = xt @ fee_coef
    pred_late = np.clip(xt @ late_coef, 0.0, 1.0)
    actual_fee = np.array([r["y1"] for r in test])
    actual_late = np.array([r["y2"] for r in test])
    old_fee = np.array([0.966 + 0.076 * (r["near_pickup"] < 30) + 0.090 * (r["near_delivery"] < 10) + 0.213 * (r["km"] >= 500)
                        + 0.331 * r["private"] for r in test])
    old_late = np.clip(np.array([-0.0017 + 0.0269 * (r["near_pickup"] < 30) - 0.0130 * (r["near_delivery"] < 10)
                                 + 0.0855 * (r["km"] >= 500) + 0.1676 * r["private"] for r in test]), 0.0, 1.0)
    print(f"\nout of sample, {len(test)} orders: fee MAE old {np.mean(abs(old_fee - actual_fee)):.4f}, new {np.mean(abs(pred_fee - actual_fee)):.4f} (of typical)")
    print(f"totals of y1: actual {actual_fee.sum():.1f}, old {old_fee.sum():.1f}, new {pred_fee.sum():.1f}")
    print("\npredicted-risk bands: actual late share in each (n)")
    print(f"{'band':10} {'old n':>6} {'old late':>9} {'new n':>6} {'new late':>9}")
    edges = [0.02, 0.05, 0.10]
    for name, lo, hi in [("under 2%", 0, 0.02), ("2-5%", 0.02, 0.05), ("5-10%", 0.05, 0.10), ("over 10%", 0.10, 1.01)]:
        om = (old_late >= lo) & (old_late < hi)
        nm = (pred_late >= lo) & (pred_late < hi)
        print(f"{name:10} {om.sum():>6} {actual_late[om].mean() if om.any() else float('nan'):>9.3f} {nm.sum():>6} {actual_late[nm].mean() if nm.any() else float('nan'):>9.3f}")
    print(f"overall late share {actual_late.mean():.3f}")


def main() -> None:
    labels = sys.argv[1:]
    if not labels:
        raise SystemExit("name one or two labels: cost.py <fit label> [<test label>]")
    rows = load(labels[0])
    tables(rows)
    if len(labels) > 1:
        fit(rows, load(labels[1]))


if __name__ == "__main__":
    main()
