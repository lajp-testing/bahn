"""Trains the learned cost model (fee model 3) on the rows of tracks/ml/rows.py, compares it with fee models 1
and 2 on the holdout worlds, and writes it out as plain Python (dispatch/learned.py). Run with nix develop:

    nix develop --command python tracks/ml/train.py              # train, report, export
    nix develop --command python tracks/ml/train.py --no-export  # report only

Split by world, never by row: the holdout seeds (hold-01..10) are never trained on; the number of trees is
chosen on a few training worlds held back for that (every seventh training seed). Then the model is refit on
all training worlds with that number of trees.
"""
from __future__ import annotations

import argparse
import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
if "SPREAD_HOME" not in os.environ and not os.path.exists("/home/agent/.t3/projects/bahn"):
    os.environ["SPREAD_HOME"] = ROOT

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor  # noqa: E402

from dispatch.features import NAMES  # noqa: E402
from harness import config  # noqa: E402

STATE = ("unbooked", "open_gigs", "held", "booked_near", "fits", "bundles_on")
TARGETS = {  # target -> (kind, loss)
    "fee": ("regressor", "poisson"),
    "late": ("classifier", "log_loss"),
    "refund": ("regressor", "poisson"),
}
PARAMS = dict(learning_rate=0.05, max_depth=5, max_leaf_nodes=24, min_samples_leaf=400, l2_regularization=1.0)
MAX_TREES = 500


def load(path: str) -> pd.DataFrame:
    frame = pd.read_csv(path, dtype={name: np.float32 for name in NAMES})
    frame["holdout"] = frame["seed"].str.startswith("hold-")
    return frame


def model(kind: str, loss: str, trees: int):
    cls = HistGradientBoostingRegressor if kind == "regressor" else HistGradientBoostingClassifier
    return cls(loss=loss, max_iter=trees, early_stopping=False, random_state=0, **PARAMS)


def predict(est, x) -> np.ndarray:
    return est.predict_proba(x)[:, 1] if hasattr(est, "predict_proba") else est.predict(x)


def staged(est, x):
    return (s[:, 1] for s in est.staged_predict_proba(x)) if hasattr(est, "staged_predict_proba") else est.staged_predict(x)


def loss_of(target: str, y: np.ndarray, p: np.ndarray) -> float:
    if target == "late":
        return logloss(y, p)
    p = np.maximum(p, 1e-6)
    return float(np.mean(2 * (y * np.log(np.maximum(y, 1e-12) / p) - (y - p))))  # Poisson deviance


def logloss(y: np.ndarray, p: np.ndarray) -> float:
    p = np.clip(p, 1e-4, 1 - 1e-4)
    return float(-np.mean(y * np.log(p) + (1 - y) * np.log(1 - p)))


def fit(train: pd.DataFrame, target: str, names: tuple[str, ...]):
    """The number of trees from the held-back training worlds, then the refit on every training world."""
    kind, loss = TARGETS[target]
    seeds = sorted(train["seed"].unique())
    back = set(seeds[3::7])
    inner, val = train[~train["seed"].isin(back)], train[train["seed"].isin(back)]
    est = model(kind, loss, MAX_TREES).fit(inner[list(names)].to_numpy(), inner[target].to_numpy())
    curve = [loss_of(target, val[target].to_numpy(), p) for p in staged(est, val[list(names)].to_numpy())]
    trees = int(np.argmin(curve)) + 1
    print(f"  {target}: {trees} trees (validation worlds {len(back)}: loss {curve[trees - 1]:.5f}, at {MAX_TREES} {curve[-1]:.5f})")
    return model(kind, loss, trees).fit(train[list(names)].to_numpy(), train[target].to_numpy())


def report(test: pd.DataFrame, fee3: np.ndarray, late3: np.ndarray, extra: dict[str, tuple[np.ndarray, np.ndarray]], const: tuple[float, float]) -> None:
    fee, late = test["fee"].to_numpy(), test["late"].to_numpy()
    candidates = {"constant": (np.full(len(test), const[0]), np.full(len(test), const[1])),
                  "model 1": (test["m1_fee"].to_numpy(), test["m1_late"].to_numpy()),
                  "model 2": (test["m2_fee"].to_numpy(), test["m2_late"].to_numpy()),
                  "model 3": (fee3, late3)} | extra
    print(f"\nholdout: {len(test)} orders in {test['week'].nunique()} weeks of {test['seed'].nunique()} worlds; "
          f"mean fee {fee.mean():.3f} of typical, late share {late.mean():.3f}")
    print(f"{'':22} {'fee MAE':>8} {'fee bias':>9} {'late logloss':>13} {'late Brier':>11}")
    for name, (f, p) in candidates.items():
        print(f"{name:22} {np.mean(abs(f - fee)):8.4f} {np.mean(f - fee):+9.4f} {logloss(late, p):13.4f} {np.mean((p - late) ** 2):11.4f}")

    print("\nlate risk by decile of model 3's prediction: predicted / actual (model 2 by its own deciles)")
    for name in ("model 2", "model 3"):
        p = candidates[name][1]
        order = np.argsort(p, kind="stable")
        cells = [f"{p[part].mean():.3f}/{late[part].mean():.3f}" for part in np.array_split(order, 10)]
        print(f"  {name}: " + " ".join(cells))

    # The one that matters for quoting: rank by predicted cost per euro of list price.
    typical, listed = test["typical"].to_numpy(), test["list"].to_numpy()
    real = fee * typical / listed
    print("\ncheapest fifth by predicted fee per euro of list price: actual fee per list euro, late share")
    for name in ("model 1", "model 2", "model 3"):
        f, p = candidates[name]
        cheap = np.argsort(f * typical / listed, kind="stable")[: len(test) // 5]
        dear = np.argsort(-(f * typical / listed), kind="stable")[: len(test) // 5]
        print(f"  {name}: cheapest {real[cheap].mean():.4f}, late {late[cheap].mean():.3f}; dearest {real[dear].mean():.4f}, late {late[dear].mean():.3f}")
    print("\nby group (fee MAE model 2 -> 3; late logloss model 2 -> 3; n)")
    for title, mask in (("bundles on", test["bundles_on"] == 1), ("bundles off", test["bundles_on"] == 0),
                        ("fits an open gig", test["fits"] == 1), ("private address", (test["private_pickup"] + test["private_delivery"]) > 0),
                        ("same-day option", test["option"] == "same_day")):
        m = mask.to_numpy()
        if m.sum() < 50:
            continue
        f2, p2 = candidates["model 2"]
        print(f"  {title:18} {np.mean(abs(f2[m] - fee[m])):.4f} -> {np.mean(abs(fee3[m] - fee[m])):.4f};"
              f" {logloss(late[m], p2[m]):.4f} -> {logloss(late[m], late3[m]):.4f}; {m.sum()}")


# --- export: the trees as plain Python ---

def trees_of(est) -> tuple[float, list]:
    base = float(np.ravel(est._baseline_prediction)[0])
    return base, [predictors[0].nodes for predictors in est._predictors]


def emit(nodes, i: int, depth: int, out: list[str]) -> None:
    node, pad = nodes[i], "    " * depth
    if node["is_leaf"]:
        out.append(f"{pad}r += {float(node['value'])!r}")
        return
    out.append(f"{pad}if x[{int(node['feature_idx'])}] <= {float(node['num_threshold'])!r}:")
    emit(nodes, int(node["left"]), depth + 1, out)
    out.append(f"{pad}else:")
    emit(nodes, int(node["right"]), depth + 1, out)


def function(name: str, est, link: str, doc: str) -> str:
    base, trees = trees_of(est)
    out = [f"def {name}(x):", f'    """{doc}"""', f"    r = {base!r}"]
    for nodes in trees:
        emit(nodes, 0, 1, out)
    out.append("    return exp(r)" if link == "exp" else "    return 1.0 / (1.0 + exp(-r))")
    return "\n".join(out)


def export(models: dict, path: str, summary: str) -> None:
    head = f'''"""The learned cost model (fee model 3): gradient-boosted trees written out as plain Python. Do not edit.

Generated by tracks/ml/train.py from the rows of tracks/ml/rows.py; the inputs are `dispatch.features.features`,
in the order of NAMES. {summary}
"""
from math import exp

NAMES = {tuple(NAMES)!r}

'''
    body = [function("fee", models["fee"], "exp", "Expected driver fees, as a multiple of the typical fee."),
            function("late", models["late"], "logit", "The chance that the order is late or undelivered."),
            function("refund", models["refund"], "exp", "Expected late refund and undelivered penalty, as a share of the price.")]
    with open(path, "w", encoding="utf-8") as file:
        file.write(head + "\n\n\n".join(body) + "\n")
    print(f"\nwrote {path} ({os.path.getsize(path) // 1024} kB)")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rows", default=os.path.join(config.DATA, "ml", "rows.csv.gz"))
    parser.add_argument("--no-export", action="store_true")
    args = parser.parse_args()
    frame = load(args.rows)
    train, test = frame[~frame["holdout"]], frame[frame["holdout"]]
    print(f"train {len(train)} orders in {train['week'].nunique()} weeks of {train['seed'].nunique()} worlds; "
          f"test {len(test)} orders in {test['week'].nunique()} weeks of {test['seed'].nunique()} worlds")
    models = {target: fit(train, target, NAMES) for target in TARGETS}
    x = test[list(NAMES)].to_numpy()
    fee3, late3 = predict(models["fee"], x), predict(models["late"], x)

    print("  without our own state at quote time (lane, time, car, note, options, schedule only):")
    lean = tuple(name for name in NAMES if name not in STATE)
    fee_lean, late_lean = fit(train, "fee", lean), fit(train, "late", lean)
    xl = test[list(lean)].to_numpy()
    extra = {"model 3 without state": (predict(fee_lean, xl), predict(late_lean, xl))}
    refund3 = predict(models["refund"], x)
    extra["model 3, late from refund"] = (fee3, np.clip(refund3 / 0.25, 0, 1))  # a late order gives back about a quarter

    report(test, fee3, late3, extra, (float(train["fee"].mean()), float(train["late"].mean())))
    for target in ("fee", "late"):
        importance = feature_gain(models[target])
        print(f"\nlargest split gains, {target}: " + ", ".join(f"{NAMES[i]} {g:.0%}" for i, g in importance[:12]))
    if not args.no_export:
        summary = (f"Trained on {len(train)} orders from {train['seed'].nunique()} worlds (every seed but hold-*), "
                   f"{len(_trees(models['fee']))}/{len(_trees(models['late']))}/{len(_trees(models['refund']))} trees of at most depth {PARAMS['max_depth']}.")
        export(models, os.path.join(ROOT, "dispatch", "learned.py"), summary)
        check(models, test[list(NAMES)].head(2000).to_numpy())


def _trees(est) -> list:
    return est._predictors


def feature_gain(est) -> list[tuple[int, float]]:
    gain = np.zeros(len(NAMES))
    for predictors in est._predictors:
        nodes = predictors[0].nodes
        inner = nodes[~nodes["is_leaf"].astype(bool)]
        np.add.at(gain, inner["feature_idx"].astype(int), inner["gain"])
    gain = gain / gain.sum()
    return sorted(enumerate(gain), key=lambda t: -t[1])


def check(models: dict, x: np.ndarray) -> None:
    """The exported functions give the same answers as sklearn."""
    import importlib
    import dispatch.learned as learned
    importlib.reload(learned)
    for target in ("fee", "late", "refund"):
        mine = np.array([getattr(learned, target)([float(v) for v in row]) for row in x])
        theirs = predict(models[target], x)
        worst = float(np.max(abs(mine - theirs)))
        print(f"export check {target}: largest difference {worst:.2e}")
        assert worst < 1e-6 * max(1.0, float(np.max(abs(theirs)))), target
    if not math.isfinite(worst):
        raise SystemExit("export check failed")


if __name__ == "__main__":
    main()
