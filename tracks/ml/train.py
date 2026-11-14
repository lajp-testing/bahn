"""Trains the learned cost model (fee model 3) on the rows of tracks/ml/rows.py, compares it with fee models 1
and 2 on the holdout worlds, and writes it out as plain Python (dispatch/learned.py). Run with nix develop:

    nix develop --command python tracks/ml/train.py              # train, report, export to dispatch/learned.py
    nix develop --command python tracks/ml/train.py --no-export  # report only
    nix develop --command python tracks/ml/train.py --no-export --shipped --name "model 4" \\
        --recent-weight 5 --out dispatch/learned2.py             # a retrained second model

Split by world, never by row: the holdout seeds (hold-01..10) are never trained on; the number of trees is
chosen on a few training worlds held back for that (every seventh training seed). Then the model is refit on
all training worlds with that number of trees. Rows from recent-policy weeks (flat fees or fee_model=3,
see `recent`) can be weighted higher with --recent-weight; the report adds a second table on the holdout
rows of those weeks only, which is the test that matters under the mainline we will play.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import subprocess
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
RECENT_VERSIONS = ("5ba1bf0", "e01292a", "3a6e7d9", "782a036", "5bb0223")
_ANCESTORS: dict[str, bool] = {}


def later(version: str) -> bool:
    """True when the version's mainline already opens with flat fees (5ba1bf0 or a descendant)."""
    base = version.split("+")[0]
    if base not in _ANCESTORS:
        done = subprocess.run(["git", "merge-base", "--is-ancestor", "5ba1bf0", base],
                              cwd=ROOT, capture_output=True, check=False)
        _ANCESTORS[base] = done.returncode == 0
    return _ANCESTORS[base]


def recent(frame: pd.DataFrame) -> np.ndarray:
    """One flag per row: the week was played under a recent policy (flat fees or fee_model=3).

    From the run's index row: params fee_flat=1 or fee_model=3; or a code version whose mainline
    defaults already carry flat fees (5ba1bf0 or later, checked by git when the version is unknown).
    """
    index = {}
    try:
        with open(config.INDEX, encoding="utf-8") as file:
            for line in file:
                row = json.loads(line)
                index[os.path.basename(row.get("folder") or "")] = row
    except OSError:
        pass

    def is_recent(week: str, version: str) -> bool:
        row = index.get(week, {})
        params = row.get("params") or {}
        base = (row.get("version") or version or "").split("+")[0]
        return (params.get("fee_flat") == 1 or params.get("fee_model") == 3
                or base in RECENT_VERSIONS
                or (row.get("policy") == "main" and later(base)))

    return np.array([is_recent(week, version) for week, version in zip(frame["week"], frame["version"])])

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


def fit(train: pd.DataFrame, target: str, names: tuple[str, ...], weight: pd.Series | None = None):
    """The number of trees from the held-back training worlds, then the refit on every training world."""
    kind, loss = TARGETS[target]
    seeds = sorted(train["seed"].unique())
    back_seeds = set(seeds[3::7])
    back = train["seed"].isin(back_seeds)
    inner, val = train[~back], train[back]
    w = None if weight is None else weight[~back].to_numpy()
    est = model(kind, loss, MAX_TREES).fit(inner[list(names)].to_numpy(), inner[target].to_numpy(), sample_weight=w)
    curve = [loss_of(target, val[target].to_numpy(), p) for p in staged(est, val[list(names)].to_numpy())]
    trees = int(np.argmin(curve)) + 1
    print(f"  {target}: {trees} trees (validation worlds {len(back_seeds)}: loss {curve[trees - 1]:.5f}, at {MAX_TREES} {curve[-1]:.5f})")
    return model(kind, loss, trees).fit(train[list(names)].to_numpy(), train[target].to_numpy(),
                                        None if weight is None else weight.to_numpy())

def table(fee: np.ndarray, late: np.ndarray, candidates: dict[str, tuple[np.ndarray, np.ndarray]]) -> None:
    print(f"{'':22} {'fee MAE':>8} {'fee bias':>9} {'late logloss':>13} {'late Brier':>11}")
    for name, (f, p) in candidates.items():
        print(f"{name:22} {np.mean(abs(f - fee)):8.4f} {np.mean(f - fee):+9.4f} {logloss(late, p):13.4f} {np.mean((p - late) ** 2):11.4f}")


def report(test: pd.DataFrame, candidates: dict, extra: dict, name: str) -> None:
    fee, late = test["fee"].to_numpy(), test["late"].to_numpy()
    both = candidates | extra
    print(f"\nholdout: {len(test)} orders in {test['week'].nunique()} weeks of {test['seed'].nunique()} worlds; "
          f"mean fee {fee.mean():.3f} of typical, late share {late.mean():.3f}")
    table(fee, late, both)
    fee3, late3 = both[name]

    print(f"\nlate risk by decile of {name}'s prediction: predicted / actual (model 2 by its own deciles)")
    for label in ("model 2", name):
        p = both[label][1]
        order = np.argsort(p, kind="stable")
        cells = [f"{p[part].mean():.3f}/{late[part].mean():.3f}" for part in np.array_split(order, 10)]
        print(f"  {label}: " + " ".join(cells))

    # The one that matters for quoting: rank by predicted cost per euro of list price.
    typical, listed = test["typical"].to_numpy(), test["list"].to_numpy()
    real = fee * typical / listed
    print("\ncheapest fifth by predicted fee per euro of list price: actual fee per list euro, late share")
    for label in ("model 1", "model 2", name):
        f, p = both[label]
        cheap = np.argsort(f * typical / listed, kind="stable")[: len(test) // 5]
        dear = np.argsort(-(f * typical / listed), kind="stable")[: len(test) // 5]
        print(f"  {label}: cheapest {real[cheap].mean():.4f}, late {late[cheap].mean():.3f}; dearest {real[dear].mean():.4f}, late {late[dear].mean():.3f}")
    print(f"\nby group (fee MAE model 2 -> {name}; late logloss model 2 -> {name}; n)")
    for title, mask in (("bundles on", test["bundles_on"] == 1), ("bundles off", test["bundles_on"] == 0),
                        ("fits an open gig", test["fits"] == 1), ("private address", (test["private_pickup"] + test["private_delivery"]) > 0),
                        ("same-day option", test["option"] == "same_day")):
        m = mask.to_numpy()
        if m.sum() < 50:
            continue
        f2, p2 = both["model 2"]
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


def export(models: dict, path: str, summary: str, name: str = "fee model 3") -> None:
    head = f'''"""The learned cost model ({name}): gradient-boosted trees written out as plain Python. Do not edit.

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
    parser.add_argument("--recent-weight", type=float, default=1.0,
                        help="sample weight of rows from recent-policy weeks (flat fees or fee_model=3); 1 = off")
    parser.add_argument("--out", default=os.path.join(ROOT, "dispatch", "learned.py"), help="the exported module's path")
    parser.add_argument("--name", default="model 3", help="the trained model's name in the report")
    parser.add_argument("--shipped", action="store_true", help="add the current dispatch/learned.py to the report")
    args = parser.parse_args()
    frame = load(args.rows)
    train, test = frame[~frame["holdout"]], frame[frame["holdout"]]
    hold = frame["holdout"].to_numpy()
    is_recent = recent(frame)
    print(f"train {len(train)} orders in {train['week'].nunique()} weeks of {train['seed'].nunique()} worlds, "
          f"{is_recent[~hold].sum()} of them in recent-policy weeks; "
          f"test {len(test)} orders in {test['week'].nunique()} weeks of {test['seed'].nunique()} worlds")
    weight = pd.Series(np.where(is_recent[~hold], args.recent_weight, 1.0), index=train.index)
    models = {target: fit(train, target, NAMES, weight) for target in TARGETS}
    x = test[list(NAMES)].to_numpy()
    fee3, late3 = predict(models["fee"], x), predict(models["late"], x)
    candidates = {"constant": (np.full(len(test), float(train["fee"].mean())), np.full(len(test), float(train["late"].mean()))),
                  "model 1": (test["m1_fee"].to_numpy(), test["m1_late"].to_numpy()),
                  "model 2": (test["m2_fee"].to_numpy(), test["m2_late"].to_numpy()),
                  args.name: (fee3, late3)}
    if args.shipped:
        candidates["model 3 (shipped)"] = shipped(x)

    print("  without our own state at quote time (lane, time, car, note, options, schedule only):")
    lean = tuple(name for name in NAMES if name not in STATE)
    fee_lean, late_lean = fit(train, "fee", lean, weight), fit(train, "late", lean, weight)
    xl = test[list(lean)].to_numpy()
    extra = {f"{args.name} without state": (predict(fee_lean, xl), predict(late_lean, xl))}
    refund3 = predict(models["refund"], x)
    extra[f"{args.name}, late from refund"] = (fee3, np.clip(refund3 / 0.25, 0, 1))  # a late order gives back about a quarter

    report(test, candidates, extra, args.name)
    for target in ("fee", "late"):
        importance = feature_gain(models[target])
        print(f"\nlargest split gains, {target}: " + ", ".join(f"{NAMES[i]} {g:.0%}" for i, g in importance[:12]))

    mask = is_recent[hold]
    if mask.any():
        fee, late = test["fee"].to_numpy(), test["late"].to_numpy()
        sub = test[mask]
        print(f"\nrecent-policy holdout rows only: {mask.sum()} orders in {sub['week'].nunique()} weeks of "
              f"{sub['seed'].nunique()} worlds; mean fee {fee[mask].mean():.3f}, late share {late[mask].mean():.3f}")
        table(fee[mask], late[mask], {k: (f[mask], p[mask]) for k, (f, p) in candidates.items()})

    if not args.no_export:
        summary = (f"Trained on {len(train)} orders from {train['seed'].nunique()} worlds (every seed but hold-*), "
                   f"recent-policy rows weighted {args.recent_weight:g}, "
                   f"{len(_trees(models['fee']))}/{len(_trees(models['late']))}/{len(_trees(models['refund']))} trees of at most depth {PARAMS['max_depth']}.")
        export(models, args.out, summary, f"fee model {3 if args.out.endswith('learned.py') else 4}")
        check(models, test[list(NAMES)].head(2000).to_numpy(), args.out)


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


def shipped(x: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """The current dispatch/learned.py's answers, in plain Python exactly as the dispatcher runs it."""
    import dispatch.learned as learned
    fee = np.array([learned.fee([float(v) for v in row]) for row in x])
    late = np.array([learned.late([float(v) for v in row]) for row in x])
    return fee, late


def check(models: dict, x: np.ndarray, path: str) -> None:
    """The exported functions give the same answers as sklearn."""
    import importlib
    learned = importlib.import_module("dispatch." + os.path.basename(path)[:-3])
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
