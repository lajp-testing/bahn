/* Spread demo — plain JS, no dependencies. All data is local JSON recorded from the
   18:00 test final; every view is a pure function of the data (and of the chosen
   minute on the map), so scrubbing backwards is exact. Design: demo/DESIGN.md. */
"use strict";

const DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun", "Mon", "Tue", "Wed"];
const END = 14280;            // the world ends Wed 22:00, minute 14280
const OPEN_MIN = 570;         // the page opens at Mon 09:30, with the first cars moving
const APPROX = "approximate: the desk replay in prepare.py could not reproduce this "
  + "request's quote to the cent (72% of the week it does; see README)";
const EXACTT = "exact: the desk replay reproduces this request's quote to the cent with "
  + "the settings that played the week";

let MAP, WEEK, DEC, STORY, RACE, SETTINGS;
let nameOf = {};   // place id -> name
let proj;          // lat/lon -> map x/y

const $ = (sel) => document.querySelector(sel);
const svgNS = "http://www.w3.org/2000/svg";
function svgEl(tag, attrs) {
  const el = document.createElementNS(svgNS, tag);
  for (const k in attrs) el.setAttribute(k, attrs[k]);
  return el;
}
function fmtEur(cents) {
  const e = (cents || 0) / 100;
  return "€" + e.toLocaleString("en-GB", { minimumFractionDigits: e % 1 ? 2 : 0, maximumFractionDigits: 2 });
}
function clockStr(min) {
  const day = Math.floor(min / 1440), m = min % 1440;
  return `${DAYS[Math.min(day, 9)]} ${String(Math.floor(m / 60)).padStart(2, "0")}:${String(m % 60).padStart(2, "0")}`;
}
function hhmm(min) { return clockStr(min).slice(4); }
function bisect(arr, t) { // count of rows with row[0] <= t
  let lo = 0, hi = arr.length;
  while (lo < hi) { const mid = (lo + hi) >> 1; if (arr[mid][0] <= t) lo = mid + 1; else hi = mid; }
  return lo;
}
const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

async function load() {
  [MAP, WEEK, DEC, STORY, RACE, SETTINGS] = await Promise.all(
    ["map", "week", "decisions", "story", "race", "settings"].map((n) =>
      fetch(`assets/${n}.json`).then((r) => r.json())));
  WEEK.reqMap = {}; WEEK.requests.forEach((r) => WEEK.reqMap[r.id] = r);
  MAP.places.forEach((p) => nameOf[p.id] = p.name);
  const hash = location.hash.slice(1).split("@");
  showTab(hash[0] && document.getElementById("tab-" + hash[0]) ? hash[0] : "week");
  buildChallenge();
  buildWeek();
  buildDecision();
  buildSystem();
  buildRace();
  if (hash[1]) setTime(+hash[1]);
}

/* ============================== header + tabs ============================== */

document.querySelectorAll("nav button").forEach((b) => b.addEventListener("click", () => showTab(b.dataset.tab)));
function showTab(tab) {
  document.querySelectorAll("nav button").forEach((b) => b.classList.toggle("on", b.dataset.tab === tab));
  document.querySelectorAll("main").forEach((m) => m.classList.toggle("on", m.id === "tab-" + tab));
}
document.querySelectorAll("[data-goto]").forEach((a) =>
  a.addEventListener("click", (e) => { e.preventDefault(); showTab(a.dataset.goto); }));

/* ============================== challenge ============================== */

function buildChallenge() {
  $("#steps").innerHTML = STORY.challenge.steps.map((s, i) =>
    `<div class="stepcard"><div class="n">${i + 1}</div><div><h4>${s.title}</h4><p>${s.text}</p></div></div>`).join("");
  $("#words").innerHTML = STORY.challenge.words.map(([w, d]) => `<dt>${w}</dt><dd>${d}</dd>`).join("");
  // the flow of a request, drawn as a road with eight stops
  const stops = [
    ["Dealer", "sends a request"], ["Our desk", "reads the note, prices each option"],
    ["Quote", "one price per option"], ["Dealer", "picks us or the competitor"],
    ["Order", "won, with a deadline"], ["Gig", "posted with a fee"],
    ["Driver", "books, drives"], ["Delivered", "on time = margin"],
  ];
  const W = 1150, H = 190, xs = stops.map((_, i) => 70 + i * (W - 140) / (stops.length - 1));
  const y = (x) => 105 + 26 * Math.sin((x / W) * Math.PI * 2.2);   // a gentle road curve
  let d = `M ${xs[0]},${y(xs[0])}`;
  xs.forEach((x, i) => { if (i) d += ` C ${xs[i-1]+55},${y(xs[i-1])} ${x-55},${y(x)} ${x},${y(x)}`; });
  const svg = svgEl("svg", { viewBox: `0 0 ${W} ${H}` });
  svg.appendChild(svgEl("path", { d, fill: "none", stroke: "#33465E", "stroke-width": 3, "stroke-dasharray": "1 7", "stroke-linecap": "round" }));
  stops.forEach(([t, s], i) => {
    const x = xs[i], yy = y(x), up = i % 2 === 0;
    svg.appendChild(svgEl("circle", { cx: x, cy: yy, r: 7, class: "stop" + (i === 7 ? " hot" : "") }));
    const ty = up ? 38 : 168;   // two quiet label bands, clear of the road
    const tx = svgEl("text", { x, y: ty, "text-anchor": "middle" });
    tx.innerHTML = `<tspan font-weight="600" fill="#EFE9DC">${t}</tspan><tspan x="${x}" dy="16" font-size="12" fill="#8FA6BE">${s}</tspan>`;
    svg.appendChild(svgEl("line", { x1: x, y1: yy + (up ? -8 : 8), x2: x, y2: ty + (up ? 10 : -20),
      stroke: "#33465E", "stroke-width": 1 }));
    svg.appendChild(tx);
  });
  $("#flow").innerHTML = "";
  $("#flow").appendChild(svg);
}

/* ============================== the week: map ============================== */

// equirectangular projection in km, covering the whole country
function makeProjection() {
  const LAT0 = 59.6, LAT1 = 70.4, LON0 = 20.3, LON1 = 31.9;
  const kmLat = 111, kmLon = 111 * Math.cos(65 * Math.PI / 180);
  const W = (LON1 - LON0) * kmLon, H = (LAT1 - LAT0) * kmLat;
  return { f: (lat, lon) => [(lon - LON0) * kmLon, (LAT1 - lat) * kmLat], W, H };
}
function ll(id) { const q = MAP.places.find((x) => x.id === id); return [q.lat, q.lon]; }

const MINOR = new Set(["espoo", "vantaa", "raisio", "lempaala", "porvoo", "salo", "rauma", "hyvinkaa", "kouvola", "ylivieska"]);

const week = {
  t: OPEN_MIN, playing: false, speed: 60, last: 0,
  reqByAt: [], wonByAt: [], lostByAt: [], ledgerCum: [], feed: [], feedAt: [],
  eventMinutes: [], orderDoneAt: [], orderDone: [],
  ridGid: {}, usedEdges: new Set(), seg: new Map(), g: null,
  view: null, hl: null, townG: null,
};

function buildWeek() {
  proj = makeProjection();
  week.view = { x: 0, y: 0, w: proj.W, h: proj.H };
  week.reqByAt = WEEK.requests.map((r) => [r.at, r]).sort((a, b) => a[0] - b[0]);
  week.wonByAt = WEEK.won.slice().sort((a, b) => a[0] - b[0]);
  week.lostByAt = WEEK.lost.slice().sort((a, b) => a[0] - b[0]);
  let cum = 0;
  week.ledgerCum = WEEK.ledger.map(([at, , cents]) => { cum += cents; return [at, cum]; });
  const legs = {}, done = {};
  WEEK.moves.forEach((m) => { legs[m.rid] = (legs[m.rid] || 0) + 1; });
  WEEK.moves.forEach((m) => { if (m.de != null) done[m.rid] = Math.max(done[m.rid] || 0, m.de); });
  const nLegs = {}; WEEK.requests.forEach((r) => nLegs[r.id] = r.n);
  week.orderDone = [];
  for (const [rid, de] of Object.entries(done)) {
    if (legs[rid] !== nLegs[rid]) continue;
    const late = WEEK.moves.some((m) => m.rid === rid && m.late);
    week.orderDone.push([de, late ? 0 : 1, rid]);
  }
  week.orderDone.sort((a, b) => a[0] - b[0]);
  week.orderDoneAt = week.orderDone.map((r) => [r[0]]);
  WEEK.moves.forEach((m, i) => {
    week.ridGid[m.rid] = m.gid;
    const pts = m.path.map((p) => proj.f(p[0], p[1])), cs = [0];
    for (let k = 1; k < pts.length; k++)
      cs.push(cs[k - 1] + Math.hypot(pts[k][0] - pts[k - 1][0], pts[k][1] - pts[k - 1][1]));
    week.seg.set(i, { pts, cs, total: cs[cs.length - 1] });
    for (let k = 1; k < m.path.length; k++) {
      const a = m.path[k - 1], b = m.path[k];
      week.usedEdges.add(a < b ? a + "|" + b : b + "|" + a);
    }
  });
  const feed = [];
  WEEK.requests.forEach((r) => feed.push({ at: r.at, kind: "req", rid: r.id }));
  WEEK.won.forEach(([at, rid]) => feed.push({ at, kind: "won", rid }));
  WEEK.lost.forEach(([at, rid]) => feed.push({ at, kind: "lost", rid }));
  WEEK.posts.forEach(([at, gid]) => feed.push({ at, kind: "post", gid }));
  WEEK.bookings.forEach(([at, gid, fee]) => feed.push({ at, kind: "book", gid, fee }));
  WEEK.drops.forEach(([at, gid]) => feed.push({ at, kind: "drop", gid }));
  WEEK.moves.forEach((m) => {
    feed.push({ at: m.pu, kind: "pick", m, rid: m.rid });
    if (m.de != null) feed.push({ at: m.de, kind: "del", m, rid: m.rid });
  });
  feed.sort((a, b) => a.at - b.at || (a.kind < b.kind ? -1 : 1));
  week.feed = feed;
  week.feedAt = feed.map((e) => [e.at]);
  week.eventMinutes = [...new Set(feed.map((e) => e.at))];
  drawMapBase();
  buildTimeline();
  wireControls();
  setTime(OPEN_MIN);
  if (!localStorage.getItem("spread-demo-hint")) $("#hint").hidden = false;
}

function u(px) {  // screen px -> map units, under preserveAspectRatio "meet"
  const svg = $("#map");
  const s = Math.min(svg.clientWidth / week.view.w, svg.clientHeight / week.view.h);
  return px / s;
}

function drawMapBase() {
  const svg = $("#map");
  svg.setAttribute("viewBox", `0 0 ${proj.W} ${proj.H}`);
  const mk = (cls) => { const g = svgEl("g", { class: cls }); svg.appendChild(g); return g; };
  const gOutline = mk("outline"), gAtmos = mk("atmos"), gRoads = mk("roads");
  const routes = mk("routes"), markers = mk("markers"), cars = mk("cars");
  week.g = { routes, markers, cars };
  week.townG = mk("towns");
  // graticule: the map's own grid, every 2 degrees
  for (let lat = 60; lat <= 70; lat += 2) {
    const a = proj.f(lat, 20.3), b = proj.f(lat, 31.9);
    gAtmos.appendChild(svgEl("line", { x1: a[0], y1: a[1], x2: b[0], y2: b[1],
      stroke: "#1B2E47", "stroke-width": 1, opacity: .6, "vector-effect": "non-scaling-stroke" }));
  }
  for (let lon = 22; lon <= 30; lon += 2) {
    const a = proj.f(59.6, lon), b = proj.f(70.4, lon);
    gAtmos.appendChild(svgEl("line", { x1: a[0], y1: a[1], x2: b[0], y2: b[1],
      stroke: "#1B2E47", "stroke-width": 1, opacity: .6, "vector-effect": "non-scaling-stroke" }));
  }
  gOutline.appendChild(svgEl("polygon", {
    points: MAP.outline.map((p) => proj.f(p[0], p[1])).map((p) => p.join(",")).join(" "),
    fill: "#142A44", stroke: "#33608C", "stroke-width": 1.5, opacity: .9, "vector-effect": "non-scaling-stroke" }));
  const place = {}; MAP.places.forEach((p) => place[p.id] = p);
  MAP.roads.forEach(([a, b, km]) => {
    const used = week.usedEdges.has(a < b ? a + "|" + b : b + "|" + a);
    if (!used && km > 170) return;
    const p = proj.f(place[a].lat, place[a].lon), q = proj.f(place[b].lat, place[b].lon);
    gRoads.appendChild(svgEl("line", { x1: p[0], y1: p[1], x2: q[0], y2: q[1],
      stroke: used ? "#44608F" : "#2E4560", "stroke-width": used ? 1.8 : 1.3, opacity: used ? .85 : .55,
      "vector-effect": "non-scaling-stroke" }));
  });
  layoutTowns();
}

function layoutTowns() {
  // towns and labels, sized to stay readable at any zoom; minor labels only when zoomed in
  const g = week.townG;
  g.textContent = "";
  const zoomed = week.view.w < proj.W * 0.55;
  MAP.places.forEach((p) => {
    const [x, y] = proj.f(p.lat, p.lon);
    const minor = MINOR.has(p.id);
    if (minor && !zoomed) {
      g.appendChild(svgEl("circle", { cx: x, cy: y, r: u(minor ? 3.5 : 4.5), fill: "#7D97C2" }));
      return;
    }
    g.appendChild(svgEl("circle", { cx: x, cy: y, r: u(minor ? 4 : 5.5), fill: "#93AECB" }));
    const t = svgEl("text", { x: x + u(9), y: y + u(4), "font-size": u(minor ? 12 : 14), class: minor ? "" : "major" });
    t.textContent = p.name;
    g.appendChild(t);
  });
}

function applyView() {
  $("#map").setAttribute("viewBox", `${week.view.x} ${week.view.y} ${week.view.w} ${week.view.h}`);
  layoutTowns();
}
function clientToMap(e) {
  const svg = $("#map"), r = svg.getBoundingClientRect();
  const v = week.view;
  return [v.x + (e.clientX - r.left) / r.width * v.w, v.y + (e.clientY - r.top) / r.height * v.h];
}
function zoomAt(factor, cx, cy) {
  const v = week.view;
  const w = Math.min(proj.W, Math.max(proj.W / 12, v.w * factor));
  const h = w * proj.H / proj.W;
  v.x = Math.min(proj.W - w, Math.max(0, cx - (cx - v.x) * w / v.w));
  v.y = Math.min(proj.H - h, Math.max(0, cy - (cy - v.y) * h / v.h));
  v.w, v.h = w, h;
  applyView();
}

function posOnPath(i, frac) {
  const { pts, cs, total } = week.seg.get(i);
  const d = frac * total;
  let k = 1;
  while (k < cs.length && cs[k] < d) k++;
  const f = (d - cs[k - 1]) / Math.max(1e-9, cs[k] - cs[k - 1]);
  return [pts[k - 1][0] + (pts[k][0] - pts[k - 1][0]) * f, pts[k - 1][1] + (pts[k][1] - pts[k - 1][1]) * f];
}
function pathD(i) { return week.seg.get(i).pts.map((p) => p.join(",")).join(" "); }

/* ============================== the week: render ============================== */

function setTime(t) {
  week.t = Math.max(0, Math.min(END, Math.round(t)));
  renderWeek();
}

function renderWeek() {
  const t = week.t;
  $("#clock").textContent = clockStr(t);
  const g = week.g;
  g.routes.textContent = ""; g.markers.textContent = ""; g.cars.textContent = "";

  const nReq = bisect(week.reqByAt, t);
  for (let i = nReq - 1; i >= 0 && week.reqByAt[i][0] > t - 25; i--) {
    const r = week.reqByAt[i][1], age = t - r.at, p = proj.f(...ll(r.p));
    const c = svgEl("circle", { cx: p[0], cy: p[1], r: u(9) + age * u(.5), fill: "none",
      stroke: "#F0A532", "stroke-width": 2, opacity: .9 * (1 - age / 25), "vector-effect": "non-scaling-stroke",
      "pointer-events": "all" });
    c.style.cursor = "pointer";
    c.addEventListener("click", () => { if (!week.dragged) openRequest(r.id); });
    g.markers.appendChild(c);
  }
  const nLost = bisect(week.lostByAt, t);
  for (let i = nLost - 1; i >= 0 && week.lostByAt[i][0] > t - 15; i--) {
    const p = proj.f(...ll(WEEK.reqMap[week.lostByAt[i][1]].p));
    g.markers.appendChild(svgEl("circle", { cx: p[0], cy: p[1], r: u(5), fill: "#5C7188",
      opacity: .7 * (1 - (t - week.lostByAt[i][0]) / 15) }));
  }
  const nWon = bisect(week.wonByAt, t);
  const wonSet = new Set();
  for (let i = 0; i < nWon; i++) wonSet.add(week.wonByAt[i][1]);
  let moving = 0, carsDone = 0;
  WEEK.moves.forEach((m, i) => {
    if (m.pu > t) return;
    const de = m.de == null ? END : m.de;
    if (m.de != null && m.de <= t) {
      carsDone++;
      const age = t - m.de;
      if (m.late) {
        g.routes.appendChild(svgEl("polyline", { points: pathD(i), fill: "none",
          stroke: "#EF6D6D", "stroke-width": 1.6, opacity: .55, "stroke-dasharray": "6 5",
          "vector-effect": "non-scaling-stroke" }));
        if (age < 360) {
          const p = posOnPath(i, 1);
          g.cars.appendChild(svgEl("circle", { cx: p[0], cy: p[1], r: u(7), fill: "#EF6D6D", stroke: "#EFE9DC", "stroke-width": 1.5, opacity: 1 - age / 360 }));
        }
      } else if (age < 150) {
        g.routes.appendChild(svgEl("polyline", { points: pathD(i), fill: "none",
          stroke: "#54C08A", "stroke-width": 1.6, opacity: .4 * (1 - age / 150), "vector-effect": "non-scaling-stroke" }));
      }
      return;
    }
    moving++;
    g.routes.appendChild(svgEl("polyline", { points: pathD(i), fill: "none",
      stroke: m.late ? "#EF6D6D" : "#7FB4E8", "stroke-width": 1.8, opacity: .8, "vector-effect": "non-scaling-stroke" }));
    const p = posOnPath(i, (t - m.pu) / Math.max(1, de - m.pu));
    g.cars.appendChild(svgEl("circle", { cx: p[0], cy: p[1], r: u(5.5), fill: m.late ? "#EF6D6D" : "#7FB4E8",
      stroke: "#0A141F", "stroke-width": 1.5 }));
  });
  WEEK.moves.forEach((m) => {
    if (!wonSet.has(m.rid) || m.pu <= t) return;
    const p = proj.f(...ll(m.p));
    const c = svgEl("circle", { cx: p[0], cy: p[1], r: u(8), fill: "none", stroke: "#54C08A",
      "stroke-width": 2.5, opacity: .85, "vector-effect": "non-scaling-stroke", "pointer-events": "all" });
    c.style.cursor = "pointer";
    c.addEventListener("click", () => { if (!week.dragged) openRequest(m.rid); });
    g.markers.appendChild(c);
  });
  if (week.hl && Date.now() < week.hl.until) {
    g.routes.appendChild(svgEl("polyline", { points: week.hl.pts.map((p) => p.join(",")).join(" "),
      fill: "none", stroke: "#F0A532", "stroke-width": 2.5, "stroke-dasharray": "2 6",
      "stroke-linecap": "round", "vector-effect": "non-scaling-stroke" }));
  } else week.hl = null;

  const k = bisect(week.ledgerCum, t);
  const margin = k ? week.ledgerCum[k - 1][1] : 0;
  $("#cMargin").textContent = fmtEur(margin);
  $("#cReq").textContent = nReq;
  $("#cWon").textContent = nWon;
  $("#cLost").textContent = nLost;
  $("#cMove").textContent = moving;
  $("#cDone").textContent = carsDone;
  const doneOrders = bisect(week.orderDoneAt, t);
  const onTime = week.orderDone.slice(0, doneOrders).filter((r) => r[1]).length;
  $("#cLate").textContent = doneOrders - onTime;
  const share = doneOrders ? onTime / doneOrders : null;
  $("#onTimeFill").style.width = (share == null ? 0 : share * 100) + "%";
  $("#onTimePct").textContent = share == null ? "–" : (share * 100).toFixed(1) + "%";

  const kf = bisect(week.feedAt, t);
  $("#feed").innerHTML = week.feed.slice(Math.max(0, kf - 11), kf).reverse().map(feedLine).join("");
  document.querySelectorAll("#feed li[data-rid]").forEach((li) =>
    li.addEventListener("click", () => openRequest(li.dataset.rid)));
  moveCursor(t);
}

function feedLine(e) {
  const t = `<span class="t">${hhmm(e.at)}</span>`;
  const rid = e.rid ? ` data-rid="${e.rid}"` : "";
  switch (e.kind) {
    case "req": return `<li class="req"${rid}>${t}${e.rid} asks: ${nameOf[WEEK.reqMap[e.rid].p]} to ${nameOf[WEEK.reqMap[e.rid].d]}</li>`;
    case "won": return `<li class="won"${rid}>${t}won ${e.rid} at ${fmtEur(DEC[e.rid]?.won?.price || 0)}</li>`;
    case "lost": return `<li class="lost"${rid}>${t}lost ${e.rid} to the competitor</li>`;
    case "post": return `<li class="post">${t}gig ${e.gid} posted in the app</li>`;
    case "book": return `<li class="book">${t}gig ${e.gid} booked at ${fmtEur(e.fee)}</li>`;
    case "drop": return `<li class="book">${t}gig ${e.gid} dropped by its driver</li>`;
    case "pick": return `<li class="post"${rid}>${t}${e.rid} collected in ${nameOf[e.m.p]}</li>`;
    case "del": return `<li class="${e.m.late ? "late" : "del"}"${rid}>${t}${e.rid} delivered ${e.m.late ? "late" : "on time"} in ${nameOf[e.m.d]}</li>`;
  }
  return "";
}

function openRequest(rid) {
  showTab("decision");
  selectRequest(rid);
}
function showOnMap(rid) {
  const r = WEEK.reqMap[rid];
  showTab("week");
  setTime(r.at);
  const move = WEEK.moves.find((m) => m.rid === rid);
  const pts = move ? week.seg.get(WEEK.moves.indexOf(move)).pts : [proj.f(...ll(r.p)), proj.f(...ll(r.d))];
  week.hl = { pts, until: Date.now() + 12000 };
  renderWeek();
}

/* ============================== the week: timeline ============================== */

function buildTimeline() {
  const svg = $("#tline");
  const W = 1000, H = 96, X = (min) => 8 + min / END * (W - 16);
  svg.setAttribute("viewBox", `0 0 ${W} ${H}`);
  // day bands + labels
  for (let d = 0; d <= 9; d++) {
    const a = Math.min(d * 1440, END), b = Math.min((d + 1) * 1440, END);
    if (a >= END) break;
    if (d % 2 === 1) svg.appendChild(svgEl("rect", { x: X(a), y: 0, width: X(b) - X(a), height: H, fill: "#FFFFFF", opacity: .022 }));
    const t = svgEl("text", { x: X(a) + 5, y: 12, class: "daylab" });
    t.textContent = DAYS[d] + (d > 6 ? " 2" : "");
    t.addEventListener("click", () => setTime(Math.min(d * 1440 + 510, END)));
    svg.appendChild(t);
  }
  // hourly activity: requests (area) and wins (line)
  const hours = Math.ceil(END / 60);
  const reqH = new Array(hours).fill(0), wonH = new Array(hours).fill(0);
  WEEK.requests.forEach((r) => reqH[Math.floor(r.at / 60)]++);
  WEEK.won.forEach(([at]) => wonH[Math.floor(at / 60)]++);
  const mx = Math.max(...reqH);
  const y0 = H - 26;
  let area = `M ${X(0)},${y0}`;
  reqH.forEach((n, h) => area += ` L ${X(h * 60)},${y0 - n / mx * (y0 - 22)}`);
  area += ` L ${X(END)},${y0} Z`;
  svg.appendChild(svgEl("path", { d: area, fill: "#8FA6BE", opacity: .18 }));
  let line = "";
  wonH.forEach((n, h) => { const x = X(h * 60), y = y0 - n / mx * (y0 - 22); line += `${line ? " L" : "M"} ${x},${y}`; });
  svg.appendChild(svgEl("path", { d: line, fill: "none", stroke: "#54C08A", "stroke-width": 1.2, opacity: .8 }));
  // story markers
  const mark = (from, to, color, label) => {
    const band = svgEl("rect", { x: X(from), y: 14, width: X(to) - X(from), height: H - 40, fill: color, opacity: .14, style: "cursor:pointer" });
    band.appendChild(svgEl("title", {})).textContent = label;
    band.addEventListener("click", () => setTime(from));
    svg.appendChild(band);
    const tri = svgEl("path", { d: `M ${X(from)},10 l 4,6 l -8,0 z`, fill: color, style: "cursor:pointer" });
    tri.appendChild(svgEl("title", {})).textContent = label;
    tri.addEventListener("click", () => setTime(from));
    svg.appendChild(tri);
  };
  mark(2880, 3960, "#F0A532", "Wednesday: the price war — the competitor cut prices 20% for the day");
  mark(3600, 3720, "#F0A532", "Wednesday noon: a dealer group sent 30 cars from one yard in Vantaa");
  WEEK.moves.filter((m) => m.late && m.de != null).forEach((m) => {
    const t = svgEl("path", { d: `M ${X(m.de)},${H - 8} l 3,6 l -6,0 z`, fill: "#EF6D6D", style: "cursor:pointer" });
    t.appendChild(svgEl("title", {})).textContent = `${m.rid} delivered late`;
    t.addEventListener("click", () => openRequest(m.rid));
    svg.appendChild(t);
  });
  // the cursor
  week.cursor = svgEl("line", { x1: X(week.t), y1: 0, x2: X(week.t), y2: H - 14, stroke: "#F0A532", "stroke-width": 1.5 });
  svg.appendChild(week.cursor);
  week.tlX = X;
  // drag / click anywhere to scrub
  const scrub = (e) => {
    const r = svg.getBoundingClientRect();
    const min = ((e.clientX - r.left) / r.width * W - 8) / (W - 16) * END;
    setTime(min);
  };
  let down = false;
  svg.addEventListener("pointerdown", (e) => { down = true; svg.setPointerCapture(e.pointerId); scrub(e); });
  svg.addEventListener("pointermove", (e) => { if (down) scrub(e); });
  svg.addEventListener("pointerup", () => { down = false; });
}
function moveCursor(t) {
  if (week.cursor) week.cursor.setAttribute("x1", week.tlX(t)),
    week.cursor.setAttribute("x2", week.tlX(t));
}

/* ============================== the week: controls ============================== */

function wireControls() {
  $("#play").addEventListener("click", togglePlay);
  $("#speed").addEventListener("change", (e) => week.speed = +e.target.value);
  $("#prevEvent").addEventListener("click", () => stepEvent(-1));
  $("#nextEvent").addEventListener("click", () => stepEvent(1));
  $("#prevHour").addEventListener("click", () => setTime(week.t - 60));
  $("#nextHour").addEventListener("click", () => setTime(week.t + 60));
  $("#prevDay").addEventListener("click", () => setTime(week.t - 1440));
  $("#nextDay").addEventListener("click", () => setTime(week.t + 1440));
  $("#hintOk").addEventListener("click", () => { $("#hint").hidden = true; localStorage.setItem("spread-demo-hint", "1"); });
  $("#hintTour").addEventListener("click", () => { $("#hint").hidden = true; localStorage.setItem("spread-demo-hint", "1"); startTour(); });
  $("#tourStart").addEventListener("click", startTour);
  // zoom + pan
  const svg = $("#map");
  svg.addEventListener("wheel", (e) => {
    e.preventDefault();
    const [cx, cy] = clientToMap(e);
    zoomAt(e.deltaY > 0 ? 1.18 : 1 / 1.18, cx, cy);
  }, { passive: false });
  let pan = null;
  svg.addEventListener("pointerdown", (e) => {
    pan = { x: e.clientX, y: e.clientY, view: { ...week.view }, moved: false };
    week.dragged = false;
    svg.setPointerCapture(e.pointerId);
  });
  svg.addEventListener("pointermove", (e) => {
    if (!pan) return;
    const r = svg.getBoundingClientRect();
    const v = pan.view;
    const dx = (e.clientX - pan.x) / r.width * v.w, dy = (e.clientY - pan.y) / r.height * v.h;
    if (Math.abs(e.clientX - pan.x) + Math.abs(e.clientY - pan.y) > 3) { pan.moved = true; week.dragged = true; }
    week.view.x = Math.min(proj.W - v.w, Math.max(0, v.x - dx));
    week.view.y = Math.min(proj.H - v.h, Math.max(0, v.y - dy));
    applyView();
  });
  svg.addEventListener("pointerup", () => { pan = null; });
  $("#zoomIn").addEventListener("click", () => zoomAt(1 / 1.6, week.view.x + week.view.w / 2, week.view.y + week.view.h / 2));
  $("#zoomOut").addEventListener("click", () => zoomAt(1.6, week.view.x + week.view.w / 2, week.view.y + week.view.h / 2));
  $("#zoomReset").addEventListener("click", () => { week.view = { x: 0, y: 0, w: proj.W, h: proj.H }; applyView(); });
  // keyboard
  document.addEventListener("keydown", (e) => {
    if (e.target.closest("input, select, textarea")) return;
    if (!document.getElementById("tab-week").classList.contains("on")) return;
    const day = e.ctrlKey || e.altKey || e.metaKey;
    if (e.key === "ArrowLeft") { e.preventDefault(); setTime(day ? week.t - 1440 : e.shiftKey ? week.t - 60 : stepMinute(-1)); }
    else if (e.key === "ArrowRight") { e.preventDefault(); setTime(day ? week.t + 1440 : e.shiftKey ? week.t + 60 : stepMinute(1)); }
    else if (e.key === " " && e.target === document.body) { e.preventDefault(); togglePlay(); }
  });
  window.addEventListener("resize", layoutTowns);
}

function stepMinute(dir) {
  const t = week.t, ms = week.eventMinutes;
  let next = null;
  if (dir > 0) next = ms.find((m) => m > t);
  else for (let i = ms.length - 1; i >= 0; i--) if (ms[i] < t) { next = ms[i]; break; }
  return next == null ? (dir > 0 ? END : 0) : next;
}
function stepEvent(dir) { setTime(stepMinute(dir)); }

function togglePlay() {
  week.playing = !week.playing;
  $("#play").innerHTML = week.playing ? "&#10074;&#10074; Pause" : "&#9654; Play";
  $("#play").classList.toggle("on", week.playing);
  if (week.playing) { week.last = performance.now(); requestAnimationFrame(tickPlay); }
}
function tickPlay(now) {
  if (!week.playing) return;
  week.t = Math.round(week.t + (now - week.last) / 1000 * week.speed);
  week.last = now;
  if (week.t >= END) { week.t = END; togglePlay(); }
  renderWeek();
  if (week.playing) requestAnimationFrame(tickPlay);
}

/* ============================== the week: guided tour ============================== */

let tour = { steps: [], i: 0 };

function startTour() {
  showTab("week");
  const bundle = WEEK.bookings.filter(([at, gid]) => (WEEK.gigOrders[gid] || []).length > 1)[0];
  const lateMove = WEEK.moves.filter((m) => m.late && m.de != null)
    .sort((a, b) => (b.de - WEEK.deadline[b.rid]) - (a.de - WEEK.deadline[a.rid]))[0];
  const lateMin = Math.round((lateMove.de - WEEK.deadline[lateMove.rid]) / 60);
  const first = WEEK.requests[0];
  tour.steps = [
    { t: 510, title: "Monday, 08:30",
      text: "The desk is open. From 09:00 dealers across Finland will start asking for prices; every amber ring is a request that gives us fifteen minutes to quote." },
    { t: first.at, title: `The first request, ${first.id}`,
      text: `${nameOf[first.p]} to ${nameOf[first.d]}, ${DEC[first.id].km} km. We quoted ${Object.entries(DEC[first.id].quote).map(([k, v]) => `${fmtEur(v)} for ${k.replace(/_/g, " ")}`).join(" and ")} — and lost it to the competitor. A loss teaches the quoter's level to step down.` },
    { t: WEEK.won[0][0], title: `The first win, ${WEEK.won[0][1]}`,
      text: `At ${fmtEur(DEC[WEEK.won[0][1]].won.price)} the dealer chose us. The gig opens at what the cost model expects the car to cost, and a driver books within minutes — watch the blue car leave ${nameOf[WEEK.reqMap[WEEK.won[0][1]].p]}.` },
    { t: bundle[0], title: "A bundle",
      text: `${WEEK.gigOrders[bundle[1]].join(" and ")} share one gig: when two or three cars fit a route, they travel together at 0.85 of the sum of their fees — one trip for the driver, less paid by us.` },
    { t: 2880, title: "Wednesday: the price war",
      text: "Nobody announces it, but today the competitor quotes 20% under its usual prices. We won 23% of Wednesday's requests, against 48% on Thursday — the quoter's level spends the day stepping down." },
    { t: 3620, title: "Wednesday noon: the bulk order",
      text: "A dealer group sends 30 cars from one yard in Vantaa. The intake's queue is near its limit of 35 unbooked orders, so we quote only the cars the flood screen says stay on time. We won 4 of the 30." },
    { t: lateMove.de - 30, rid: lateMove.rid, title: `A late car, ${lateMove.rid}`,
      text: `${lateMin} minutes late: the dealer gets part of its price back and its trust count halves. Ten of our 356 orders ran late; 97.2% arrived on time — above the 90% the ranking demands.` },
    { t: END, title: "The end of the week",
      text: "€17,442.75 of margin, 356 orders, 97.2% on time: 5th of 75 teams. The gap to the top was about 110 short cars — the fee floors priced them out. The fix went in the same evening; it is in the How it works tab." },
  ];
  tour.i = 0;
  $("#hint").hidden = true;
  $("#tourbox").hidden = false;
  showTourStep();
}
function showTourStep() {
  const s = tour.steps[tour.i];
  setTime(s.t);
  $("#tourTitle").textContent = `${s.title}`;
  $("#tourText").textContent = s.text;
  $("#tourStep").textContent = `${tour.i + 1} / ${tour.steps.length}`;
  const btn = $("#tourNext");
  btn.textContent = tour.i === tour.steps.length - 1 ? "Finish" : "Next";
  const insp = $("#tourPrev").parentElement.querySelector(".inspect");
  if (insp) insp.remove();
  if (s.rid) {
    const b = document.createElement("button");
    b.className = "quiet inspect";
    b.textContent = "Inspect " + s.rid;
    b.addEventListener("click", () => { endTour(); openRequest(s.rid); });
    $(".tourctrl").insertBefore(b, $("#tourStep"));
  }
}
function endTour() { $("#tourbox").hidden = true; }

function wireTour() {
  $("#tourNext").addEventListener("click", () => {
    if (tour.i >= tour.steps.length - 1) endTour();
    else { tour.i++; showTourStep(); }
  });
  $("#tourPrev").addEventListener("click", () => { if (tour.i > 0) { tour.i--; showTourStep(); } });
  $("#tourClose").addEventListener("click", endTour);
}

/* ============================== inspect a decision ============================== */

const dec = { filter: "all", search: "", sel: null };

function buildDecision() {
  $("#search").addEventListener("input", (e) => { dec.search = e.target.value.toLowerCase(); renderRows(); });
  $("#filter").addEventListener("change", (e) => { dec.filter = e.target.value; renderRows(); });
  const buckets = [[0, 40], [40, 100], [100, 300], [300, 1e9]];
  const stat = buckets.map(() => [0, 0]);
  WEEK.requests.forEach((r) => {
    const d = DEC[r.id]; if (!d) return;
    const b = buckets.findIndex(([lo, hi]) => d.km >= lo && d.km < hi);
    stat[b][0]++; if (d.won) stat[b][1]++;
  });
  $("#laneStats").innerHTML = "win rate by lane: " + buckets.map(([lo, hi], i) =>
    `${hi < 1e9 ? (lo ? `${lo}–${hi}` : `<${hi}`) : `${lo}+`} km ${stat[i][0] ? Math.round(100 * stat[i][1] / stat[i][0]) : 0}% (${stat[i][1]}/${stat[i][0]})`
  ).join("  ·  ");
  wireTour();
  renderRows();
  const withNote = WEEK.requests.find((r) => r.note && DEC[r.id]?.won);
  if (withNote) selectRequest(withNote.id);
}

function renderRows() {
  const rows = WEEK.requests.filter((r) => {
    const d = DEC[r.id]; if (!d) return false;
    if (dec.filter === "won" && !d.won) return false;
    if (dec.filter === "lost" && !d.lost) return false;
    if (dec.filter === "late" && !(d.won && d.won.delivered && d.won.delivered.some((x) => x != null && x > d.won.deadline))) return false;
    if (dec.filter === "note" && !r.note) return false;
    if (dec.filter === "bundle" && !(d.won && week.ridGid[r.id] && WEEK.gigOrders[week.ridGid[r.id]]?.length > 1)) return false;
    if (dec.search && !(r.id.toLowerCase().includes(dec.search) || r.k.toLowerCase().includes(dec.search)
      || nameOf[r.p].toLowerCase().includes(dec.search) || nameOf[r.d].toLowerCase().includes(dec.search))) return false;
    return true;
  });
  $("#drows").innerHTML = rows.map((r) => {
    const d = DEC[r.id];
    const ratioList = Object.entries(d.quote).map(([k, c]) => c / (r.o.find((o) => o[0] === k)[2]));
    const badge = d.won
      ? (d.won.delivered.some((x) => x != null && x > d.won.deadline) ? `<span class="badge late">late</span>` : `<span class="badge won">won</span>`)
      : d.cancelled ? `<span class="badge cancel">cancelled</span>` : `<span class="badge lost">lost</span>`;
    return `<tr data-r="${r.id}" class="${dec.sel === r.id ? "sel" : ""}">
      <td class="mono">${clockStr(r.at)}</td><td class="mono">${r.id}</td><td>${nameOf[r.p]} to ${nameOf[r.d]}</td>
      <td class="r">${d.km}</td><td class="r mono">&times;${Math.min(...ratioList).toFixed(2)}</td><td>${badge}</td></tr>`;
  }).join("");
  document.querySelectorAll("#drows tr").forEach((tr) =>
    tr.addEventListener("click", () => selectRequest(tr.dataset.r)));
}

function stage(n, title, body, tag) {
  const tagHtml = tag === "exact" ? `<span class="tag exact" title="${EXACTT}">exact</span>`
    : tag === "approx" ? `<span class="tag approx" title="${APPROX}">&approx;</span>` : "";
  return `<div class="stage"><span class="node">${n}</span><h4>${title}${tagHtml}</h4><div class="body">${body}</div></div>`;
}

function selectRequest(rid) {
  dec.sel = rid;
  renderRows();
  const r = WEEK.reqMap[rid], d = DEC[rid];
  const facts = d.noteFacts;
  const floors = SETTINGS.floors;
  let noteBody = `<p>No note — the reader has nothing to read.</p>`;
  if (r.note) {
    const chips = [];
    if (facts.ready != null) chips.push(`<span class="chip">ready from ${clockStr(facts.ready)}</span>`);
    if (facts.deadline != null) chips.push(`<span class="chip">deadline ${clockStr(facts.deadline)}</span>`);
    if (facts.hours) chips.push(`<span class="chip">pickup hours ${facts.hours[0] != null ? hhmm(facts.hours[0]) : ""}–${facts.hours[1] != null ? hhmm(facts.hours[1]) : ""}</span>`);
    if (facts.manual) chips.push(`<span class="chip">manual licence needed</span>`);
    if (facts.plates) chips.push(`<span class="chip">fetch plates</span>`);
    if (!facts.sure) chips.push(`<span class="chip bad">reader unsure</span>`);
    noteBody = `<p class="noteq">&ldquo;${esc(r.note)}&rdquo;</p><div class="chips">${chips.join("") || '<span class="chip">harmless — no constraint</span>'}</div>`;
  }
  const offered = Object.keys(d.quote), all = r.o.map((o) => o[0]);
  const slackChips = all.map((k) => {
    const ok = d.slack[k] != null && d.slack[k] >= 12;
    return `<span class="chip ${offered.includes(k) ? (ok ? "good" : "") : "off"}">${k.replace(/_/g, " ")} · ${d.slack[k] != null ? d.slack[k] + " h slack" : "not offered"}</span>`;
  });
  const declined = offered.length === 1 && Object.values(d.quote)[0] > 4 * r.o[0][2];
  const intakeBody = `
    <div class="chips">${slackChips.join("")}</div>
    <div class="kv"><b>queue</b><span>${d.queue[0]} of ${d.queue[1]} unbooked${d.queue[0] >= d.queue[1] ? " — full" : ""}${declined ? " — declined (the quote sits far above the list price, so losing it costs nothing)" : ""}</span></div>`;
  const costBody = `
    <div class="kv">
      <b>expected fee</b><span>${fmtEur(d.cost[0])} = ${d.cost[1].toFixed(2)}&times; the typical fee (${fmtEur(d.typical)})</span>
      <b>late risk</b><span>${(d.cost[2] * 100).toFixed(1)}%</span>
      <b>cost tilt</b><span>&times;${d.cost[3]} the expected fee</span>
    </div>`;
  const qrows = r.o.filter((o) => d.quote[o[0]] != null).map((o) => {
    const q = d.quote[o[0]], ch = d.chance[o[0]] ?? 0;
    return `<div class="optrow"><span class="pl">${o[0].replace(/_/g, " ")}</span>
      <div class="bar"><i style="width:${ch * 100}%"></i></div>
      <span class="val">${fmtEur(q)} · &times;${(q / o[2]).toFixed(2)} list · win chance ${(ch * 100).toFixed(0)}%</span></div>`;
  }).join("");
  const quoterBody = `
    <div class="kv"><b>market level</b><span>&times;${d.level.toFixed(2)} of list — rises on wins, falls on losses</span>
    <b>dealer trust</b><span>${d.trust} on-time orders${d.trust ? ` · +${d.trust}% accepted price` : ""}</span></div>
    ${qrows}`;
  let tail = stage(5, "The outcome", d.won
    ? `<p>The dealer took our <b>${d.won.option.replace(/_/g, " ")}</b> option at <b>${fmtEur(d.won.price)}</b>.</p>`
    : d.cancelled
      ? `<p>The dealer cancelled this order, so it does not count.</p>`
      : `<p>The dealer went to the competitor. Our level steps down — a loss teaches more the more surprising it was.</p>`);
  if (d.won) {
    const g = d.won.gig;
    const sched = g ? g.schedule.map((s, i) =>
      `<span class="gigstep">${i === 0 ? "opens " : "then "}${fmtEur(s.feeCents)}</span>`)
      .join('<span class="gigjoin">&#8250;</span>') : "";
    const bundle = week.ridGid[rid] && WEEK.gigOrders[week.ridGid[rid]]?.length > 1
      ? ` <span class="chip">bundle of ${WEEK.gigOrders[week.ridGid[rid]].length} cars</span>` : "";
    const pickedUp = d.won.pickedUp.map((x) => x != null ? clockStr(x) : "never").join(", ");
    const delivered = d.won.delivered.map((x) => x != null ? clockStr(x) : "never").join(", ");
    const lateBy = d.won.delivered.map((x) => x != null ? x - d.won.deadline : null);
    const isLate = lateBy.some((x) => x != null && x > 0);
    tail += stage(6, "The gig", `
      ${g ? `<div class="gigline">${sched}</div>
      <div class="kv">
        <b>posted</b><span>${clockStr(g.posted)}${bundle}</span>
        <b>booked</b><span>${g.by} at ${fmtEur(g.fee)} — ${g.at - g.posted} min after ${g.views} view${g.views === 1 ? "" : "s"}</span>
        <b>fee vs typical</b><span>&times;${(g.fee / d.typical).toFixed(2)} (floored at &times;${floors[0]}, or &times;${floors[1]} under 40 km — this week's settings)</span>
      </div>` : "<p>No gig moved this car.</p>"}
      <div class="kv"><b>collected</b><span>${pickedUp}</span><b>delivered</b><span>${delivered}</span></div>
      ${isLate ? `<p><span class="badge late">late by ${lateBy.filter((x) => x > 0).map((x) => Math.round(x / 60) + " h").join(", ")}</span> — refunded, and the dealer's trust count halves</p>`
               : `<p><span class="badge won">on time</span> — the price is ours, and the dealer counts one more on-time order</p>`}`);
    const m = d.money || {};
    const price = m.price || d.won.price, fees = m.fees || 0, refund = m.refund || 0, other = m.other || 0;
    const net = price - fees - refund - other;
    const tot = Math.max(price, fees + refund);
    const w1 = 100 * price / tot, w2 = 100 * fees / tot, w3 = 100 * refund / tot;
    tail += stage(7, "The money", `
      <div class="money">
        <div class="m-price" style="width:${w1}%">price ${fmtEur(price)}</div>
        <div class="m-fee" style="width:${w2}%">fee ${fmtEur(Math.round(fees))}</div>
        ${refund ? `<div class="m-ref" style="width:${w3}%">refund ${fmtEur(Math.round(refund))}</div>` : ""}
        <div class="m-net">margin ${fmtEur(Math.round(net))}</div>
      </div>`);
  }
  const match = SETTINGS.match, pct = Math.round(100 * match[0] / match[1]);
  $("#detail").innerHTML = `
    <div class="dhead">
      <h3>${rid} <span class="lane">${nameOf[r.p]} to ${nameOf[r.d]}, ${d.km} km</span></h3>
      <span class="when">${clockStr(r.at)} · dealer ${r.k} · ${r.n} car${r.n > 1 ? "s" : ""}</span>
    </div>
    <p class="settings">One request, answered within its fifteen minutes. The stages below are the parts of our
    desk, in the order they ran. <b>Replayed with the settings that played this week</b> — fee model
    ${SETTINGS.model}, cost tilt &times;${SETTINGS.asPlayed.car} on every lane, flat-fee floors
    &times;${floors[0]}/${floors[1]}, intake ${SETTINGS.asPlayed.limit} (${SETTINGS.asPlayed.morning_limit}
    before noon, safe cars to ${SETTINGS.asPlayed.safe_limit}). The replay reproduces ${pct}% of the week's
    quotes to the cent; ${d.replay.match ? "this one is among them" : "this one is not among them"}.</p>
    <div class="spine">
      ${stage(1, "The note reader", noteBody)}
      ${stage(2, "The intake", intakeBody)}
      ${stage(3, "The learned cost model", costBody, d.replay.match ? "exact" : "approx")}
      ${stage(4, "The quoter", quoterBody)}
      ${tail}
    </div>
    <button class="quiet maplink" id="showMap">Show ${rid} on the map</button>`;
  $("#showMap").addEventListener("click", () => showOnMap(rid));
  $("#detail").scrollTop = 0;
}

/* ============================== how it works ============================== */

function buildSystem() {
  $("#pipeline").innerHTML = STORY.parts.map((p) => `
    <div class="part"><div><h4>${p.name}</h4><span class="code">${p.code}</span></div>
    <p>${p.reason}</p><div class="eff">${p.effect}</div></div>`).join("");
  $("#method").innerHTML = STORY.method.map(([t, d]) => `<dt>${t}</dt><dd>${d}</dd>`).join("");
  $("#rejected").innerHTML = "<tr><th>idea</th><th>result</th><th>why rejected</th></tr>" +
    STORY.rejected.map(([a, b, c]) => `<tr><td>${a}</td><td class="lose">${b}</td><td>${c}</td></tr>`).join("");
  const max = Math.max(...STORY.adoption.map((a) => a.gain));
  $("#adoption").innerHTML = STORY.adoption.map((a) => `
    <div class="adoptrow${a.neutral ? " neutral" : ""}">
      <div class="lbl">${a.label}</div>
      <div class="bar"><i style="width:${100 * a.gain / max}%"></i></div>
      <div class="gain">${a.gainText ?? "+€" + a.gain.toLocaleString("en-GB")}</div>
      <div class="sub">${a.note}</div>
    </div>`).join("");
}

/* ============================== the race ============================== */

function buildRace() {
  const s = RACE.series, x0 = s[0][0], x1 = RACE.end;
  const chart = (svgSel, pick, idx, yLabel, fmt) => {
    const svg = $(svgSel), W = 900, H = 380, ml = 64, mt = 26, mb = 30;
    svg.setAttribute("viewBox", `0 0 ${W} ${H}`);
    const yMax = Math.max(...s.map(pick)) * 1.08;
    const X = (min) => ml + (min - x0) / (x1 - x0) * (W - ml - 12);
    const Y = (v) => H - mb - v / yMax * (H - mt - mb);
    let grid = "";
    for (let d = 0; d <= 9; d++) { const min = d * 1440 + 480;
      if (min < x0 || min > x1) continue;
      grid += `<line x1="${X(min)}" y1="${mt}" x2="${X(min)}" y2="${H - mb}" stroke="#223349"/>
        <text x="${X(min)}" y="${H - 10}" fill="#5C7188" font-size="12" text-anchor="middle">${DAYS[d]} 08</text>`; }
    for (let k = 0; k <= 4; k++) { const v = yMax * k / 4;
      grid += `<line x1="${ml}" y1="${Y(v)}" x2="${W - 12}" y2="${Y(v)}" stroke="#16263B"/>
        <text x="${ml - 8}" y="${Y(v) + 4}" fill="#5C7188" font-size="11" text-anchor="end">${fmt(v)}</text>`; }
    const line = (i, color) =>
      `<polyline points="${s.map((p) => `${X(p[0])},${Y(p[i])}`).join(" ")}" fill="none" stroke="${color}" stroke-width="2.2"/>`;
    svg.innerHTML = `
      <text x="${ml}" y="16" fill="#8FA6BE" font-size="13">${yLabel}</text>${grid}
      ${line(idx[0], "#54C08A")}${line(idx[1], "#F0A532")}
      <text x="${X(x1) - 4}" y="${Y(s[s.length - 1][idx[0]]) - 8}" fill="#54C08A" font-size="12" text-anchor="end">us ${fmt(s[s.length - 1][idx[0]])}</text>
      <text x="${X(x1) - 4}" y="${Y(s[s.length - 1][idx[1]]) - 8}" fill="#F0A532" font-size="12" text-anchor="end">top team ${fmt(s[s.length - 1][idx[1]])}</text>`;
  };
  chart("#raceMargin", (p) => Math.max(p[1], p[3]), [1, 3], "margin (game euros)", (v) => "€" + Math.round(v / 100 / 1000) + "k");
  chart("#raceOrders", (p) => Math.max(p[2], p[4]), [2, 4], "orders won", (v) => Math.round(v));
  $("#raceNotes").innerHTML = STORY.raceNotes.map(([d, t]) => `<div><b>${d}</b> — ${t}</div>`).join("")
    + `<div><b>The feed</b> — every team's totals, every 2 s; we show only us and the top team. The top team's books,
       read off the same feed, were ours plus about 110 cars on lanes under 100 km — worth about €19 of margin each.</div>`;
}

load();
