"""How much of the within-day spread can the request's own features explain?

Target y = an option's switching ratio minus its world-and-day mean (first scanned
option per request, so each request counts once; switch_high == 0 rows skipped).
Features are everything known when the request arrives. Driver-proximity features
(drivers living within 30 km of the pickup/delivery) are skipped: the scan worlds'
rosters were not saved and no saved week shares a scan seed.

Leave-one-world-out (LOWO): fit on five scans, predict the sixth, pool the six.
Run: nix develop --command python tracks/t2/predict.py
"""
import json
import math
from collections import defaultdict
from pathlib import Path

import numpy as np

TRACK = Path(__file__).resolve().parent
DEALERS = ["D01", "D02", "D03", "D04", "D05", "D06"]
LANGS = ["fi", "en", "sv"]
KINDS = ["same_day", "next_day", "within_3_days"]


def load():
    """One row per request: the first scanned option, with the request's features."""
    roads = {(r["from"], r["to"]): r for r in json.load((TRACK / "map.json").open())["roads"]}
    rows = []
    for s in range(1, 7):
        seen = set()
        for line in (TRACK / f"scan-t2-scan-{s}-l8.jsonl").open():
            r = json.loads(line)
            if r["switch_high"] == 0 or r["request"]["id"] in seen:
                continue
            seen.add(r["request"]["id"])
            rows.append(row(r, roads))
    return rows
def row(r, roads):
    req, opt = r["request"], None
    for o in req["options"]:
        if o["kind"] == r["option"]:
            opt = o
    leg = req["legs"][0]
    note = req.get("note") or {}
    road = roads[(leg["pickup"]["placeId"], leg["delivery"]["placeId"])]
    return {
        "world": r["seed"], "ratio": (r["switch_low"] + r["switch_high"]) / 2,
        "day": r["arrival"] // 1440,
        "fee_ratio": req["referenceFeeCents"] / opt["listPriceCents"],
        "log_list": math.log(opt["listPriceCents"]),
        "log_fee": math.log(req["referenceFeeCents"]),
        "km": road["km"], "minutes": road["minutes"],
        "private_pickup": 1 if leg["pickup"]["privateAddress"] else 0,
        "private_delivery": 1 if leg["delivery"]["privateAddress"] else 0,
        "premium": 1 if leg["car"]["premium"] else 0,
        "electric": 1 if leg["car"]["electric"] else 0,
        "charge_low": 1 if (leg["car"]["chargePercent"] or 100) < 30 else 0,
        "kind": r["option"], "n_options": len(req["options"]),
        "lead_h": (leg["pickup"]["window"]["from"] - req["arrivedAt"]) / 60.0,
        "deadline_h": (opt["deadline"] - req["arrivedAt"]) / 60.0,
        "arrival_hour": (req["arrivedAt"] % 1440) / 60.0,
        "dealer": req["dealerId"], "has_note": 1 if note else 0,
        "lang": note.get("language", "none"),
        "n_legs": len(req["legs"]),
        "batch": 1 if req.get("batchId") else 0,
        "pickup": leg["pickup"]["placeId"], "delivery": leg["delivery"]["placeId"],
    }


NUMERIC = ["fee_ratio", "log_list", "log_fee", "km", "minutes", "private_pickup", "private_delivery",
           "premium", "electric", "charge_low", "n_options", "lead_h", "deadline_h", "arrival_hour",
           "has_note", "n_legs", "batch"]
CATEGORIES = {"kind": KINDS, "dealer": DEALERS + ["other"], "lang": LANGS}


def features(rows, towns, pickups):
    """The design matrix: numeric columns plus one-hot categories and towns."""
    cols, names = [], []
    for f in NUMERIC:
        cols.append([r[f] for r in rows])
        names.append(f)
    for f, groups in CATEGORIES.items():
        for g in groups:
            cols.append([1 if (r[f] if f != "dealer" else big(r[f])) == g else 0 for r in rows])
            names.append(f"{f}:{g}")
    for t in towns:
        cols.append([1 if r["delivery"] == t else 0 for r in rows])
        names.append(f"delivery:{t}")
    for t in pickups:
        cols.append([1 if r["pickup"] == t else 0 for r in rows])
        names.append(f"pickup:{t}")
    return np.array(cols, dtype=float).T, names


def big(dealer):
    return dealer if dealer in DEALERS else "other"


def target(rows):
    """y = ratio minus its world-and-day mean."""
    means = defaultdict(list)
    for r in rows:
        means[(r["world"], r["day"])].append(r["ratio"])
    means = {k: sum(v) / len(v) for k, v in means.items()}
    return np.array([r["ratio"] - means[(r["world"], r["day"])] for r in rows])


def lowo_single(rows, y):
    """Each feature alone: LOWO R squared. Numeric: a line. Category: group means."""
    worlds = sorted({r["world"] for r in rows})
    out = []
    for f in NUMERIC:
        x = np.array([r[f] for r in rows])
        out.append((f, single_numeric(rows, y, x, worlds), "line"))
    for f, groups in CATEGORIES.items():
        out.append((f, single_group(rows, y, [r[f] if f != "dealer" else big(r[f]) for r in rows], worlds), "group means"))
    for f, key in (("delivery", "delivery"), ("pickup", "pickup")):
        out.append((f, single_group(rows, y, [r[key] for r in rows], worlds), "group means"))
    return sorted(out, key=lambda t: -t[1])


def single_numeric(rows, y, x, worlds):
    pred = np.zeros(len(rows))
    for w in worlds:
        test = np.array([r["world"] == w for r in rows])
        xt, yt = x[~test], y[~test]
        b = np.polyfit(xt, yt, 1)
        pred[test] = np.polyval(b, x[test])
    return r2(y, pred)


def single_group(rows, y, keys, worlds):
    pred = np.zeros(len(rows))
    for w in worlds:
        test = np.array([r["world"] == w for r in rows])
        overall = y[~test].mean()
        means = defaultdict(list)
        for k, yy, rr in zip(keys, y, rows):
            if rr["world"] != w:
                means[k].append(yy)
        means = {k: sum(v) / len(v) for k, v in means.items()}
        pred[test] = [means.get(k, overall) for k, rr in zip(keys, rows) if rr["world"] == w]
    return r2(y, pred)


def ridge(X, y, lam):
    """Standardised features, unpenalised intercept; returns a predictor."""
    mu, sd = X.mean(0), X.std(0)
    sd[sd == 0] = 1.0
    Z = (X - mu) / sd
    A = np.hstack([np.ones((len(Z), 1)), Z])
    P = np.eye(A.shape[1]) * lam
    P[0, 0] = 0.0
    beta = np.linalg.solve(A.T @ A + P, A.T @ y)
    return lambda Xq: np.hstack([np.ones((len(Xq), 1)), (Xq - mu) / sd]) @ beta, beta, mu, sd


def r2(y, pred):
    return 1 - ((y - pred) ** 2).sum() / ((y - y.mean()) ** 2).sum()


def lowo(X, y, rows, lam):
    worlds = sorted({r["world"] for r in rows})
    pred = np.zeros(len(rows))
    for w in worlds:
        test = np.array([r["world"] == w for r in rows])
        fn = ridge(X[~test], y[~test], lam)[0]
        pred[test] = fn(X[test])
    return r2(y, pred)


def main():
    rows = load()
    y = target(rows)
    counts = defaultdict(int)
    for r in rows:
        counts[r["delivery"]] += 1
    pcounts = defaultdict(int)
    for r in rows:
        pcounts[r["pickup"]] += 1
    towns = sorted(t for t, n in counts.items() if n >= 100)
    pickups = sorted(t for t, n in pcounts.items() if n >= 100)
    print(f"{len(rows)} requests, {len(towns)} delivery towns with n>=100, {len(pickups)} pickup towns")
    print(f"y stdev {y.std():.4f}\n")

    print("## 1. Single features, leave-one-world-out R squared")
    print("| feature | LOWO R2 | fit |")
    print("|---|---:|---|")
    for f, val, how in lowo_single(rows, y):
        print(f"| {f} | {val:+.4f} | {how} |")

    X, names = features(rows, towns, pickups)
    print(f"\nfull model: {X.shape[1]} columns")
    print("\n## 2. Ridge, leave-one-world-out")
    print("| model | penalty | LOWO R2 | in-sample R2 |")
    print("|---|---:|---:|---:|")
    best = (-1, None)
    for lam in (1, 10, 100):
        lo = lowo(X, y, rows, lam)
        ins = r2(y, ridge(X, y, lam)[0](X))
        print(f"| full ({X.shape[1]} cols) | {lam} | {lo:+.4f} | {ins:+.4f} |")
        if lo > best[0]:
            best = (lo, lam)
    print(f"| full best | {best[1]} | {best[0]:+.4f} |")

    # the small model: the 6-8 best single features
    singles = lowo_single(rows, y)
    chosen = [f for f, _, _ in singles[:8]]
    small_numeric = [f for f in chosen if f in NUMERIC]
    small_cats = [f for f in chosen if f in CATEGORIES or f in ("delivery", "pickup")]
    cols, snames = [], []
    for f in small_numeric:
        cols.append([r[f] for r in rows])
        snames.append(f)
    for f in small_cats:
        if f in CATEGORIES:
            for g in CATEGORIES[f]:
                key = (lambda d: big(d)) if f == "dealer" else (lambda v: v)
                cols.append([1 if key(r[f]) == g else 0 for r in rows])
                snames.append(f"{f}:{g}")
        elif f == "delivery":
            for t in towns:
                cols.append([1 if r["delivery"] == t else 0 for r in rows])
                snames.append(f"delivery:{t}")
        elif f == "pickup":
            for t in pickups:
                cols.append([1 if r["pickup"] == t else 0 for r in rows])
                snames.append(f"pickup:{t}")
    Xs = np.array(cols, dtype=float).T
    print(f"\nsmall model features: {chosen} -> {Xs.shape[1]} columns")
    print("| model | penalty | LOWO R2 | in-sample R2 |")
    print("|---|---:|---:|---:|")
    sbest = (-1, None)
    for lam in (1, 10, 100):
        lo = lowo(Xs, y, rows, lam)
        ins = r2(y, ridge(Xs, y, lam)[0](Xs))
        print(f"| small ({Xs.shape[1]} cols) | {lam} | {lo:+.4f} | {ins:+.4f} |")
        if lo > sbest[0]:
            sbest = (lo, lam)
    print(f"| small best | {sbest[1]} | {sbest[0]:+.4f} |")

    print("\n## 3. Small model coefficients (plain units), penalty", sbest[1])
    fn, beta, mu, sd = ridge(Xs, y, sbest[1])
    print("| feature | coefficient (ratio per unit) |")
    print("|---|---:|")
    for i, name in enumerate(snames):
        print(f"| {name} | {beta[i + 1] / sd[i]:+.5f} |")
    print(f"| intercept | {beta[0] - sum(beta[i + 1] / sd[i] * mu[i] for i in range(len(snames))):+.5f} |")
    pred = fn(Xs)
    print(f"\nprediction stdev {pred.std():.4f}, mean {pred.mean():+.5f}; y stdev {y.std():.4f}")

    # step 3a: dealer leftovers, raw and after a small model fitted WITHOUT dealer columns
    keep = [i for i, n in enumerate(snames) if not n.startswith("dealer:")]
    fn2 = ridge(Xs[:, keep], y, sbest[1])[0]
    resid2 = y - fn2(Xs[:, keep])
    print("\n## Dealer leftovers in the scans (no trust)")
    print("| dealer | n | mean y | mean residual (model without dealer) |")
    print("|---|---:|---:|---:|")
    for d in DEALERS + ["other"]:
        m = np.array([big(r["dealer"]) == d for r in rows])
        if m.sum():
            se = resid2[m].std() / math.sqrt(m.sum())
            print(f"| {d} | {m.sum()} | {y[m].mean():+.4f} | {resid2[m].mean():+.4f} (se {se:.4f}) |")


if __name__ == "__main__":
    main()
