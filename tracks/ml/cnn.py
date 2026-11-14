"""Fee model 4: a small CNN on a map of the lane, joined with the features of fee model 3.

    python tracks/ml/cnn.py                # train, report on the holdout worlds, export dispatch/learned_cnn.py
    python tracks/ml/cnn.py --epochs 10

Needs torch, numpy and pandas, and the rows of tracks/ml/rows.py (data/ml/rows.csv.gz). The picture is a
16 x 8 grid of Finland with seven channels: the pickup, the delivery, the drivers living within 80 km of
each (log), and for every place of the map the drivers living there, our booked gigs that end there and our
open gigs that start there (dispatch.features.map_features; log of the sum in a cell). Two 3 x 3 convolutions read it; a dense layer reads the 44
features; a joint layer gives the expected fee (Poisson, as a multiple of typical) and the late risk.
Split by world: hold-* seeds are never trained on. The export is plain Python, as dispatch/learned.py is.
"""
from __future__ import annotations

import argparse
import importlib
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
if "SPREAD_HOME" not in os.environ and not os.path.exists("/home/agent/.t3/projects/bahn"):
    os.environ["SPREAD_HOME"] = ROOT

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import torch  # noqa: E402
import torch.nn.functional as F  # noqa: E402
from torch import nn  # noqa: E402

from dispatch.features import MAP_CHANNELS, MAP_NAMES, NAMES, PLACES  # noqa: E402
from harness import config  # noqa: E402

H, W = 16, 8
LAT0, LATS, LON0, LONS = 59.5, 7.5, 20.5, 10.0  # the grid covers 59.5..67 N, 20.5..30.5 E
ENDS = ((NAMES.index("pickup_lat"), NAMES.index("pickup_lon"), NAMES.index("pickup_80")),
        (NAMES.index("delivery_lat"), NAMES.index("delivery_lon"), NAMES.index("delivery_80")))
COLUMNS = list(NAMES + MAP_NAMES)
CHANNELS = 4 + len(MAP_CHANNELS)


def cells() -> list[int]:
    """The grid cell (row x W + column) of each place of the map, in the map's order."""
    for path in (os.path.join(config.DATA, "map.json"), os.path.join(ROOT, "tracks", "t2", "map.json")):
        if os.path.exists(path):
            places = json.load(open(path, encoding="utf-8"))["places"]
            assert len(places) == PLACES
            return [min(H - 1, max(0, int((p["lat"] - LAT0) / LATS * H))) * W + min(W - 1, max(0, int((p["lon"] - LON0) / LONS * W))) for p in places]
    raise SystemExit("no map.json")


CELLS = cells()


def images(x: np.ndarray) -> np.ndarray:
    """The pictures of a batch of rows (the columns of COLUMNS)."""
    img, rows = np.zeros((len(x), CHANNELS, H, W), np.float32), np.arange(len(x))
    for k in range(len(MAP_CHANNELS)):
        plane = img[:, 4 + k].reshape(len(x), H * W)  # a view: several places can share a cell
        for p, cell in enumerate(CELLS):
            plane[:, cell] += x[:, len(NAMES) + k * PLACES + p]
        np.log1p(plane, out=plane)
    for ch, (lat, lon, near) in enumerate(ENDS):
        r = np.clip(((x[:, lat] - LAT0) / LATS * H).astype(int), 0, H - 1)
        c = np.clip(((x[:, lon] - LON0) / LONS * W).astype(int), 0, W - 1)
        img[rows, ch, r, c] = 1.0
        img[rows, 2 + ch, r, c] = np.log1p(x[:, near])
    return img


class Net(nn.Module):
    def __init__(self, features: int):
        super().__init__()
        self.c1, self.c2 = nn.Conv2d(CHANNELS, 8, 3, padding=1), nn.Conv2d(8, 16, 3, padding=1)
        self.t, self.h, self.o = nn.Linear(features, 32), nn.Linear(48, 32), nn.Linear(32, 2)

    def forward(self, img, tab):
        a = F.max_pool2d(F.relu(self.c1(img)), 2)
        a = F.relu(self.c2(a)).amax((2, 3))
        return self.o(F.relu(self.h(torch.cat([a, F.relu(self.t(tab))], 1))))  # log fee, logit late


def predict(net, x, mean, std, device) -> tuple[np.ndarray, np.ndarray]:
    net.eval()
    out = []
    with torch.no_grad():
        for i in range(0, len(x), 8192):
            part = x[i:i + 8192]
            out.append(net(torch.from_numpy(images(part)).to(device), torch.from_numpy((part[:, :len(NAMES)] - mean) / std).to(device)).cpu().numpy())
    out = np.concatenate(out)
    return np.exp(out[:, 0]), 1 / (1 + np.exp(-out[:, 1]))


def logloss(y, p) -> float:
    p = np.clip(p, 1e-4, 1 - 1e-4)
    return float(-np.mean(y * np.log(p) + (1 - y) * np.log(1 - p)))


FORWARD = '''
def _conv(a, w, b):
    """A 3 x 3 convolution with padding 1, then ReLU. It skips the empty cells of the picture."""
    h, wd, out = len(a[0]), len(a[0][0]), []
    for o in range(len(w)):
        plane = [[b[o]] * wd for _ in range(h)]
        for c, src in enumerate(a):
            k = w[o][c]
            for i in range(h):
                for j in range(wd):
                    v = src[i][j]
                    if v:
                        for di in (-1, 0, 1):
                            for dj in (-1, 0, 1):
                                if 0 <= i - di < h and 0 <= j - dj < wd:
                                    plane[i - di][j - dj] += v * k[di + 1][dj + 1]
        out.append([[v if v > 0 else 0.0 for v in row] for row in plane])
    return out


def _dense(x, w, b, relu=True):
    out = [sum(wi * xi for wi, xi in zip(row, x)) + bi for row, bi in zip(w, b)]
    return [v if v > 0 else 0.0 for v in out] if relu else out


def _forward(x):
    if _memo[0] is x:  # the quoter asks for the fee and the late risk of the same request
        return _memo[1]
    img = [[[0.0] * W for _ in range(H)] for _ in range(CHANNELS)]
    for k in range(CHANNELS - 4):
        plane = img[4 + k]
        for p, cell in enumerate(CELLS):
            plane[cell // W][cell % W] += x[len(MEAN) + k * len(CELLS) + p]
        img[4 + k] = [[log1p(v) for v in row] for row in plane]
    for ch, (lat, lon, near) in enumerate(ENDS):
        r = min(H - 1, max(0, int((x[lat] - LAT0) / LATS * H)))
        c = min(W - 1, max(0, int((x[lon] - LON0) / LONS * W)))
        img[ch][r][c], img[2 + ch][r][c] = 1.0, log1p(x[near])
    a = _conv(img, P["c1.weight"], P["c1.bias"])
    a = [[[max(p[2 * i][2 * j], p[2 * i][2 * j + 1], p[2 * i + 1][2 * j], p[2 * i + 1][2 * j + 1]) for j in range(W // 2)] for i in range(H // 2)] for p in a]
    a = [max(max(row) for row in p) for p in _conv(a, P["c2.weight"], P["c2.bias"])]
    t = _dense([(v - m) / s for v, m, s in zip(x, MEAN, STD)], P["t.weight"], P["t.bias"])
    out = _dense(_dense(a + t, P["h.weight"], P["h.bias"]), P["o.weight"], P["o.bias"], relu=False)
    _memo[0], _memo[1] = x, out
    return out


def fee(x):
    """Expected driver fees, as a multiple of the typical fee."""
    return exp(_forward(x)[0])


def late(x):
    """The chance that the order is late or undelivered."""
    return 1.0 / (1.0 + exp(-_forward(x)[1]))
'''


def export(net, mean, std, path: str, summary: str) -> None:
    weights = {name: value.detach().cpu().tolist() for name, value in net.state_dict().items()}
    with open(path, "w", encoding="utf-8") as file:
        file.write(f'"""The learned cost model as a CNN (fee model 4), written out as plain Python. Do not edit.\n\n'
                   f'Generated by tracks/ml/cnn.py; the inputs are `dispatch.features.features`, in the order of NAMES. {summary}\n"""\n'
                   f"from math import exp, log1p\n\nNAMES = {tuple(COLUMNS)!r}\nH, W, CHANNELS = {H}, {W}, {CHANNELS}\nCELLS = {CELLS!r}\n"
                   f"LAT0, LATS, LON0, LONS = {LAT0}, {LATS}, {LON0}, {LONS}\nENDS = {ENDS!r}\n"
                   f"MEAN = {mean.tolist()!r}\nSTD = {std.tolist()!r}\nP = {weights!r}\n_memo = [None, None]\n" + FORWARD)
    print(f"wrote {path} ({os.path.getsize(path) // 1024} kB)")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rows", default=os.path.join(config.DATA, "ml", "rows.csv.gz"))
    parser.add_argument("--epochs", type=int, default=6)
    parser.add_argument("--batch", type=int, default=1024)
    args = parser.parse_args()
    torch.manual_seed(0)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    frame = pd.read_csv(args.rows, dtype={name: np.float32 for name in COLUMNS})
    hold = frame["seed"].str.startswith("hold-")
    train, test = frame[~hold], frame[hold]
    x, y = train[COLUMNS].to_numpy(), train[["fee", "late"]].to_numpy(np.float32)
    mean, std = x[:, :len(NAMES)].mean(0), x[:, :len(NAMES)].std(0)
    std[std == 0] = 1.0
    print(f"train {len(train)} orders of {train['seed'].nunique()} worlds; test {len(test)} orders of {test['seed'].nunique()} worlds; {device}")

    net = Net(len(NAMES)).to(device)
    opt = torch.optim.AdamW(net.parameters(), lr=2e-3, weight_decay=1e-4)
    steps = args.epochs * (len(x) // args.batch + 1)
    sched = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr=2e-3, total_steps=steps)
    xt, ft, lt = test[COLUMNS].to_numpy(), test["fee"].to_numpy(), test["late"].to_numpy()
    for epoch in range(args.epochs):
        net.train()
        order, total = np.random.default_rng(epoch).permutation(len(x)), 0.0
        for i in range(0, len(order), args.batch):
            idx = order[i:i + args.batch]
            out = net(torch.from_numpy(images(x[idx])).to(device), torch.from_numpy((x[idx][:, :len(NAMES)] - mean) / std).to(device))
            target = torch.from_numpy(y[idx]).to(device)
            loss = (torch.exp(out[:, 0]) - target[:, 0] * out[:, 0]).mean() + F.binary_cross_entropy_with_logits(out[:, 1], target[:, 1])
            opt.zero_grad()
            loss.backward()
            opt.step()
            sched.step()
            total += float(loss) * len(idx)
        f, p = predict(net, xt, mean, std, device)
        print(f"epoch {epoch + 1}: train loss {total / len(x):.4f}; holdout fee MAE {np.mean(abs(f - ft)):.4f}, late logloss {logloss(lt, p):.4f}")

    candidates = {"model 2": (test["m2_fee"].to_numpy(), test["m2_late"].to_numpy()), "model 4 (CNN)": (f, p)}
    try:  # the trees, on the same rows
        learned = importlib.import_module("dispatch.learned")
        rows = [[float(v) for v in row[:len(NAMES)]] for row in xt]
        candidates["model 3 (trees)"] = (np.array([learned.fee(r) for r in rows]), np.array([learned.late(r) for r in rows]))
    except ImportError:
        pass
    print(f"\n{'':18} {'fee MAE':>8} {'fee bias':>9} {'late logloss':>13}")
    for name, (cf, cp) in candidates.items():
        print(f"{name:18} {np.mean(abs(cf - ft)):8.4f} {np.mean(cf - ft):+9.4f} {logloss(lt, cp):13.4f}")

    path = os.path.join(ROOT, "dispatch", "learned_cnn.py")
    export(net, mean, std, path, f"Trained on {len(train)} orders from {train['seed'].nunique()} worlds (every seed but hold-*), {args.epochs} epochs.")
    mine = importlib.import_module("dispatch.learned_cnn")
    worst = max(abs(mine.fee([float(v) for v in row]) - f[i]) for i, row in enumerate(xt[:500]))
    print(f"export check: largest fee difference {worst:.2e} on 500 rows")
    assert worst < 1e-3, "the plain-Python network differs from torch"


if __name__ == "__main__":
    main()
