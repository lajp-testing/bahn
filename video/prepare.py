"""Turn the demo's real week (the Saturday 18:00 test final) into the video's compact data.

Reads ../demo/assets/{map,week,decisions}.json; writes src/data/week.json. Standard library only.
Run: python3 prepare.py
"""
import json, math, os

HERE = os.path.dirname(os.path.abspath(__file__))
A = os.path.join(HERE, "..", "demo", "assets")
load = lambda f: json.load(open(os.path.join(A, f)))
m, w, dec = load("map.json"), load("week.json"), load("decisions.json")

K = math.cos(math.radians(64.5))
S = 92.0  # px per degree of latitude
LON0, LAT0 = 19.3, 70.2
def P(lat, lon):
    return [round((lon - LON0) * K * S, 1), round((LAT0 - lat) * S, 1)]

border = []
for ring in m["border"]:
    pts = [P(a, b) for a, b in ring]
    if len(pts) < 3:
        continue
    border.append(pts)
places = {p["id"]: dict(name=p["name"], xy=P(p["lat"], p["lon"])) for p in m["places"]}

moves = [dict(pu=mv["pu"], de=mv["de"], late=mv["late"],
              path=[P(a, b) for a, b in mv["path"]]) for mv in w["moves"]]
reqs = [[r["at"], places[r["p"]]["xy"]] for r in w["requests"] if r["p"] in places]
won = sorted(t for t, _ in w["won"])
led = sorted((t, c) for t, _, c, _ in w["ledger"])
cum, s = [], 0
for t, c in led:
    s += c
    cum.append([t, s])
last = {}
for mv in w["moves"]:
    last[mv["rid"]] = max(last.get(mv["rid"], 0), mv["de"])
delivered = sorted(last.values())

r13 = dec["R00013"]
t13 = r13["terms"]["next_day"]
out = dict(border=border, places=places, moves=moves, requests=reqs, won=won, margin=cum,
           delivered=delivered, late=len(w["lateOrders"]),
           r13=dict(km=r13["km"], typical=r13["typical"], terms=t13, at=r13["at"], fee=r13["money"]["fees"]))
json.dump(out, open(os.path.join(HERE, "src", "data", "week.json"), "w"), separators=(",", ":"))
xs = [p[0] for r in border for p in r]; ys = [p[1] for r in border for p in r]
print("border bbox", min(xs), max(xs), min(ys), max(ys), "moves", len(moves), "reqs", len(reqs),
      "margin end", cum[-1], "delivered", len(delivered))

# the final's code (b89-main) on the 40 unseen worlds rob-21..60, one row per week; and the deck's numbers
RUNS = "/home/agent/.t3/projects/bahn/data/runs.jsonl"
weeks = {}
for line in open(RUNS):
    r = json.loads(line)
    if r.get("label") == "b89-main" and not r.get("board"):
        weeks[r["seed"]] = [r["seed"], round(r["marginCents"] / 100), round(r["onTimeShare"] * 100, 1), r["wonOrders"], r["ranked"]]
unseen = sorted(weeks.values(), key=lambda x: x[0])
nums = json.load(open(os.path.join(HERE, "..", "docs", "deck", "numbers.json")))
json.dump(dict(unseen=unseen, steps=nums["steps"], flood=nums["flood_on_time"], sameday=nums["sameday_vs_b37_30wk"],
               testfinal=nums["testfinal"]),
          open(os.path.join(HERE, "src", "data", "numbers.json"), "w"), indent=1)
print("unseen", len(unseen), "ranked", sum(1 for u in unseen if u[4]), "mean on time", round(sum(u[2] for u in unseen) / len(unseen), 2),
      "min", min(u[2] for u in unseen), "mean margin", round(sum(u[1] for u in unseen) / len(unseen)))
