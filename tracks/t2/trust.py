"""Step 3b: does each counted order really add about 1% to the share we win?

For every really-quoted request in a label's saved weeks (the reveal holds our prices and
the outcome; declined 4x quotes are skipped), rebuilds the dealer's trust count at the
moment we quoted from the events, and tabulates the win share by count band (0, 1-9,
10-24, 25) inside effective-ratio bands (lowest quoted price / list, divided by the
dealer's trust factor 1 + 0.01 * count), for D01 and for all other dealers.
Run: python3 tracks/t2/trust.py <label>
"""
import gzip
import json
import sys
from pathlib import Path

RUNS = Path("/home/agent/.t3/projects/bahn/data/runs")
TRUST = 1.0  # the mainline's trust scale: the factor is 1 + 0.01 * TRUST * count
RATIO_BANDS = [(1.0, 1.2), (1.2, 1.4), (1.4, 1.6), (1.6, 99.0)]
COUNT_BANDS = [(0, 0), (1, 9), (10, 24), (25, 25)]


def counts_at_quote(folder):
    """request id -> (dealer, the dealer's counted orders when the request arrived)."""
    counts, open_orders, before, seen = {}, {}, {}, {}
    for line in gzip.open(folder / "events.jsonl.gz", "rt", encoding="utf-8"):
        e = json.loads(line)
        k = e["kind"]
        if k == "price_request":
            req = e["request"]
            seen[req["id"]] = (req["dealerId"], counts.get(req["dealerId"], 0))
        elif k == "order_won":
            open_orders[e["order"]["id"]] = e["order"]["dealerId"]
        elif k == "order_cancelled":
            open_orders.pop(e.get("orderId"), None)
        elif k == "ledger":
            l, order = e["line"], e["line"].get("orderId")
            if l["kind"] == "revenue" and order in open_orders:
                dealer = open_orders.pop(order)
                before[order] = (dealer, counts.get(dealer, 0))
                counts[dealer] = min(25, counts.get(dealer, 0) + 1)
            elif l["kind"] == "late_refund" and order in before:
                dealer, was = before.pop(order)
                counts[dealer] = was // 2
    return seen


def main():
    label = sys.argv[1]
    rows = []
    for folder in sorted(RUNS.iterdir()):
        result = folder / "result.json"
        if not result.exists():
            continue
        meta = json.loads(result.read_text())
        if meta.get("label") != label or meta.get("level") != 8:
            continue
        seen = counts_at_quote(folder)
        reveal = json.load(gzip.open(folder / "reveal.json.gz", "rt", encoding="utf-8"))
        for entry in reveal["requests"]:
            req, quote = entry["request"], entry.get("quote") or {}
            if req["id"] not in seen or not quote:
                continue
            lists = {o["kind"]: o["listPriceCents"] for o in req["options"]}
            cents = [c for k, c in quote.items() if k in lists]
            if not cents:
                continue
            ratio = min(cents) / min(lists.values())
            if ratio > 4:
                continue  # the intake declined this request
            dealer, count = seen[req["id"]]
            rows.append({"dealer": dealer, "count": count,
                         "ratio": ratio / (1 + 0.01 * TRUST * count),
                         "won": 1 if entry.get("outcome") == "won" else 0})
    print(f"{len(rows)} really-quoted requests in {label}")
    for who in ("D01", "other"):
        sub = [r for r in rows if (r["dealer"] == "D01") == (who == "D01")]
        print(f"\n## {who} ({len(sub)} requests): win share by count band inside ratio bands")
        print("| count | " + " | ".join(f"{a}-{b if b < 90 else ''} ratio" for a, b in RATIO_BANDS) + " | all |")
        print("|---|" + "---:|" * (len(RATIO_BANDS) + 1))
        for lo, hi in COUNT_BANDS:
            cells = []
            for a, b in RATIO_BANDS:
                band = [r for r in sub if lo <= r["count"] <= hi and a <= r["ratio"] < b]
                cells.append(f"{sum(r['won'] for r in band)}/{len(band)} ({sum(r['won'] for r in band)/len(band):.2f})" if band else "-")
            band = [r for r in sub if lo <= r["count"] <= hi]
            cells.append(f"{sum(r['won'] for r in band)}/{len(band)} ({sum(r['won'] for r in band)/len(band):.2f})" if band else "-")
            print(f"| {lo}-{hi} | " + " | ".join(cells) + " |")


if __name__ == "__main__":
    main()
