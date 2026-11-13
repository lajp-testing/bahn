"""Builds the delivery-town level offsets for ProfitQuoter, from the six scans.

For each first-option request in every scan, the leftover is its switching ratio
minus the mean ratio of its world and day (as structure.py computes it). For each
delivery town the mean leftover m and the count n give the shrunk offset
m * n / (n + 30). Prints the table and writes dispatch/towns.py.

Run locally: python3 tracks/t2/towns.py
"""
import json
import sys
from collections import defaultdict
from pathlib import Path

TRACK = Path(__file__).resolve().parent
DISPATCH = TRACK.parent.parent / "dispatch"


def rows():
    """First-option scan rows with a switching ratio and the day-leftover attached."""
    out = []
    for path in sorted(TRACK.glob("scan-t2-scan-*-l8.jsonl")):
        for line in path.open():
            r = json.loads(line)
            if r["switch_high"] == 0:
                continue
            r["ratio"] = (r["switch_low"] + r["switch_high"]) / 2
            r["day"] = r["arrival"] // 1440
            if r["option"] != r["request"]["options"][0]["kind"]:
                continue
            out.append(r)
    return out


def main():
    first = rows()
    day_mean = defaultdict(list)
    for r in first:
        day_mean[(r["seed"], r["day"])].append(r["ratio"])
    day_mean = {k: sum(v) / len(v) for k, v in day_mean.items()}
    vals = defaultdict(list)
    for r in first:
        vals[r["delivery_town"]].append(r["ratio"] - day_mean[(r["seed"], r["day"])])
    print(f"{'town':<14} {'n':>5} {'mean':>7} {'offset':>7}")
    table = {}
    for town, v in sorted(vals.items()):
        m = sum(v) / len(v)
        table[town] = round(m * len(v) / (len(v) + 30), 4)
        print(f"{town:<14} {len(v):>5} {m:>+7.3f} {table[town]:>+7.4f}")
    body = ", ".join(f'"{t}": {o}' for t, o in sorted(table.items()))
    text = (
        '"""The lane part of a dealer\'s switching price: a level offset per delivery town.\n'
        "\n"
        "Made by tracks/t2/towns.py from the six level 8 scans: for each first-option request the\n"
        "switching ratio minus its world-and-day mean, then per delivery town the mean leftover\n"
        "shrunk by n / (n + 30). The same leftover appears in every scanned world (FINDINGS.md).\n"
        '"""\n'
        "DELIVERY = {" + body + "}\n"
    )
    if "--write" in sys.argv:
        (DISPATCH / "towns.py").write_text(text)
        print(f"\nwrote {DISPATCH / 'towns.py'}")
    else:
        print("\n(dry run; pass --write to write dispatch/towns.py)")


if __name__ == "__main__":
    main()
