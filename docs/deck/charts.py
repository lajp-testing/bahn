"""Draws the deck's charts as SVG from saved weeks, so every number can be refreshed.

    python3 docs/deck/charts.py            # reads data/runs.jsonl of the main checkout
    SPREAD_DATA=/path/to/data python3 docs/deck/charts.py

Writes docs/deck/charts/*.svg and docs/deck/numbers.json (every number the charts show).
Standard library only. Which label each chart reads is written next to it below and in README.md.
"""
from __future__ import annotations

import gzip
import json
import os
import statistics
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
DATA = Path(os.environ.get("SPREAD_DATA", "/home/agent/.t3/projects/bahn/data"))
OUT = HERE / "charts"
FEED = REPO / "tracks/orch/finals/testfinal-20261114-1800/leaderboard-feed.sse.gz"

# Colours (validated categorical slots 1 and 2 of the dataviz reference palette, plus neutrals).
INK, INK2, MUTED, GRID = "#0b0b0b", "#52514e", "#8a8984", "#e4e3df"
BLUE, ORANGE, GREY = "#2a78d6", "#eb6834", "#c9c8c2"
FONT = "Inter, 'Helvetica Neue', Arial, sans-serif"

SEEDS40 = [f"dev-{i:02d}" for i in range(1, 11)] + [f"rob-{i:02d}" for i in range(1, 21)] + [f"hold-{i:02d}" for i in range(1, 11)]
SEEDS30 = SEEDS40[:30]
UNSEEN30 = [f"rob-{i:02d}" for i in range(21, 51)]
UNSEEN40 = [f"rob-{i:02d}" for i in range(21, 61)]

# The day's adopted steps, in order (tracks/orch/FINDINGS.md, sections 10:45 to 21:45 UTC).
STEPS = [
    ("t3s10-calm", "Morning", "10:45"),
    ("t3s15-safe-flat15", "Safe cars +\nflat fees", "13:40"),
    ("b37-fee3", "Learned\ncost model", "14:00"),
    ("b46-car105-sameday480", "Same-day +\ncost tilt", "15:05"),
    ("b52-fee4-car110", "Model 4 +\ncar 1.1", "17:00"),
    ("b68-floor075-short095-carshort085", "Fee floors +\nshort lanes", "19:45"),
    ("b84-fee5", "Model 5", "21:30"),
    ("b87-fee5-limit45", "Limits\n45 / 55 / 100", "21:45"),
]


def load_runs() -> dict[str, dict[str, dict]]:
    by: dict[str, dict[str, dict]] = {}
    for line in open(DATA / "runs.jsonl", encoding="utf-8"):
        r = json.loads(line)
        if r.get("board") or r.get("level") != 8:
            continue
        by.setdefault(r["label"], {})[r["seed"]] = r  # a later row for the same seed replaces the earlier
    return by


def week_stats(runs: dict[str, dict], seeds: list[str]) -> dict:
    rs = [runs[s] for s in seeds]
    orders = sum(r["wonOrders"] for r in rs)
    return {
        "weeks": len(rs),
        "margin_eur": round(sum(r["marginCents"] for r in rs) / 100, 2),
        "mean_week_eur": round(sum(r["marginCents"] for r in rs) / 100 / len(rs), 2),
        "orders_per_week": round(orders / len(rs), 1),
        "on_time_pct": round(100 * sum(r["onTimeShare"] * r["wonOrders"] for r in rs) / orders, 2),
        "lowest_on_time": sorted(round(100 * r["onTimeShare"], 1) for r in rs)[:3],
        "all_ranked": all(r["ranked"] for r in rs),
        "per_week_eur": {s: round(runs[s]["marginCents"] / 100, 2) for s in seeds},
        "per_week_on_time": {s: round(100 * runs[s]["onTimeShare"], 2) for s in seeds},
    }


def paired(a: dict, b: dict, seeds: list[str]) -> dict:
    d = {s: (a[s]["marginCents"] - b[s]["marginCents"]) / 100 for s in seeds}
    return {"weeks": len(seeds), "change_eur": round(sum(d.values()), 2), "ahead": sum(v > 0 for v in d.values()), "per_week": d}


# ---------------------------------------------------------------- SVG helpers

def svg(w: int, h: int, body: list[str]) -> str:
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" '
            f'font-family="{FONT}">\n' + "\n".join(body) + "\n</svg>\n")


def text(x, y, s, size=14, fill=INK2, anchor="start", weight=400, extra=""):
    lines = str(s).split("\n")
    out = []
    for i, ln in enumerate(lines):
        ln = ln.replace("&", "&amp;").replace("<", "&lt;")
        out.append(f'<text x="{x:.1f}" y="{y + i * size * 1.2:.1f}" font-size="{size}" fill="{fill}" '
                   f'text-anchor="{anchor}" font-weight="{weight}" {extra}>{ln}</text>')
    return "\n".join(out)


def eur(v: float, sign=False) -> str:
    s = f"{abs(v):,.0f}"
    return (("+" if v >= 0 else "−") if sign else ("−" if v < 0 else "")) + "€" + s


# ---------------------------------------------------------------- charts

def chart_steps(runs, nums):
    """Margin per week on the same 40 worlds, at each adopted step of the day."""
    W, H, L, R, T, B = 1160, 330, 64, 10, 26, 80
    ys = []
    for label, _, _ in STEPS:
        ys += [runs[label][s]["marginCents"] / 100 for s in SEEDS40]
    lo, hi = 5000, 27500
    sx = (W - L - R) / len(STEPS)
    y = lambda v: T + (H - T - B) * (1 - (v - lo) / (hi - lo))
    body = [f'<rect width="{W}" height="{H}" fill="white"/>']
    for g in range(5000, 27501, 5000):
        body.append(f'<line x1="{L}" x2="{W - R}" y1="{y(g):.1f}" y2="{y(g):.1f}" stroke="{GRID}" stroke-width="1"/>')
        body.append(text(L - 10, y(g) + 5, f"€{g // 1000}k", 14, MUTED, "end"))
    nums["steps"] = []
    prev = None
    for i, (label, name, at) in enumerate(STEPS):
        st = week_stats(runs[label], SEEDS40)
        cx = L + sx * (i + 0.5)
        vals = [st["per_week_eur"][s] for s in SEEDS40]
        for j, v in enumerate(sorted(vals)):
            jit = ((j * 37) % 17 - 8) * 2.2
            body.append(f'<circle cx="{cx + jit:.1f}" cy="{y(v):.1f}" r="3.2" fill="{BLUE}" fill-opacity="0.28"/>')
        m = st["mean_week_eur"]
        body.append(f'<line x1="{cx - 30:.1f}" x2="{cx + 30:.1f}" y1="{y(m):.1f}" y2="{y(m):.1f}" stroke="{INK}" stroke-width="3" stroke-linecap="round"/>')
        body.append(text(cx, y(m) - 12, eur(m), 16, INK, "middle", 700))
        body.append(text(cx, H - B + 20, name, 14, INK, "middle", 600))
        body.append(text(cx, H - B + 56, f"{at} UTC", 12, MUTED, "middle"))
        body.append(text(cx, H - B + 72, f"lowest week {st['lowest_on_time'][0]:.1f}%", 12.5, INK2, "middle"))
        if prev is not None:
            px, pm = prev
            body.append(f'<line x1="{px + 30:.1f}" x2="{cx - 30:.1f}" y1="{y(pm):.1f}" y2="{y(m):.1f}" stroke="{INK}" stroke-opacity="0.35" stroke-width="1.5" stroke-dasharray="4 4"/>')
        prev = (cx, m)
        nums["steps"].append({"label": label, "at": at, **{k: v for k, v in st.items() if not k.startswith("per_week")}})
    (OUT / "steps.svg").write_text(svg(W, H, body))


def chart_unseen(runs, nums):
    """The candidate for the final against the 19:45 mainline, on 30 worlds no part was tuned on."""
    a, b = runs["b89-main"], runs["b68-floor075-short095-carshort085"]
    p = paired(a, b, UNSEEN30)
    nums["unseen_b89_vs_b68"] = {k: v for k, v in p.items() if k != "per_week"}
    nums["unseen40_b89"] = {k: v for k, v in week_stats(a, UNSEEN40).items() if not k.startswith("per_week")}
    W, H, L, R, T, B = 720, 320, 80, 10, 30, 16
    d = sorted(p["per_week"].values())
    m = max(abs(v) for v in d)
    lim = (int(m / 1000) + 1) * 1000
    y = lambda v: T + (H - T - B) * (1 - (v + lim) / (2 * lim))
    bw = (W - L - R) / len(d)
    body = [f'<rect width="{W}" height="{H}" fill="white"/>']
    for g in range(-lim, lim + 1, 1000):
        body.append(f'<line x1="{L}" x2="{W - R}" y1="{y(g):.1f}" y2="{y(g):.1f}" stroke="{GRID if g else INK2}" stroke-width="1"/>')
        body.append(text(L - 10, y(g) + 5, eur(g, sign=bool(g)) if g else "€0", 14, MUTED, "end"))
    for i, v in enumerate(d):
        x0 = L + i * bw + 2
        top, bot = (y(v), y(0)) if v >= 0 else (y(0), y(v))
        body.append(f'<rect x="{x0:.1f}" y="{top:.1f}" width="{bw - 4:.1f}" height="{max(bot - top, 1):.1f}" rx="3" fill="{BLUE if v >= 0 else ORANGE}"/>')
    body.append(text(L + 6, T - 8, f"Ahead in {p['ahead']} of {p['weeks']} weeks, {eur(p['change_eur'], True)} in total", 17, INK, "start", 700))
    (OUT / "unseen.svg").write_text(svg(W, H, body))


def chart_testfinal(nums):
    """Every ranked team at the end of the 18:00 UTC test final, from the recorded public leaderboard feed."""
    last = None
    for line in gzip.open(FEED, "rt", encoding="utf-8", errors="replace"):
        if line.startswith("data:"):
            try:
                d = json.loads(line[5:])
            except ValueError:
                continue
            if d.get("status") in ("running", "ended") and d.get("teams"):
                last = d
    teams = [t for t in last["teams"] if t.get("ranked") and t.get("wonOrders")]
    us = next(t for t in teams if t["team"] in ("pelaaja-juhlii", "pelaajajuhlii") or "pelaaja" in t["name"].lower())
    top = min(teams, key=lambda t: t["rank"])
    nums["testfinal"] = {"ranked_teams": len(teams), "our_rank": us["rank"], "our_margin_eur": us["marginCents"] / 100,
                         "our_orders": us["wonOrders"], "our_on_time_pct": round(100 * us["onTimeShare"], 1),
                         "top_margin_eur": top["marginCents"] / 100, "top_orders": top["wonOrders"]}
    W, H, L, R, T, B = 600, 430, 56, 16, 34, 56
    xlo, xhi, ylo, yhi = 0, 600, 0, 70
    X = lambda v: L + (W - L - R) * (v - xlo) / (xhi - xlo)
    Y = lambda v: T + (H - T - B) * (1 - (v - ylo) / (yhi - ylo))
    body = [f'<rect width="{W}" height="{H}" fill="white"/>']
    for g in range(0, 71, 10):
        body.append(f'<line x1="{L}" x2="{W - R}" y1="{Y(g):.1f}" y2="{Y(g):.1f}" stroke="{GRID}"/>')
        body.append(text(L - 8, Y(g) + 5, f"€{g}", 14, MUTED, "end"))
    for g in range(0, 601, 100):
        body.append(text(X(g), H - B + 22, str(g), 14, MUTED, "middle"))
    body.append(text((L + W - R) / 2, H - 6, "orders won in the week", 15, INK2, "middle"))
    body.append(text(L - 50, T - 16, "margin per order", 15, INK2, "start"))
    # Iso-margin curve through our result.
    mu = us["marginCents"] / 100
    pts = " ".join(f"{X(o):.1f},{Y(mu / o):.1f}" for o in range(260, 600, 5) if mu / o <= yhi)
    body.append(f'<polyline points="{pts}" fill="none" stroke="{INK2}" stroke-width="1.5" stroke-dasharray="5 5"/>')
    body.append(text(X(300) + 10, Y(mu / 300) + 4, "same total margin as ours", 14, INK2, "start", 400, 'stroke="white" stroke-width="4" paint-order="stroke"'))
    for t in teams:
        if t is us or t is top:
            continue
        o, m = t["wonOrders"], t["marginCents"] / 100 / t["wonOrders"]
        if xlo <= o <= xhi and ylo <= m <= yhi:
            body.append(f'<circle cx="{X(o):.1f}" cy="{Y(m):.1f}" r="4.5" fill="{GREY}"/>')
    for t, col, lab, dx, dy in ((top, ORANGE, f"1st: {top['wonOrders']} orders, {eur(top['marginCents'] / 100)}", 4, 34),
                                (us, BLUE, f"us, 5th: {us['wonOrders']} orders, {eur(mu)}", -14, -16)):
        o, m = t["wonOrders"], t["marginCents"] / 100 / t["wonOrders"]
        body.append(f'<circle cx="{X(o):.1f}" cy="{Y(m):.1f}" r="8" fill="{col}" stroke="white" stroke-width="2"/>')
        body.append(text(X(o) + dx, Y(m) + dy, lab, 15, INK, "end" if dx < 0 else "middle", 700, 'stroke="white" stroke-width="5" paint-order="stroke"'))
    (OUT / "testfinal.svg").write_text(svg(W, H, body))


def chart_flood(nums):
    """On-time share by kind of car, normal intake against 55% more orders (t1s11-base vs t1s13-flood, 10 dev weeks).
    Numbers from tracks/t1/FINDINGS.md, 'What breaks, by group'."""
    groups = [("under\n100 km", 98.1, 94.6), ("100–200", 97.2, 95.3), ("200–300", 96.8, 94.3),
              ("300–500", 96.1, 88.2), ("500 km\nand more", 88.2, 72.3), ("private\naddress", 81.1, 75.9)]
    nums["flood_on_time"] = groups
    W, H, L, R, T, B = 620, 380, 50, 8, 44, 70
    lo, hi = 60, 100
    Y = lambda v: T + (H - T - B) * (1 - (v - lo) / (hi - lo))
    gw = (W - L - R) / len(groups)
    body = [f'<rect width="{W}" height="{H}" fill="white"/>']
    for g in range(60, 101, 10):
        body.append(f'<line x1="{L}" x2="{W - R}" y1="{Y(g):.1f}" y2="{Y(g):.1f}" stroke="{GRID}"/>')
        body.append(text(L - 6, Y(g) + 5, f"{g}%", 13, MUTED, "end"))
    body.append(f'<line x1="{L}" x2="{W - R}" y1="{Y(90):.1f}" y2="{Y(90):.1f}" stroke="{INK2}" stroke-dasharray="5 4"/>')
    body.append(text(W - R - 4, Y(90) - 6, "90%: ranked", 13, INK2, "end"))
    for i, (name, a, b) in enumerate(groups):
        x0 = L + i * gw + gw * 0.14
        bw = gw * 0.34
        for k, (v, col) in enumerate(((a, BLUE), (b, ORANGE))):
            xx = x0 + k * (bw + 3)
            body.append(f'<rect x="{xx:.1f}" y="{Y(v):.1f}" width="{bw:.1f}" height="{Y(lo) - Y(v):.1f}" rx="3" fill="{col}"/>')
            body.append(text(xx + bw / 2, Y(v) - 6, f"{v:.0f}", 13, INK2, "middle"))
        body.append(text(L + i * gw + gw / 2, H - B + 20, name, 14, INK2, "middle"))
    body.append(f'<path d="M {L + 8} {T - 8} V {T - 14} H {L + 3 * gw - 8} V {T - 8}" fill="none" stroke="{INK2}" stroke-width="1.5"/>')
    body.append(text(L + 1.5 * gw, T - 22, "safe cars: under 300 km, no private address", 14, INK, "middle", 600))
    body.append(f'<rect x="{W - R - 290}" y="{H - 20}" width="13" height="13" rx="2" fill="{BLUE}"/>')
    body.append(text(W - R - 272, H - 9, "normal intake", 14, INK2))
    body.append(f'<rect x="{W - R - 150}" y="{H - 20}" width="13" height="13" rx="2" fill="{ORANGE}"/>')
    body.append(text(W - R - 132, H - 9, "55% more orders", 14, INK2))
    (OUT / "flood.svg").write_text(svg(W, H, body))


def chart_sameday(runs, nums):
    """Four ways to win margin back on the learned-model mainline, on the same 30 dev + rob weeks against b37-fee3."""
    base = runs["b37-fee3"]
    rows = [("b44-car100", "cost tilt 1.0"), ("b43-car105", "cost tilt 1.05"),
            ("b45-sameday480", "same-day whenever\n8 h of slack"), ("b46-car105-sameday480", "both: same-day\n+ tilt 1.05")]
    data = []
    for label, name in rows:
        p = paired(runs[label], base, SEEDS30)
        st = week_stats(runs[label], SEEDS30)
        data.append((name, p["change_eur"], p["ahead"], st["lowest_on_time"][0], label))
    nums["sameday_vs_b37_30wk"] = [{"label": d[4], "change_eur": d[1], "ahead": d[2], "lowest_on_time": d[3]} for d in data]
    W, H, L, R, T, B = 640, 300, 175, 120, 24, 30
    hi = 40000
    X = lambda v: L + (W - L - R) * v / hi
    bh = (H - T - B) / len(data)
    body = [f'<rect width="{W}" height="{H}" fill="white"/>']
    for g in range(0, hi + 1, 10000):
        body.append(f'<line x1="{X(g):.1f}" x2="{X(g):.1f}" y1="{T}" y2="{H - B}" stroke="{GRID}"/>')
        body.append(text(X(g), H - B + 20, eur(g, bool(g)) if g else "€0", 13, MUTED, "middle"))
    body.append(text(W - R + 14, T - 6, "lowest week", 13, MUTED))
    for i, (name, ch, ahead, low, label) in enumerate(data):
        yc = T + bh * (i + 0.5)
        unranked = low < 90
        col = ORANGE if unranked else BLUE
        body.append(f'<rect x="{L}" y="{yc - bh * 0.28:.1f}" width="{max(X(ch) - L, 2):.1f}" height="{bh * 0.56:.1f}" rx="4" fill="{col}"/>')
        body.append(text(L - 10, yc + (-3 if "\n" in name else 5), name, 14, INK2, "end"))
        body.append(text(X(ch) + 8, yc + 5, eur(ch, True), 15, INK, "start", 700))
        body.append(text(W - R + 14, yc + (-3 if unranked else 5), f"{low:.1f}%" + ("\nunranked" if unranked else ""), 15, "#b8461a" if unranked else INK2, "start", 700 if unranked else 400))
    (OUT / "sameday.svg").write_text(svg(W, H, body))


def board(nums):
    rows = [json.loads(l) for l in open(DATA / "runs.jsonl", encoding="utf-8")]
    b = [r for r in rows if r.get("board") and r["label"].startswith("b81-board-s9")]
    orders = sum(r["wonOrders"] for r in b)
    nums["board_saturday_2100"] = {"runs": len(b), "margin_eur": round(sum(r["marginCents"] for r in b) / 100, 2), "orders": orders,
                                   "on_time_pct": round(100 * sum(r["onTimeShare"] * r["wonOrders"] for r in b) / orders, 2)}


def main():
    OUT.mkdir(exist_ok=True)
    runs = load_runs()
    nums: dict = {}
    chart_steps(runs, nums)
    chart_unseen(runs, nums)
    chart_testfinal(nums)
    chart_flood(nums)
    chart_sameday(runs, nums)
    board(nums)
    (HERE / "numbers.json").write_text(json.dumps(nums, indent=1, ensure_ascii=False) + "\n")
    print(json.dumps(nums, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
