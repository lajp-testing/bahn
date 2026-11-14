"""The test final's queue over the week: does a full unbooked queue price us out?

    python3 tracks/t2/queue_final.py [DIR=tracks/t2/final-1800]

Rebuilds, at every price_request minute, the count of our orders without a booked
driver (order_won minus gig_booked / delivered / cancelled; gig_dropped and
gig_expired put an order back), then buckets the requests by waiting = unbooked /
limit. The intake's limit is 45 before 12:00 and 35 after; the quoter's queue
charge (0.3 x waiting^2) always divides by 35.

A decline is not an empty answer: `dispatch.quote.decline` sends the first option
at 5x its list price, so a request whose every quoted option sits at exactly 5x
list was declined by the intake (all 85 such requests below were checked against
the desk's journal in tracks/orch/finals/testfinal-2026-11-14-1800). Writes the
tables of FINDINGS.md "Test final 18:00: queue and price over the week". Standard
library only.
"""
from __future__ import annotations

import json
import os
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
DAY = 1440
WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
BUCKETS = [(0.0, 0.25), (0.25, 0.5), (0.5, 0.75), (0.75, 1.0), (1.0, float("inf"))]
DECLINE_FACTOR = 5  # dispatch/quote.py: a decline quotes the first option at 5x its list price


def find_dir(name: str) -> str:
    here = os.path.join(HERE, name)
    return here if os.path.isdir(here) else os.path.join(
        "/home/agent/.t3/projects/bahn/tracks/t2", name)


def load(dirpath: str):
    with open(os.path.join(dirpath, "events.json"), encoding="utf-8") as fh:
        events = json.load(fh)
    with open(os.path.join(dirpath, "reveal.json"), encoding="utf-8") as fh:
        reveal = json.load(fh)
    with open(os.path.join(dirpath, "snapshot.json"), encoding="utf-8") as fh:
        snapshot = json.load(fh)
    return events, reveal, snapshot


def unbooked_at_requests(events: list, snapshot: dict, quoted: set | None = None) -> dict:
    """For each price_request event: (minute, unbooked orders, pending quoted requests).

    Mirrors `dispatch.intake.unbooked`: an order counts while it is won, not cancelled,
    not fully delivered, and one of its undelivered legs has no gig now or a gig no
    driver holds. The desk keeps one current gig per leg (`leg_gigs`, a re-post gets a
    new id), so a leg's gig at minute m is the last gig posted for it no later than m;
    gig_booked books a gig, gig_dropped and no_show unbook it. A quote is pending from
    its request until the dealer decides (order_won / order_lost) or its respondBy
    passes; only quoted requests hold a place, as in the intake.
    """
    leg_gigs = defaultdict(list)  # (order id, leg) -> [(postedAt, gigId)], the posts in order
    for gig in snapshot["gigs"]:
        for stop in gig["stops"]:
            if stop["kind"] == "pickup":
                leg_gigs[(stop["orderId"], stop["leg"])].append((gig["postedAt"], gig["id"]))
    for posts in leg_gigs.values():
        posts.sort()
    orders = {}  # id -> [legs, delivered legs, cancelled]
    booked = set()
    pending = {}  # request id -> respondBy
    decided = set()
    out = {}

    def held(at: int) -> int:
        count = 0
        for oid, (legs, done, cancelled) in orders.items():
            if cancelled:
                continue
            for leg in range(legs):
                if leg in done:
                    continue
                posts = leg_gigs.get((oid, leg), [])
                gig = next((gid for posted, gid in reversed(posts) if posted <= at), None)
                if gig is None or gig not in booked:
                    count += 1
                    break
        return count

    for event in events:
        kind, at = event["kind"], event["at"]
        if kind == "price_request":
            request = event["request"]
            out[request["id"]] = (at, held(at), sum(
                1 for rid, end in pending.items() if rid not in decided and end > at))
            if quoted is None or request["id"] in quoted:
                pending[request["id"]] = request["respondBy"]
        elif kind == "order_won":
            order = event["order"]
            orders[order["id"]] = [len(order["legs"]), set(), False]
            decided.add(order["id"])
            pending.pop(order["id"], None)
        elif kind == "order_lost":
            decided.add(event["requestId"])
            pending.pop(event["requestId"], None)
        elif kind == "gig_booked":
            booked.add(event["gigId"])
        elif kind in ("gig_dropped", "no_show"):
            booked.discard(event["gigId"])
        elif kind in ("delivered", "release"):  # a release: the dealer gave a leg up, it will never be delivered
            oid = event["orderId"]
            if oid in orders:
                orders[oid][1].add(event["leg"])
        elif kind == "order_cancelled":
            oid = event["orderId"]
            if oid in orders:
                orders[oid][2] = True
            pending.pop(oid, None)
    return out


def analyse(dirpath: str) -> None:
    events, reveal, snapshot = load(dirpath)
    quoted = {r["request"]["id"] for r in reveal["requests"] if r["quote"]}
    state = unbooked_at_requests(events, snapshot, quoted)

    rows = []
    for r in reveal["requests"]:
        req = r["request"]
        quote = r["quote"] or {}
        lists = {o["kind"]: o["listPriceCents"] for o in req["options"]}
        declined = bool(quote) and all(
            k in lists and q == lists[k] * DECLINE_FACTOR for k, q in quote.items())
        ratios = [q / lists[k] for k, q in quote.items() if q is not None and k in lists]
        at, held, pend = state[req["id"]]
        limit = 45 if at % DAY < 720 else 35
        rows.append({
            "id": req["id"], "at": at, "held": held, "pend": pend, "limit": limit,
            "waiting": held / limit, "q_wait": held / 35,  # the quoter's own waiting
            "won": r["outcome"] == "won", "declined": declined,
            "min_ratio": None if declined else (min(ratios) if ratios else None),
        })

    n, wins = len(rows), sum(r["won"] for r in rows)
    declines = [r for r in rows if r["declined"]]
    limit_decl = [r for r in declines if r["held"] + r["pend"] >= r["limit"]]
    print(f"{n} requests, {wins} won ({wins / n:.1%}), {len(declines)} declined by the intake "
          f"({len(limit_decl)} of them at or over the queue limit)\n")

    head = (f"{'waiting':<10}{'requests':>9}{'won':>6}{'win rate':>10}"
            f"{'mean quote/list':>17}{'declined':>10}{'>2.5x quoted':>13}{'mean unbooked':>14}")

    def bucket_table(wait_key: str, title: str) -> None:
        print(title)
        print(head)
        for lo, hi in BUCKETS:
            g = [r for r in rows if lo <= r[wait_key] < hi]
            if not g:
                continue
            w = sum(r["won"] for r in g)
            ratios = [r["min_ratio"] for r in g if r["min_ratio"] is not None]
            hi_txt = f"{hi:g}" if hi < 9 else ""
            print(f"{lo:g}-{hi_txt:<10}{len(g):>9}{w:>6}{w / len(g):>10.1%}"
                  f"{(sum(ratios) / len(ratios)) if ratios else float('nan'):>17.3f}"
                  f"{sum(r['declined'] for r in g):>10}"
                  f"{sum(r['min_ratio'] is not None and r['min_ratio'] > 2.5 for r in g):>13}"
                  f"{sum(r['held'] for r in g) / len(g):>14.1f}")
        print()

    bucket_table("waiting", "waiting = unbooked / intake limit (45 before noon, 35 after)")
    bucket_table("q_wait", "quoter's waiting = unbooked / 35 (what the queue charge uses, all day)")

    print(f"declines: {len(declines)} in all; at/over the limit (unbooked + pending >= limit): "
          f"{len(limit_decl)}, on {sorted({r['at'] // DAY for r in limit_decl})}; "
          f"the other {len(declines) - len(limit_decl)} failed the slack screen")
    over = [r for r in rows if not r["declined"] and r["held"] + r["pend"] >= r["limit"]]
    print(f"over the limit but quoted through (the safe-car screen): {len(over)}\n")

    # A line per 4 world hours, with the Wednesday 16-20h window marked.
    print("per 4 world hours (requests arrive 08:00-18:00)")
    print(f"{'window':<12}{'requests':>9}{'won':>6}{'win rate':>10}{'mean waiting':>14}"
          f"{'mean quote/list':>17}{'declined':>10}")
    bins = defaultdict(list)
    for r in rows:
        bins[(r["at"] // DAY, r["at"] % DAY // 240)].append(r)
    for (day, slot), g in sorted(bins.items()):
        w = sum(r["won"] for r in g)
        ratios = [r["min_ratio"] for r in g if r["min_ratio"] is not None]
        mark = "  <<< Wednesday 16-20h" if (day, slot) == (2, 4) else ""
        print(f"{WEEKDAYS[day]} {slot * 4:02g}-{slot * 4 + 4:02g}h"
              f"{len(g):>9}{w:>6}{w / len(g):>10.1%}{sum(r['waiting'] for r in g) / len(g):>14.2f}"
              f"{(sum(ratios) / len(ratios)) if ratios else float('nan'):>17.3f}"
              f"{sum(r['declined'] for r in g):>10}{mark}")

    # The Wednesday window itself, on wins (decisions run to 18:15).
    wed = [e for e in events if e["kind"] == "order_won" and 2 * DAY + 960 <= e["at"] < 2 * DAY + 1200]
    reqs = [r for r in rows if 2 * DAY + 960 <= r["at"] < 2 * DAY + 1080]
    genuine = [r for r in reqs if r["min_ratio"] is not None]
    print(f"\norders won Wed 16:00-20:00: {len(wed)}")
    print(f"requests Wed 16:00-18:00: {len(reqs)}, won {sum(r['won'] for r in reqs)}, "
          f"declined {sum(r['declined'] for r in reqs)}, mean waiting "
          f"{sum(r['waiting'] for r in reqs) / len(reqs):.2f}, mean unbooked "
          f"{sum(r['held'] for r in reqs) / len(reqs):.1f}")
    print(f"genuine quotes among them: {len(genuine)}, mean quote/list "
          f"{sum(r['min_ratio'] for r in genuine) / len(genuine):.2f}, "
          f"won {sum(r['won'] for r in genuine)}")


if __name__ == "__main__":
    analyse(sys.argv[1] if len(sys.argv) > 1 else find_dir("final-1800"))
