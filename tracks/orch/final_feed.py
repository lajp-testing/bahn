"""Reads a recording of the public final leaderboard feed (`GET /v1/leaderboard`, server-sent events every 2 seconds)
and shows how each team's orders, revenue and margin grew through the week.

    curl -sN https://spread.bahnexpress.com/v1/leaderboard >> data/finals/<name>.sse     # record (no key needed)
    python3 tracks/orch/final_feed.py data/finals/<name>.sse                            # the end table
    python3 tracks/orch/final_feed.py data/finals/<name>.sse --by day --top 12          # growth per world day
    python3 tracks/orch/final_feed.py data/finals/<name>.sse --team juhus --by hour     # one team, per world hour

Per team: orders won, revenue per order (what dealers paid), margin per order, margin share of revenue, on time.
Revenue per order against margin per order separates teams that win by price from teams that win by cheap drivers.
"""
from __future__ import annotations

import argparse
import json


def frames(path: str) -> list[dict]:
    out, last = [], None
    for line in open(path, encoding="utf-8", errors="replace"):
        if not line.startswith("data:"):
            continue
        try:
            d = json.loads(line[5:])
        except ValueError:
            continue
        if d.get("status") not in ("running", "ended") or d.get("now") is None or d.get("now") == last:
            continue
        last = d["now"]
        out.append(d)
    return out


def row(t: dict) -> tuple:
    o, rev, m = t.get("wonOrders") or 0, (t.get("revenueCents") or 0) / 100, (t.get("marginCents") or 0) / 100
    return o, rev, m, (rev / o if o else 0), (m / o if o else 0), (m / rev if rev else 0), (t.get("onTimeShare") or 0) * 100


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("--top", type=int, default=15)
    ap.add_argument("--team", action="append", default=[], help="team id(s) to follow; default: the top teams and us")
    ap.add_argument("--by", choices=("end", "day", "hour"), default="end")
    a = ap.parse_args()
    fs = frames(a.path)
    if not fs:
        raise SystemExit("no running frames yet")
    end = fs[-1]
    teams = sorted(end["teams"], key=lambda t: (t.get("rank") is None, t.get("rank") or 0, -(t.get("marginCents") or 0)))
    pick = a.team or [t["team"] for t in teams[: a.top]] + ["pelaaja-juhlii"]
    print(f"{len(fs)} frames, world minute {fs[0]['now']} to {end['now']}, status {end['status']}")
    hdr = f"{'rank':>4} {'team':24} {'orders':>6} {'revenue':>9} {'margin':>9} {'rev/ord':>7} {'mar/ord':>7} {'share':>6} {'ontime':>6}"
    if a.by == "end":
        print(hdr)
        for t in teams:
            if t["team"] not in pick:
                continue
            o, rev, m, ro, mo, sh, ot = row(t)
            print(f"{t.get('rank') or '-':>4} {t['name'][:24]:24} {o:6d} {rev:9,.0f} {m:9,.0f} {ro:7.1f} {mo:7.1f} {sh:6.1%} {ot:6.1f}")
        return
    step = 1440 if a.by == "day" else 60
    marks, seen = [], set()
    for f in fs:
        k = f["now"] // step
        if k not in seen:
            seen.add(k)
            marks.append(f)
    marks.append(end)
    for team in pick:
        print(f"\n{team}")
        print(f"{'minute':>7} {'orders':>6} {'+orders':>7} {'margin':>9} {'+margin':>8} {'rev/ord':>7} {'mar/ord':>7} {'ontime':>6}")
        prev = None
        for f in marks:
            t = next((x for x in f["teams"] if x["team"] == team), None)
            if t is None:
                continue
            o, rev, m, ro, mo, sh, ot = row(t)
            do, dm = (o - prev[0], m - prev[2]) if prev else (o, m)
            print(f"{f['now']:7d} {o:6d} {do:7d} {m:9,.0f} {dm:8,.0f} {ro:7.1f} {mo:7.1f} {ot:6.1f}")
            prev = (o, rev, m)


if __name__ == "__main__":
    main()
