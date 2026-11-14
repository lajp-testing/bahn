/* Spread demo — plain JS, no dependencies. All data is local JSON recorded from the
   18:00 test final; every view is a pure function of the data (and of the chosen
   minute on the map), so scrubbing backwards is exact. */
"use strict";

const DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun", "Mon", "Tue", "Wed"];
const END = 14280; // the world ends Wed 22:00, minute 14280
const APPROX = "approximate: computed by replaying this week through our code; the final world's "
  + "driver list was not saved, so the cost model's driver-supply inputs use a stand-in level-8 roster";

let MAP, WEEK, DEC, STORY, RACE;
let nameOf = {};   // place id -> name
let proj;          // lat/lon -> svg x/y

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

async function load() {
  [MAP, WEEK, DEC, STORY, RACE] = await Promise.all(
    ["map", "week", "decisions", "story", "race"].map((n) => fetch(`data/${n}.json`).then((r) => r.json())));
  WEEK.reqMap = {}; WEEK.requests.forEach((r) => WEEK.reqMap[r.id] = r);
  MAP.places.forEach((p) => nameOf[p.id] = p.name);
  const hash = location.hash.slice(1);
  if (hash && document.getElementById("tab-" + (hash.split("@")[0]))) showTab(hash.split("@")[0]);
  buildHeader();
  buildChallenge();
  buildWeek();
  buildDecision();
  buildSystem();
  buildRace();
}

/* ============================== header + tabs ============================== */

function buildHeader() {
  const r = STORY.result;
  $("#finalScore").innerHTML = `
    <div><b>${r.rank}<small>/${r.of}</small></b><span>rank</span></div>
    <div><b>${fmtEur(Math.round(r.marginEur * 100))}</b><span>margin</span></div>
    <div><b>${r.orders}</b><span>orders</span></div>
    <div><b>${(r.onTime * 100).toFixed(1)}%</b><span>on time</span></div>
    <div><b>${r.requests}</b><span>requests</span></div>`;
}

document.querySelectorAll("nav button").forEach((b) => b.addEventListener("click", () => showTab(b.dataset.tab)));
function showTab(tab) {
  document.querySelectorAll("nav button").forEach((b) => b.classList.toggle("on", b.dataset.tab === tab));
  document.querySelectorAll("main").forEach((m) => m.classList.toggle("on", m.id === "tab-" + tab));
}
document.querySelectorAll("[data-goto]").forEach((a) =>
  a.addEventListener("click", (e) => { e.preventDefault(); showTab(a.dataset.goto); }));

/* ============================== challenge ============================== */

function buildChallenge() {
  $("#steps").innerHTML = STORY.challenge.steps.map((s) =>
    `<div class="card"><h4>${s.title}</h4><p>${s.text}</p></div>`).join("");
  $("#flow").innerHTML = `<div class="flowrow">
    ${["Dealer|sends a request", "Our desk|reads the note, prices each option", "Quote|one price per option",
       "Dealer|picks us or the competitor", "Order|won, with a deadline", "Gig|posted with a fee",
       "Driver|books, drives", "Delivered|on time = margin"]
      .map((s, i, arr) => {
        const [b, t] = s.split("|");
        return `<div class="fbox"><b>${b}</b><span>${t}</span></div>${i < arr.length - 1 ? '<div class="farrow">&#10142;</div>' : ""}`;
      }).join("")}</div>`;
  $("#words").innerHTML = STORY.challenge.words.map(([w, d]) => `<dt>${w}</dt><dd>${d}</dd>`).join("");
}

/* ============================== the week ============================== */

// --- projection: equirectangular in km, covering the (simplified) outline ---
function makeProjection() {
  const LAT0 = 59.6, LAT1 = 68.7, LON0 = 20.8, LON1 = 30.9;
  const kmLat = 111, kmLon = 111 * Math.cos(64 * Math.PI / 180);
  const W = (LON1 - LON0) * kmLon, H = (LAT1 - LAT0) * kmLat;
  return { f: (lat, lon) => [(lon - LON0) * kmLon, (LAT1 - lat) * kmLat], W, H };
}
function ll(id) { const q = MAP.places.find((x) => x.id === id); return [q.lat, q.lon]; }

const week = {
  t: 0, playing: false, speed: 60, last: 0,
  reqByAt: [], wonByAt: [], lostByAt: [], ledgerCum: [], feed: [], feedAt: [],
  eventMinutes: [], orderDoneAt: [], orderDone: [],
  movesByRid: {}, ridGid: {}, usedEdges: new Set(), seg: new Map(), g: null,
};

function buildWeek() {
  proj = makeProjection();
  week.reqByAt = WEEK.requests.map((r) => [r.at, r]).sort((a, b) => a[0] - b[0]);
  week.wonByAt = WEEK.won.slice().sort((a, b) => a[0] - b[0]);
  week.lostByAt = WEEK.lost.slice().sort((a, b) => a[0] - b[0]);
  let cum = 0;
  week.ledgerCum = WEEK.ledger.map(([at, , cents]) => { cum += cents; return [at, cum]; });
  // order completion times (all legs delivered) for the on-time share
  const legs = {}, done = {};
  WEEK.moves.forEach((m) => { legs[m.rid] = (legs[m.rid] || 0) + 1; });
  WEEK.moves.forEach((m) => { if (m.de != null) done[m.rid] = Math.max(done[m.rid] || 0, m.de); });
  const nLegs = {}; WEEK.requests.forEach((r) => nLegs[r.id] = r.n);
  week.orderDone = [];
  for (const [rid, de] of Object.entries(done)) {
    if (legs[rid] !== nLegs[rid]) continue;
    const late = WEEK.moves.filter((m) => m.rid === rid).some((m) => m.late);
    week.orderDone.push([de, late ? 0 : 1, rid]);
  }
  week.orderDone.sort((a, b) => a[0] - b[0]);
  week.orderDoneAt = week.orderDone.map((r) => [r[0]]);
  // move geometry: cumulative segment lengths for interpolation
  WEEK.moves.forEach((m, i) => {
    (week.movesByRid[m.rid] = week.movesByRid[m.rid] || []).push(i);
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
  // the event feed + its minutes (for stepping)
  const feed = [];
  WEEK.requests.forEach((r) => feed.push({ at: r.at, kind: "req", r }));
  WEEK.won.forEach(([at, rid]) => feed.push({ at, kind: "won", rid }));
  WEEK.lost.forEach(([at, rid]) => feed.push({ at, kind: "lost", rid }));
  WEEK.posts.forEach(([at, gid]) => feed.push({ at, kind: "post", gid }));
  WEEK.bookings.forEach(([at, gid, fee]) => feed.push({ at, kind: "book", gid, fee }));
  WEEK.drops.forEach(([at, gid]) => feed.push({ at, kind: "drop", gid }));
  WEEK.moves.forEach((m) => {
    feed.push({ at: m.pu, kind: "pick", m });
    if (m.de != null) feed.push({ at: m.de, kind: "del", m });
  });
  feed.sort((a, b) => a.at - b.at || (a.kind < b.kind ? -1 : 1));
  week.feed = feed;
  week.feedAt = feed.map((e) => [e.at]);
  week.eventMinutes = [...new Set(feed.map((e) => e.at))];
  drawMapBase();
  // controls
  $("#slider").addEventListener("input", (e) => setTime(+e.target.value));
  $("#play").addEventListener("click", togglePlay);
  $("#speed").addEventListener("change", (e) => week.speed = +e.target.value);
  $("#prevEvent").addEventListener("click", () => stepEvent(-1));
  $("#nextEvent").addEventListener("click", () => stepEvent(1));
  $("#prevHour").addEventListener("click", () => setTime(week.t - 60));
  $("#nextHour").addEventListener("click", () => setTime(week.t + 60));
  $("#prevDay").addEventListener("click", () => setTime(week.t - 1440));
  $("#nextDay").addEventListener("click", () => setTime(week.t + 1440));
  $("#dayJumps").innerHTML = [0, 1, 2, 3, 4, 5, 7].map((d) =>
    `<button data-d="${d}">${DAYS[d]}</button>`).join("");
  document.querySelectorAll("#dayJumps button").forEach((b) =>
    b.addEventListener("click", () => setTime(+b.dataset.d * 1440 + 8 * 60)));
  setTime(0);
  const at = location.hash.split("@")[1];
  if (at) setTime(+at);
}

function drawMapBase() {
  const svg = $("#map");
  svg.setAttribute("viewBox", `0 0 ${proj.W} ${proj.H}`);
  const mk = (cls) => { const g = svgEl("g", { class: cls }); svg.appendChild(g); return g; };
  mk("outline"); mk("roads"); const routes = mk("routes"), markers = mk("markers"), cars = mk("cars"); mk("towns");
  week.g = { routes, markers, cars };
  const gOutline = svg.querySelector(".outline"), gRoads = svg.querySelector(".roads"), gTowns = svg.querySelector(".towns");
  gOutline.appendChild(svgEl("polygon", {
    points: MAP.outline.map((p) => proj.f(p[0], p[1])).map((p) => p.join(",")).join(" "),
    fill: "#12233a", stroke: "#2c4a6e", "stroke-width": 6, opacity: .85 }));
  const place = {}; MAP.places.forEach((p) => place[p.id] = p);
  MAP.roads.forEach(([a, b, km]) => {
    const used = week.usedEdges.has(a < b ? a + "|" + b : b + "|" + a);
    if (!used && km > 170) return;
    const p = proj.f(place[a].lat, place[a].lon), q = proj.f(place[b].lat, place[b].lon);
    gRoads.appendChild(svgEl("line", {
      x1: p[0], y1: p[1], x2: q[0], y2: q[1],
      stroke: used ? "#44608f" : "#2c4066", "stroke-width": used ? 4 : 3,
      opacity: used ? .55 : .38 }));
  });
  MAP.places.forEach((p) => {
    const [x, y] = proj.f(p.lat, p.lon);
    gTowns.appendChild(svgEl("circle", { cx: x, cy: y, r: 8, fill: "#7d97c2", stroke: "#0e1420", "stroke-width": 2 }));
    const t = svgEl("text", { x: x + 13, y: y + 4, fill: "#a9bcdc", "font-size": 14, "font-family": "system-ui" });
    t.textContent = p.name; gTowns.appendChild(t);
  });
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

function setTime(t) {
  week.t = Math.max(0, Math.min(END, Math.round(t)));
  renderWeek();
}

function renderWeek() {
  const t = week.t;
  $("#clock").textContent = clockStr(t);
  if (+$("#slider").value !== t) $("#slider").value = t;
  document.querySelectorAll("#dayJumps button").forEach((b) =>
    b.classList.toggle("cur", Math.floor(t / 1440) === +b.dataset.d));

  const g = week.g;
  g.routes.textContent = ""; g.markers.textContent = ""; g.cars.textContent = "";

  // requests: a pulse at the pickup town for 25 minutes after arrival
  const nReq = bisect(week.reqByAt, t);
  for (let i = nReq - 1; i >= 0 && week.reqByAt[i][0] > t - 25; i--) {
    const r = week.reqByAt[i][1], age = t - r.at, p = proj.f(...ll(r.p));
    g.markers.appendChild(svgEl("circle", { cx: p[0], cy: p[1], r: 10 + age * 1.3, fill: "none",
      stroke: "#fbbf24", "stroke-width": 5, opacity: 0.9 * (1 - age / 25) }));
  }
  // lost requests: a brief grey flash at the pickup
  const nLost = bisect(week.lostByAt, t);
  for (let i = nLost - 1; i >= 0 && week.lostByAt[i][0] > t - 15; i--) {
    const p = proj.f(...ll(WEEK.reqMap[week.lostByAt[i][1]].p));
    g.markers.appendChild(svgEl("circle", { cx: p[0], cy: p[1], r: 7, fill: "#5c6c8a",
      opacity: .7 * (1 - (t - week.lostByAt[i][0]) / 15) }));
  }
  // cars: routes and interpolating dots
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
      if (m.late) { // a late car stays as a red scar on the map
        g.routes.appendChild(svgEl("polyline", { points: pathD(i), fill: "none",
          stroke: "#f87171", "stroke-width": 3.5, opacity: .55, "stroke-dasharray": "10 7" }));
        if (age < 360) { const p = posOnPath(i, 1);
          g.cars.appendChild(svgEl("circle", { cx: p[0], cy: p[1], r: 9, fill: "#f87171", stroke: "#fff", "stroke-width": 2, opacity: 1 - age / 360 })); }
      } else if (age < 150) { // an on-time delivery fades out
        g.routes.appendChild(svgEl("polyline", { points: pathD(i), fill: "none",
          stroke: "#4ade80", "stroke-width": 3.5, opacity: .5 * (1 - age / 150) }));
      }
      return;
    }
    moving++;
    g.routes.appendChild(svgEl("polyline", { points: pathD(i), fill: "none",
      stroke: m.late ? "#f87171" : "#60a5fa", "stroke-width": 3, opacity: .8 }));
    const p = posOnPath(i, (t - m.pu) / Math.max(1, de - m.pu));
    g.cars.appendChild(svgEl("circle", { cx: p[0], cy: p[1], r: 7, fill: m.late ? "#f87171" : "#60a5fa", stroke: "#0e1420", "stroke-width": 2 }));
  });
  // an order won but not yet collected: a green ring at its pickup
  WEEK.moves.forEach((m) => {
    if (!wonSet.has(m.rid) || m.pu <= t) return;
    const p = proj.f(...ll(m.p));
    g.markers.appendChild(svgEl("circle", { cx: p[0], cy: p[1], r: 9, fill: "none", stroke: "#4ade80", "stroke-width": 4, opacity: .8 }));
  });

  // counters
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
  const late = doneOrders - onTime;
  $("#cLate").textContent = late;
  const share = doneOrders ? onTime / doneOrders : null;
  $("#onTimeFill").style.width = (share == null ? 0 : share * 100) + "%";
  $("#onTimeFill").style.background = share != null && share < 0.9
    ? "linear-gradient(90deg,#7f1d1d,#f87171)" : "linear-gradient(90deg,#166534,#4ade80)";
  $("#onTimePct").textContent = share == null ? "–" : (share * 100).toFixed(1) + "%";

  // the feed: the last 12 things that happened at or before t
  const kf = bisect(week.feedAt, t);
  $("#feed").innerHTML = week.feed.slice(Math.max(0, kf - 12), kf).reverse().map(feedLine).join("");
}

function feedLine(e) {
  const t = `<span class="t">${hhmm(e.at)}</span>`;
  switch (e.kind) {
    case "req": return `<li class="req">${t}${e.r.id} · ${nameOf[e.r.p]} &rarr; ${nameOf[e.r.d]} asks for a price</li>`;
    case "won": return `<li class="won">${t}won ${e.rid} · ${fmtEur(DEC[e.rid]?.won?.price || 0)}</li>`;
    case "lost": return `<li class="lost">${t}lost ${e.rid} to the competitor</li>`;
    case "post": return `<li class="post">${t}gig ${e.gid} posted in the app</li>`;
    case "book": return `<li class="book">${t}gig ${e.gid} booked · ${fmtEur(e.fee)}</li>`;
    case "drop": return `<li class="book">${t}gig ${e.gid} dropped by the driver</li>`;
    case "pick": return `<li class="post">${t}${e.m.rid} · car collected in ${nameOf[e.m.p]}</li>`;
    case "del": return `<li class="${e.m.late ? "late" : "del"}">${t}${e.m.rid} delivered ${e.m.late ? "LATE" : "on time"} in ${nameOf[e.m.d]}</li>`;
  }
  return "";
}

function togglePlay() {
  week.playing = !week.playing;
  $("#play").innerHTML = week.playing ? "&#10074;&#10074; pause" : "&#9654; play";
  $("#play").classList.toggle("on", week.playing);
  if (week.playing) { week.last = performance.now(); requestAnimationFrame(tickPlay); }
}
function tickPlay(now) {
  if (!week.playing) return;
  week.t += (now - week.last) / 1000 * week.speed;
  week.last = now;
  if (week.t >= END) { week.t = END; togglePlay(); }
  renderWeek();
  if (week.playing) requestAnimationFrame(tickPlay);
}
function stepEvent(dir) {
  const t = week.t, ms = week.eventMinutes;
  let next = null;
  if (dir > 0) next = ms.find((m) => m > t);
  else for (let i = ms.length - 1; i >= 0; i--) if (ms[i] < t) { next = ms[i]; break; }
  setTime(next == null ? (dir > 0 ? END : 0) : next);
}

/* ============================== inspect a decision ============================== */

const dec = { filter: "all", search: "", sel: null };

function buildDecision() {
  $("#search").addEventListener("input", (e) => { dec.search = e.target.value.toLowerCase(); renderRows(); });
  $("#filter").addEventListener("change", (e) => { dec.filter = e.target.value; renderRows(); });
  // win rate by lane length, for context
  const buckets = [[0, 40], [40, 100], [100, 300], [300, 1e9]];
  const stat = buckets.map(() => [0, 0]);
  WEEK.requests.forEach((r) => {
    const d = DEC[r.id]; if (!d) return;
    const b = buckets.findIndex(([lo, hi]) => d.km >= lo && d.km < hi);
    stat[b][0]++; if (d.won) stat[b][1]++;
  });
  $("#laneStats").innerHTML = "win rate by lane: " + buckets.map(([lo, hi], i) =>
    `<b>${hi < 1e9 ? (lo ? `${lo}–${hi}` : `&lt;${hi}`) : `${lo}+`} km</b> ${stat[i][0] ? Math.round(100 * stat[i][1] / stat[i][0]) : 0}% (${stat[i][1]}/${stat[i][0]})`
  ).join(" · ");
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
      <td>${clockStr(r.at)}</td><td>${r.id}</td><td>${nameOf[r.p]}&rarr;${nameOf[r.d]}</td>
      <td class="r">${d.km}</td><td class="r">&times;${Math.min(...ratioList).toFixed(2)}</td><td>${badge}</td></tr>`;
  }).join("");
  document.querySelectorAll("#drows tr").forEach((tr) =>
    tr.addEventListener("click", () => selectRequest(tr.dataset.r)));
}

function stage(n, title, body, approx) {
  return `<div class="stage" data-n="${n}"><h4>${title}${approx ? ` <span class="approx" title="${APPROX}">&approx;</span>` : ""}</h4>${body}</div>`;
}

function selectRequest(rid) {
  dec.sel = rid;
  renderRows();
  const r = WEEK.reqMap[rid], d = DEC[rid];
  const facts = d.noteFacts;
  // 1. the note
  let noteBody = `<p class="small">No note — the reader has nothing to read.</p>`;
  if (r.note) {
    const chips = [];
    if (facts.ready != null) chips.push(`<span class="chip">ready from ${clockStr(facts.ready)}</span>`);
    if (facts.deadline != null) chips.push(`<span class="chip">deadline ${clockStr(facts.deadline)}</span>`);
    if (facts.hours) chips.push(`<span class="chip">pickup hours ${facts.hours[0] != null ? hhmm(facts.hours[0]) : ""}–${facts.hours[1] != null ? hhmm(facts.hours[1]) : ""}</span>`);
    if (facts.manual) chips.push(`<span class="chip">manual licence needed</span>`);
    if (facts.plates) chips.push(`<span class="chip">fetch plates</span>`);
    if (!facts.sure) chips.push(`<span class="chip bad">reader unsure</span>`);
    noteBody = `<p class="noteq">&ldquo;${r.note}&rdquo;</p><div class="chips">${chips.join("") || '<span class="chip">harmless — no constraint</span>'}</div>`;
  }
  // 2. the intake
  const offered = Object.keys(d.quote), all = r.o.map((o) => o[0]);
  const slackChips = all.map((k) => {
    const ok = d.slack[k] != null && d.slack[k] >= 12;
    return `<span class="chip ${offered.includes(k) ? (ok ? "good" : "") : "off"}">${k.replaceAll("_", " ")} · ${d.slack[k] != null ? d.slack[k] + " h slack" : "not offered"}</span>`;
  });
  const declined = offered.length === 1 && Object.values(d.quote)[0] > 4 * r.o[0][2];
  const intakeBody = `
    <div class="chips">${slackChips.join("")}</div>
    <div class="kv"><b>queue</b><span>${d.queue[0]} of ${d.queue[1]} unbooked ${d.queue[0] >= d.queue[1] ? "— full" : ""}${declined ? " — declined (the quote sits far above the list price, so losing it costs nothing)" : ""}</span></div>`;
  // 3. the cost model
  const costBody = `
    <div class="kv">
      <b>expected fee</b><span>${fmtEur(d.cost[0])} = ${d.cost[1].toFixed(2)}&times; the typical fee (${fmtEur(d.typical)})</span>
      <b>late risk</b><span>${(d.cost[2] * 100).toFixed(1)}%</span>
      <b>cost tilt</b><span>${d.cost[3]}&times; the expected fee ${d.km < 100 ? "(a lane under 100 km)" : ""}</span>
    </div>`;
  // 4. the quoter
  const qrows = r.o.filter((o) => d.quote[o[0]] != null).map((o) => {
    const q = d.quote[o[0]], ch = d.chance[o[0]] ?? 0;
    return `<div class="optrow"><span>${o[0].replaceAll("_", " ")}</span>
      <div class="bar"><i style="width:${ch * 100}%"></i></div>
      <span>${fmtEur(q)} · &times;${(q / o[2]).toFixed(2)} list · win chance ${(ch * 100).toFixed(0)}%</span></div>`;
  }).join("");
  const quoterBody = `
    <div class="kv"><b>market level</b><span>${d.level.toFixed(2)}&times; list (rises on wins, falls on losses)</span>
    <b>dealer trust</b><span>${d.trust} on-time orders${d.trust ? ` · +${d.trust}% accepted price` : ""}</span></div>
    ${qrows}`;
  // 5-7. outcome, gig, money
  let tail = stage(5, "The outcome", d.won
    ? `<p>The dealer took our <b>${d.won.option.replaceAll("_", " ")}</b> option at <b>${fmtEur(d.won.price)}</b>.</p>`
    : d.cancelled
      ? `<p>The dealer cancelled this order, so it does not count.</p>`
      : `<p>The dealer went to the competitor. Our level steps down — a loss teaches more the more surprising it was.</p>`);
  if (d.won) {
    const g = d.won.gig;
    const sched = g ? g.schedule.map((s, i) =>
      `<span class="gigstep">${i === 0 ? "opens " : "then "}${fmtEur(s.feeCents)}</span>`)
      .join('<span class="gigjoin">&rarr;</span>') : "";
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
        <b>fee vs typical</b><span>${(g.fee / d.typical).toFixed(2)}&times; (floored at 0.75, or 0.95 under 40 km)</span>
      </div>` : "<p class='small'>No gig moved this car.</p>"}
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
  $("#detail").innerHTML = `
    <div class="dhead">
      <h3>${rid} <span class="lane">${nameOf[r.p]} &rarr; ${nameOf[r.d]} · ${d.km} km</span></h3>
      <span class="small">${clockStr(r.at)} · dealer ${r.k} · ${r.n} car${r.n > 1 ? "s" : ""}</span>
    </div>
    <p class="small">One request, answered in the 15 minutes before its response deadline. The stages below are
    the parts of our desk, in the order they ran.</p>
    ${stage(1, "The note reader", noteBody)}
    ${stage(2, "The intake", intakeBody)}
    ${stage(3, "The learned cost model", costBody, true)}
    ${stage(4, "The quoter", quoterBody)}
    ${tail}`;
  $("#detail").scrollTop = 0;
}

/* ============================== the system ============================== */

function buildSystem() {
  $("#pipeline").innerHTML = STORY.parts.map((p) => `
    <div class="pcard"><span class="code">${p.code}</span><h4>${p.name}</h4>
    <p>${p.reason}</p><div class="eff">${p.effect}</div></div>`).join("");
  $("#method").innerHTML = STORY.method.map(([t, d]) => `<dt>${t}</dt><dd>${d}</dd>`).join("");
  $("#rejected").innerHTML = "<tr><th>idea</th><th>result</th><th>why rejected</th></tr>" +
    STORY.rejected.map(([a, b, c]) => `<tr><td>${a}</td><td class="lose">${b}</td><td>${c}</td></tr>`).join("");
  const max = Math.max(...STORY.adoption.map((a) => a.gain));
  $("#adoption").innerHTML = STORY.adoption.map((a) => `
    <div class="adoptrow">
      <div class="lbl">${a.label}</div>
      <div class="bar"><i style="width:${100 * a.gain / max}%"></i></div>
      <div class="gain">+€${a.gain.toLocaleString("en-GB")}</div>
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
      grid += `<line x1="${X(min)}" y1="${mt}" x2="${X(min)}" y2="${H - mb}" stroke="#26324c"/>
        <text x="${X(min)}" y="${H - 10}" fill="#5c6c8a" font-size="12" text-anchor="middle">${DAYS[d]} 08</text>`; }
    for (let k = 0; k <= 4; k++) { const v = yMax * k / 4;
      grid += `<line x1="${ml}" y1="${Y(v)}" x2="${W - 12}" y2="${Y(v)}" stroke="#1d2739"/>
        <text x="${ml - 8}" y="${Y(v) + 4}" fill="#5c6c8a" font-size="11" text-anchor="end">${fmt(v)}</text>`; }
    const line = (i, color) =>
      `<polyline points="${s.map((p) => `${X(p[0])},${Y(p[i])}`).join(" ")}" fill="none" stroke="${color}" stroke-width="2.5"/>`;
    svg.innerHTML = `
      <text x="${ml}" y="16" fill="#8fa0bd" font-size="13">${yLabel}</text>${grid}
      ${line(idx[0], "#4ade80")}${line(idx[1], "#fbbf24")}
      <text x="${X(x1) - 4}" y="${Y(s[s.length - 1][idx[0]]) - 8}" fill="#4ade80" font-size="12" text-anchor="end">us ${fmt(s[s.length - 1][idx[0]])}</text>
      <text x="${X(x1) - 4}" y="${Y(s[s.length - 1][idx[1]]) - 8}" fill="#fbbf24" font-size="12" text-anchor="end">top team ${fmt(s[s.length - 1][idx[1]])}</text>`;
  };
  chart("#raceMargin", (p) => Math.max(p[1], p[3]), [1, 3], "margin (game euros)", (v) => "€" + Math.round(v / 100 / 1000) + "k");
  chart("#raceOrders", (p) => Math.max(p[2], p[4]), [2, 4], "orders won", (v) => Math.round(v));
  $("#raceNotes").innerHTML = STORY.raceNotes.map(([d, t]) => `<div><b>${d}</b> — ${t}</div>`).join("")
    + `<div><b>The feed</b> — every team's totals, every 2 s; we show only us and the top team. The top team's books,
       read off the same feed, were ours plus about 110 cars on lanes under 100 km — worth about €19 of margin each.</div>`;
}

load();
