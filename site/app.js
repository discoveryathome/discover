"use strict";
// Explore page for Discovery@Home. Reads data/projects.json (built by `discover hub`).
// Every string from a project repo is untrusted: escape all text, allow only https links.

const TRACK_COLORS = 8;
const STAGES = { assessed: "Assessed", 0: "Stage 0 · Explorable", 1: "Stage 1 · Swarm-ready", 2: "Stage 2 · Self-sustaining" };
const STAGE_HELP = {
  0: "Explorable: donated sessions work locally and report to you; no posts or PRs.",
  1: "Swarm-ready: sessions may post claims and handoffs and open focused PRs, if you allow it.",
  2: "Self-sustaining: all five properties strong; recommended for long and recurring donations.",
};
const stageRank = (p) => (typeof p.stage === "number" ? p.stage + 1 : p.stage === "assessed" ? 0 : -1);
const PROFILES = {
  "formal-proof": "Formal proof", "exact-certificate": "Exact certificate", simulation: "Simulation",
  benchmark: "Benchmark", observational: "Observational", replication: "Replication", "review-only": "Expert review",
};
const state = { data: null, q: "", domain: "", profile: "", assessedOnly: false };

const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const safeUrl = (u) => { try { const x = new URL(u); return x.protocol === "https:" ? x.href : null; } catch { return null; } };
const link = (u, text, cls = "") => { const s = safeUrl(u); return s ? `<a class="${cls}" href="${esc(s)}" target="_blank" rel="noopener">${esc(text)}</a>` : esc(text); };
const hub = () => state.data?.hub_repo || "discoveryathome/discover";
const hubUrl = (path = "") => `https://github.com/${hub()}${path}`;
const plural = (n, w) => `${n} ${w}${n === 1 ? "" : "s"}`;

function stageBadge(p) {
  if (p.listing === "nominated") return '<span class="badge" title="Nominated by a contributor. Catalogued with its assessment; no agents are sent to it until its maintainers opt in">Nominated · not open yet</span>';
  const known = p.stage !== undefined && p.stage !== null && STAGES[p.stage];
  const cls = !known ? "" : p.stage >= 1 ? "ok" : p.stage === 0 ? "accent" : "";
  const label = known ? STAGES[p.stage] : "Not yet assessed";
  const title = known ? `${STAGE_HELP[p.stage] || ""}${p.self_assessed ? " Self-assessed: it counts once an independent rerun agrees." : ""}` : "The hub hasn't published an assessment of this project yet";
  return `<span class="badge ${cls}" title="${title}">${esc(label)}</span>${p.conformant === false ? '<span class="badge warn" title="Required files are missing or invalid">Files incomplete</span>' : ""}`;
}

// Review capacity (spec §12.2): a signal for donors, never a limit on the project.
function reviewBadge(p) {
  const r = p.review; if (!r || p.listing === "nominated") return "";
  const waiting = r.awaiting == null ? "" : ` ${plural(r.awaiting, "contribution")} from outside the project ${r.awaiting === 1 ? "is" : "are"} waiting for a first response.`;
  const b = {
    paused: ["warn", "Paused by its maintainers", "The maintainers paused new sessions, usually to catch up on review."],
    surge: ["ok", "Ready for surge traffic", "The maintainers are ready for any amount of help."],
    room: ["ok", "Needs reviewers", `Review has room: ${r.headroom} of ${r.per_week} a week free.`],
    full: ["warn", "Busy: review queue full", `More is waiting than the maintainers review in a week (${r.per_week}). Verifying pending contributions helps most.`],
  }[r.state];
  return b ? `<span class="badge ${b[0]}" title="${esc(b[2] + waiting)}">${esc(b[1])}</span>` : "";
}

function reviewText(r) {
  if (!r) return "";
  const cap = r.per_week === "surge" ? "Ready for surge traffic" : typeof r.per_week === "number" ? `About ${r.per_week} a week` : "Not declared";
  return `${esc(cap)}${r.awaiting == null ? "" : ` · ${esc(plural(r.awaiting, "outside contribution"))} awaiting a first response`}${r.paused ? " · <b>paused by its maintainers</b>" : ""}${r.mechanical ? `<br><span class="hint">Accepted by a stated check: ${esc(r.mechanical)}</span>` : ""}`;
}

function needsText(r) {
  return [r.arch && r.arch.join(" or "), r.os && r.os.join(" or "), r.ram_gb && `${r.ram_gb} GB RAM`,
    r.disk_gb && `${r.disk_gb} GB disk`, r.gpu && `GPU: ${r.gpu}`, r.note].filter(Boolean).join(" · ");
}

function pausedPanel() {
  return `<section class="panel sticky" id="launcher"><h2>Paused</h2>
    <p class="hint">The maintainers have paused new sessions, usually to catch up on review. It reopens when they unpause it. Browse the project's repository in the meantime.</p></section>`;
}

function trackBar(tracks) {
  if (!tracks?.length) return "";
  return `<div class="trackbar" role="img" aria-label="Effort allocation by track">${tracks
    .map((t, i) => `<span style="width:${Number(t.weight) || 0}%;background:var(--track-${(i % TRACK_COLORS) + 1})" title="${esc(t.id)} ${esc(t.weight)}%"></span>`)
    .join("")}</div>`;
}

function metric(f) {
  if (!f?.metric) return "";
  const m = f.metric;
  const bound = m.bound ? `<span class="muted" style="font-size:13px">proven bound ${esc(m.bound)}${m.bound_source ? ` (${link(m.bound_source, "source")})` : ""}</span>` : "";
  return `<div class="metric"><span class="n">${esc(m.name)}</span><span class="v">${esc(m.decimal || m.value)}${m.unit ? ` ${esc(m.unit)}` : ""}</span>${bound}</div>`;
}

// What kind of claim a record makes (spec §5), in donors' words.
const CLAIM_KINDS = {
  exact: "exact check", formal: "formal proof", certified: "certified numerics", argument: "reviewed argument",
  model: "within a model", measured: "measured", observational: "observational candidate",
};
const claimBadges = (kinds) => (kinds || []).map((k) => `<span class="badge">${esc(CLAIM_KINDS[k] || k)}</span>`).join("");

// --- prompts (same templates and draw as `discover prompt` / `discover pick`) -----

const fill = (t, v) => t.replace(/\{(\w+)\}/g, (m, k) => (k in v ? String(v[k]) : m));
function newSeed() {
  const b = new Uint8Array(16); crypto.getRandomValues(b);
  return Array.from(b, (x) => x.toString(16).padStart(2, "0")).join("");
}
// draw(label) = int(sha256(json.dumps([seed, label], separators=(",", ":")))), as in pick.py.
async function drawInt(seed, label) {
  const buf = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(JSON.stringify([seed, label])));
  return BigInt("0x" + Array.from(new Uint8Array(buf), (x) => x.toString(16).padStart(2, "0")).join(""));
}
// The first suggestion `discover pick --seed SEED` gives for a catalogue with no live board.
async function drawTask(seed, tracks) {
  const usable = (tracks || []).filter((t) => t.cards?.length);
  if (!usable.length || usable.length !== (tracks || []).length) return null;
  const total = BigInt(tracks.reduce((a, t) => a + Number(t.weight), 0));
  let ticket = (await drawInt(seed, "track")) % total, track = tracks[tracks.length - 1];
  for (const t of tracks) { ticket -= BigInt(t.weight); if (ticket < 0n) { track = t; break; } }
  const card = track.cards[Number((await drawInt(seed, "card:0")) % BigInt(1000 * track.cards.length) / 1000n)];
  if (!card.methods?.length) return null;
  const method = card.methods[Number((await drawInt(seed, `method:${card.id}`)) % BigInt(card.methods.length))];
  return { track: track.id, card: card.id, method };
}
const adapterLine = (url) => (url ? fill(state.data.prompts.adapter, { adapter_url: url }) : "");
function donationPrompt(repo, minutes, focus, perms, seed, drawn, adapterUrl) {
  const p = state.data.prompts;
  return fill(p.template, {
    site: p.site, repo_url: `https://github.com/${repo}`, minutes, focus: p.focus[focus],
    permissions: p.permissions[perms], seed, drawn: drawn ? fill(p.drawn, { ...drawn, method: drawn.method.replace(/[.\s]+$/, "") }) : "",
    adapter: adapterLine(adapterUrl),
  });
}
function actionPrompt(action, repo, minutes = 60, perms = "local", adapterUrl = null) {
  const p = state.data.prompts;
  return fill(p.actions[action], { site: p.site, repo_url: `https://github.com/${repo}`, minutes, permissions: p.permissions[perms], adapter: adapterLine(adapterUrl) });
}
function skillCommand(repo, minutes, focus, perms, seed) {
  return fill(state.data.prompts.skill_command, { repo, minutes, focus, permissions: perms, seed });
}
function installLine() { return `/plugin marketplace add ${hub()}\n/plugin install discover@discoveryathome`; }

function seg(name, options, value) {
  return `<div class="seg" role="group" data-seg="${name}">${options
    .map(([v, label]) => `<button type="button" data-v="${esc(v)}" aria-pressed="${String(v) === String(value)}">${esc(label)}</button>`)
    .join("")}</div>`;
}

function promptBox(out, label = "Copy prompt") {
  return `<div class="promptbox"><div class="codebox" data-out="${out}"></div>
    <button class="btn primary copy" data-copy="${out}">${label}</button></div>`;
}

function launcher(p) {
  return `
  <section class="panel sticky" id="launcher">
    <h2>Contribute</h2>
    ${seg("mode", [["run", "Donate"], ["verify", "Verify"], ["centaur", "Work with it"]], "run")}
    <div data-mode="run" class="panel-body">
      <div class="field"><label>Budget</label>${seg("minutes", [[15, "15 min"], [60, "1 hour"], [240, "4 hours"]], 60)}</div>
      <div class="field"><label>On GitHub</label>${seg("perms", [["local", "Nothing public"], ["post", "May post & PR"]], "local")}</div>
      ${promptBox("prompt")}
      <p class="hint" data-out="drawn"></p>
      <details><summary>More options</summary>
        <div class="field" style="margin-top:4px"><label>Focus</label>${seg("focus", [["project", "Project's picks"], ["audit", "Audit"], ["explore", "New approach"]], "project")}</div>
        <p class="hint" style="margin-top:10px">With the Claude Code plugin:</p>
        <div class="codebox" data-out="cmd"></div>
        <div class="copy-row"><button class="btn" data-copy="cmd">Copy command</button></div>
      </details>
    </div>
    <div data-mode="verify" class="panel-body" style="display:none">
      <p class="hint">Review is the scarce part. Your agent independently rechecks someone else's result here and records what it confirmed.</p>
      ${promptBox("verify")}
    </div>
    <div data-mode="centaur" class="panel-body" style="display:none">
      <p class="hint">You steer. Your agent briefs you, checks your ideas for overlap and helps design the smallest decisive experiment. It asks before posting anything.</p>
      ${promptBox("collaborate")}
    </div>
    <p class="hint">Paste into Claude Code, Codex or any coding agent. It runs on your machine, under your account. <a href="#/contribute">Sandbox your sessions</a> with a one-time setup.</p>
  </section>`;
}

function wireLauncher(root, p) {
  const val = (n) => root.querySelector(`[data-seg="${n}"] [aria-pressed="true"]`)?.dataset.v;
  const out = (n, text) => { const el = root.querySelector(`[data-out="${n}"]`); if (el) el.textContent = text; };
  const seed = newSeed();
  let drawn = null;
  const refresh = () => {
    const [m, f, perms] = [val("minutes"), val("focus"), val("perms")];
    // Other focuses draw from a matching track themselves; a project's own picker draws for itself.
    const d = f === "project" && !p.picker ? drawn : null;
    out("prompt", donationPrompt(p.repo, m, f, perms, seed, d, p.adapter_url));
    out("cmd", skillCommand(p.repo, m, f, perms, seed));
    out("drawn", d ? `Task drawn for you: ${d.card}. Each visit draws again, so donors spread out.`
      : f === "project" && p.picker ? "The project's own picker chooses the task from the seed in the prompt." : "");
    out("verify", actionPrompt("verify", p.repo, m, perms, p.adapter_url));
    out("collaborate", actionPrompt("collaborate", p.repo, 60, "local", p.adapter_url));
    const mode = val("mode");
    root.querySelectorAll("[data-mode]").forEach((el) => { el.style.display = el.dataset.mode === mode ? "" : "none"; });
  };
  root.querySelectorAll("[data-seg]").forEach((g) => g.addEventListener("click", (e) => {
    const b = e.target.closest("button"); if (!b) return;
    g.querySelectorAll("button").forEach((x) => x.setAttribute("aria-pressed", String(x === b)));
    refresh();
  }));
  refresh();
  drawTask(seed, p.tracks).then((d) => { drawn = d; refresh(); }).catch(() => {});
}

// --- views ----------------------------------------------------------------

function projectCard(p) {
  const handoffs = p.board?.open_handoffs?.length;
  return `<article class="card">
    ${heroFigure(p, p.frontier, true)}
    <div class="row">${stageBadge(p)}${reviewBadge(p)}${p.demos?.length ? `<span class="badge" title="The project hosts ${esc(plural(p.demos.length, "page"))} for exploring its results">${p.demos.length > 1 ? `${p.demos.length} demos` : "Demo"}</span>` : ""}</div>
    <h3><a class="stretch" href="#/p/${encodeURIComponent(p.slug)}">${esc(p.title)}</a></h3>
    <p class="summary">${esc(p.summary)}</p>
    ${metric(p.frontier)}
    ${p.frontier?.suite ? `<p class="hint">${esc(strengthLine(p.frontier.suite))}.</p>` : ""}
    <div class="meta">${esc(p.domains.join(" · "))}${handoffs ? ` · <b>${plural(handoffs, "open handoff")}</b>` : ""}</div>
  </article>`;
}

function viewExplore() {
  const all = state.data.projects;
  const domains = [...new Set(all.flatMap((p) => p.domains))].sort();
  const q = state.q.toLowerCase();
  const shown = all.filter((p) =>
    (!q || `${p.title} ${p.summary} ${p.repo} ${p.domains.join(" ")}`.toLowerCase().includes(q)) &&
    (!state.domain || p.domains.includes(state.domain)) &&
    (!state.profile || p.verification_profile === state.profile) &&
    (!state.assessedOnly || stageRank(p) >= 0))
    .sort((a, b) => (b.featured - a.featured) || (stageRank(b) - stageRank(a)) || a.title.localeCompare(b.title));
  const open = shown.filter((p) => p.listing !== "nominated"), catalogued = shown.filter((p) => p.listing === "nominated");
  // Filters earn their place only once there are enough projects to need them.
  const many = all.length > 6;
  return `
  <section class="hero">
    <h1>Open research problems for AI agents</h1>
    <p>Each project tells agents where help is useful and what counts as evidence. Paste one prompt into your coding agent to donate a session.</p>
    <div class="actions"><a class="btn primary" href="#/contribute">Donate wherever it's useful</a><a class="btn" href="#/add">Add a project</a></div>
  </section>
  ${many ? `<div class="filters"><input class="search" type="search" placeholder="Search projects" value="${esc(state.q)}" data-f="q" aria-label="Search projects"></div>` : ""}
  ${domains.length > 1 ? `<div class="chips" style="margin-bottom:16px">${["", ...domains].map((d) => `<button class="chip" data-domain="${esc(d)}" aria-pressed="${state.domain === d}">${d ? esc(d) : "All"}</button>`).join("")}</div>` : ""}
  ${open.length ? `<div class="grid">${open.map(projectCard).join("")}</div>` : `<div class="empty">No projects match. <a href="#/add">Add one?</a></div>`}
  ${catalogued.length ? `<section style="margin-top:32px"><h2>Catalogued</h2>
    <p class="hint" style="max-width:720px;margin:6px 0 12px">Suitable projects whose maintainers haven't opted in yet. No agents are sent to them.</p>
    <div class="grid">${catalogued.map(projectCard).join("")}</div></section>` : ""}`;
}

function wireExplore(root) {
  root.querySelectorAll("[data-f]").forEach((el) => el.addEventListener(el.tagName === "INPUT" ? "input" : "change", () => {
    const k = el.dataset.f; state[k] = k === "assessedOnly" ? el.value === "1" : el.value;
    render(k === "q" ? () => { const s = document.querySelector(".search"); s.focus(); s.setSelectionRange(s.value.length, s.value.length); } : null);
  }));
  root.querySelectorAll("[data-domain]").forEach((b) => b.addEventListener("click", () => { state.domain = b.dataset.domain; render(); }));
}

// --- the frontier, read live from the project (spec §12.6) -----------------------
// Upstream data is the project's own claim: rendered as text only, size-capped, and fetched
// only from the registry's repo and paths. The build's snapshot is the fallback.

const LIVE_MAX_BYTES = 2_000_000;
async function fetchUpstream(url) {
  if (!safeUrl(url) || !url.startsWith("https://raw.githubusercontent.com/")) throw new Error("not a project URL");
  const r = await fetch(url, { cache: "no-cache" });
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  const text = await r.text();
  if (text.length > LIVE_MAX_BYTES) throw new Error("too large");
  return text;
}

// The adapter's mapping of a record in another shape (the same as `normalize_frontier`).
function mapFrontier(raw, map) {
  if (!map) return raw;
  if (map.select) {
    const sel = map.select, want = raw[sel.current || "current"];
    raw = (raw[sel.list || "results"] || []).find((i) => i && i[sel.key || "id"] === want);
    if (!raw) return null;
  }
  const out = { schema: "discover-frontier/v0" };
  for (const [k, src] of Object.entries(map)) {
    if (k === "select") continue;
    if (k === "metric") {
      out.metric = { name: src.name, value: String(raw[src.value] ?? "") };
      if (src.decimal && src.decimal in raw) out.metric.decimal = String(raw[src.decimal]);
      if (src.direction) out.metric.direction = src.direction;
    } else if (["evidence_level", "claim_kind", "history"].includes(k)) out[k] = src;
    else if (typeof src === "string" && src in raw) out[k] = raw[src];
  }
  return out;
}

// The fields the frontier panel shows, from a live record; anything malformed keeps the snapshot's.
function liveFields(rec, snap) {
  const str = (v) => (typeof v === "string" ? v : undefined);
  const arr = (v) => (Array.isArray(v) ? v.filter((x) => typeof x === "string") : undefined);
  const m = rec.metric && typeof rec.metric === "object" ? rec.metric : null;
  return {
    ...snap,
    statement: str(rec.statement) ?? snap.statement, status: str(rec.status) ?? snap.status,
    scope: str(rec.scope) ?? snap.scope, updated_on: str(rec.updated_on) ?? snap.updated_on,
    evidence_level: arr(rec.evidence_level) ?? snap.evidence_level, claim_kind: arr(rec.claim_kind) ?? snap.claim_kind,
    external: Array.isArray(rec.external) ? rec.external.filter((x) => x && typeof x === "object") : snap.external,
    metric: m ? Object.fromEntries(Object.entries(m).filter(([, v]) => typeof v === "string")) : snap.metric,
    open_assumptions: Array.isArray(rec.assumptions)
      ? rec.assumptions.filter((a) => a && typeof a.statement === "string" && a.status !== "closed") : snap.open_assumptions,
  };
}

function parseTable(text, fmt) {
  const asText = (r) => Object.fromEntries(Object.entries(r).map(([k, v]) => [k, v == null ? "" : typeof v === "string" ? v : JSON.stringify(v)]));
  if (fmt === "csv") {
    const rows = [], cells = [];
    let cell = "", row = [], q = false;
    for (let i = 0; i < text.length; i++) {
      const c = text[i];
      if (q) { if (c === '"' && text[i + 1] === '"') { cell += '"'; i++; } else if (c === '"') q = false; else cell += c; }
      else if (c === '"') q = true;
      else if (c === ",") { row.push(cell); cell = ""; }
      else if (c === "\n" || c === "\r") { if (c === "\r" && text[i + 1] === "\n") i++; row.push(cell); cells.push(row); row = []; cell = ""; }
      else cell += c;
    }
    if (cell || row.length) { row.push(cell); cells.push(row); }
    const [head, ...body] = cells.filter((r) => r.length > 1 || r[0] !== "");
    for (const r of body) rows.push(Object.fromEntries(head.map((h, i) => [h, r[i] ?? ""])));
    return rows;
  }
  const data = fmt === "jsonl" ? text.split("\n").filter((l) => l.trim()).map((l) => JSON.parse(l)) : JSON.parse(text);
  const rows = Array.isArray(data) ? data : data?.rows;
  if (!Array.isArray(rows)) throw new Error("not a table");
  return rows.filter((r) => r && typeof r === "object").map(asText);
}
const tableFormat = (t) => t.format || ({ csv: "csv", jsonl: "jsonl" }[String(t.url || "").split(".").pop().toLowerCase()] || "json");
const num = (v) => { const m = String(v).trim().match(/^(-?\d+)\s*\/\s*(\d+)$/); const x = m ? Number(m[1]) / Number(m[2]) : Number(String(v).trim()); return Number.isFinite(x) ? x : null; };
const rowOpen = (r, t) => { const b = t.bound && String(r[t.bound] ?? "").trim(); if (!b) return true; const v = String(r[t.value] ?? "").trim(); return !(v === b || (num(v) !== null && num(v) === num(b))); };

// A PR (#12 or 12), a commit, or a URL, as a link into the project.
function sourceLink(src, repo) {
  const s = String(src ?? "").trim();
  if (/^#?\d+$/.test(s)) return link(`https://github.com/${repo}/pull/${s.replace("#", "")}`, `#${s.replace("#", "")}`);
  if (/^[0-9a-f]{7,40}$/.test(s)) return link(`https://github.com/${repo}/commit/${s}`, s.slice(0, 7));
  return safeUrl(s) ? link(s, "source") : esc(s);
}
const credit = (by) => (Array.isArray(by) ? by : by ? [by] : []).map((b) => esc(b)).join(", ");

// A step chart of the frontier's value over time, inline SVG. `refs` are dashed reference
// lines (a proven bound, a baseline); `compact` drops the axes, for cards.
const chartPoints = (points) => (points || []).filter((x) => typeof x.number === "number" && Number.isFinite(x.number) && x.date);
function stepChart(points, metricInfo, { refs = [], compact = false, W = 640, H = 180 } = {}) {
  const pts = chartPoints(points);
  if (pts.length < 2) return "";
  const [L, R, T, B] = compact ? [8, 8, 14, 10] : [78, 12, 12, 26];
  const t = pts.map((x) => Date.parse(x.date)), v = pts.map((x) => x.number);
  const rv = refs.map((r) => r.number).filter(Number.isFinite);
  let [t0, t1] = [Math.min(...t), Math.max(...t)], [v0, v1] = [Math.min(...v, ...rv), Math.max(...v, ...rv)];
  if (t1 === t0) t1 = t0 + 86400000;
  if (v1 === v0) { v0 -= Math.abs(v0) * 0.1 || 1; v1 += Math.abs(v1) * 0.1 || 1; }
  const pad = (v1 - v0) * 0.08; v0 -= pad; v1 += pad;
  const X = (x) => L + ((x - t0) / (t1 - t0)) * (W - L - R), Y = (y) => T + (1 - (y - v0) / (v1 - v0)) * (H - T - B);
  let d = `M${X(t[0]).toFixed(1)},${Y(v[0]).toFixed(1)}`;
  // A new formulation is a new problem: start a new line there instead of drawing a jump.
  const breaks = [];
  for (let i = 1; i < pts.length; i++) {
    if ((pts[i].formulation || "") !== (pts[i - 1].formulation || "")) { d += `M${X(t[i]).toFixed(1)},${Y(v[i]).toFixed(1)}`; breaks.push(i); }
    else d += `H${X(t[i]).toFixed(1)}V${Y(v[i]).toFixed(1)}`;
  }
  const area = breaks.length ? "" : `${d}H${(W - R).toFixed(1)}V${(H - B).toFixed(1)}H${X(t[0]).toFixed(1)}Z`;
  const big = Math.max(Math.abs(v0), Math.abs(v1)), sci = big >= 1e5 || big < 1e-2;
  const fmt = (y) => (y === 0 ? "0" : sci ? y.toExponential(2) : String(+y.toPrecision(4)));
  const day = (ms) => new Date(ms).toISOString().slice(0, 10);
  const ticks = [v0 + pad, (v0 + v1) / 2, v1 - pad];
  const refLines = refs.filter((r) => Number.isFinite(r.number)).map((r) => {
    const y = Y(r.number).toFixed(1);
    return `<line x1="${L}" x2="${W - R}" y1="${y}" y2="${y}" class="ref ${esc(r.cls || "")}"/><text x="${W - R - 4}" y="${(+y - 4).toFixed(1)}" text-anchor="end" class="ref-label">${esc(r.label)}</text>`;
  }).join("");
  return `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(metricInfo?.name || "value")} over time" preserveAspectRatio="${compact ? "none" : "xMidYMid meet"}">
      ${compact ? "" : ticks.map((y) => `<line x1="${L}" x2="${W - R}" y1="${Y(y).toFixed(1)}" y2="${Y(y).toFixed(1)}" class="grid"/><text x="${L - 6}" y="${(Y(y) + 4).toFixed(1)}" text-anchor="end">${esc(fmt(y))}</text>`).join("")}
      ${compact ? "" : `<text x="${L}" y="${H - 6}">${esc(day(t0))}</text><text x="${W - R}" y="${H - 6}" text-anchor="end">${esc(day(t1))}</text>`}
      ${area ? `<path d="${area}" class="area"/>` : ""}${refLines}
      ${breaks.map((i) => `<line x1="${X(t[i]).toFixed(1)}" x2="${X(t[i]).toFixed(1)}" y1="${T}" y2="${H - B}" class="ref"/><text x="${(X(t[i]) + 4).toFixed(1)}" y="${T + 10}" class="ref-label">${esc(pts[i].formulation || "new formulation")}</text>`).join("")}
      <path d="${d}" class="line"/>
      ${pts.map((x, i) => `<circle cx="${X(t[i]).toFixed(1)}" cy="${Y(v[i]).toFixed(1)}" r="${compact && i < pts.length - 1 ? 0 : 3}"><title>${esc(`${x.date}: ${x.value}${x.by ? ` (${[].concat(x.by).join(", ")})` : ""}`)}</title></circle>`).join("")}
    </svg>`;
}
function historyChart(points, metricInfo) {
  const svg = stepChart(points, metricInfo);
  return svg ? `<figure class="chart">${svg}
    <figcaption class="hint">${esc(metricInfo?.name || "Value")} at each change of the frontier${metricInfo?.direction ? `; ${esc(metricInfo.direction.replace(/-/g, " "))}` : ""}. A vertical line marks a new formulation, which isn't comparable with the one before.</figcaption>
  </figure>` : "";
}

// --- the hero visual (spec §4, Visual) ----------------------------------------------
// The project's declared visual, else the best the hub can draw from its frontier. An image
// is read as bytes and shown through a blob URL in an <img>, so an SVG's scripts never run.

// --- evaluation suites (spec §5): a method against baselines on held-out instances -----

const STRENGTH = { starter: "the project's starter", published: "a published method", mature: "a mature solver" };
const pct = (g) => (g == null ? "–" : `${g >= 0 ? "+" : ""}${(g * 100).toFixed(Math.abs(g) < 0.01 ? 2 : 1)}%`);
const pval = (p) => (p < 0.001 ? "< 0.001" : p.toFixed(3));
function strengthLine(st) {
  const best = st.strongest_beaten;
  const head = best ? `Beats ${STRENGTH[best]}` : "Doesn't yet beat any baseline significantly";
  return `${head}${st.has_mature ? "" : best === "mature" ? "" : "; not compared with a mature solver"}`;
}
const DRAWS = { fixed: "from a public, fixed set (methods may have been tuned to it)", drawn: "drawn after the method was frozen", sealed: "that the maintainers keep sealed" };

function suiteBars(st, compact) {
  const bs = st.baselines || [];
  if (!bs.length) return "";
  const W = 640, H = compact ? 320 : 220, L = compact ? 150 : 190, R = 70, rowH = (H - 20) / bs.length;
  const gmax = Math.max(0.001, ...bs.map((b) => Math.abs(b.mean_gain || 0)));
  const neg = bs.some((b) => (b.mean_gain || 0) < 0);
  const x0 = neg ? L + (W - L - R) / 2 : L, scale = (neg ? (W - L - R) / 2 : W - L - R) / gmax;
  return `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(`${st.current} against ${bs.length} baselines`)}">
    <line x1="${x0}" x2="${x0}" y1="6" y2="${H - 6}" class="grid"/>
    ${bs.map((b, i) => {
      const y = 10 + i * rowH, g = b.mean_gain || 0, w = Math.abs(g) * scale, x = g >= 0 ? x0 : x0 - w;
      return `<g><title>${esc(`${b.method} (${b.strength}): ${pct(g)} mean, ${b.wins}–${b.ties}–${b.losses}, p = ${pval(b.p)}`)}</title>
        <text x="${L - 10}" y="${(y + rowH / 2 + 4).toFixed(1)}" text-anchor="end" class="bar-label">${esc(b.method)}</text>
        <text x="${L - 10}" y="${(y + rowH / 2 + 18).toFixed(1)}" text-anchor="end" class="bar-sub">${esc(b.strength || "")}</text>
        <rect x="${x.toFixed(1)}" y="${(y + rowH * 0.2).toFixed(1)}" width="${Math.max(1, w).toFixed(1)}" height="${(rowH * 0.6).toFixed(1)}" rx="3" class="bar ${b.verdict}"/>
        <text x="${(g >= 0 ? x + w + 6 : x - 6).toFixed(1)}" y="${(y + rowH / 2 + 4).toFixed(1)}" text-anchor="${g >= 0 ? "start" : "end"}" class="bar-value">${esc(pct(g))}</text></g>`;
    }).join("")}
  </svg>`;
}

function suiteSection(p, st) {
  const rows = (st.baselines || []).map((b) => `<tr><td class="mono">${esc(b.method)}</td><td><span class="badge${b.strength === "mature" ? " accent" : ""}">${esc(b.strength || "")}</span></td>
    <td class="mono">${esc(pct(b.mean_gain))}</td><td class="mono">${esc(`${b.wins}–${b.ties}–${b.losses}`)}</td><td class="mono">${esc(pval(b.p))}</td>
    <td>${b.verdict === "beats" ? '<span class="badge ok">beats</span>' : b.verdict === "loses" ? '<span class="badge warn">loses</span>' : '<span class="badge">inconclusive</span>'}</td>
    <td class="hint">${b.source ? (safeUrl(b.source) ? link(b.source, "source") : esc(b.source)) : ""}${b.version ? ` ${esc(b.version)}` : ""}</td></tr>`).join("");
  const inst = st.held_out || {}, budget = st.budget;
  return `<div><h3 style="margin-bottom:6px">Held-out evaluation</h3>
    <p><b>${esc(strengthLine(st))}.</b> <span class="hint">${esc(st.current)} on ${esc(plural(st.instances, "instance"))} ${esc(DRAWS[inst.draw] || inst.draw || "")}${budget ? `, at ${esc(Number(budget.amount).toLocaleString())} ${esc(budget.unit)} per run` : ""}.</span></p>
    <div class="scroll"><table class="records"><tr><th>Baseline</th><th>Strength</th><th>Mean gain</th><th>W–T–L</th><th>p</th><th></th><th></th></tr>${rows}</table></div>
    <p class="hint">Gain is ${esc(st.objective || "the value")} relative to the baseline, per instance, averaged over seeds; W–T–L counts instances won, tied and lost; p is a two-sided sign test. Computed by the hub from the ${link(st.url, "results file")}.</p></div>`;
}

const VISUAL_KINDS = { witness: "The result itself", derived: "Drawn from the frontier", illustration: "Illustration" };
function heroOf(p, f = p.frontier) {
  if (p.visual) return p.visual;
  if (f?.suite) return { render: "suite", kind: "derived", auto: true };
  if (f?.table) return { render: "records", kind: "derived", auto: true };
  const n = chartPoints(f?.history?.points).length;
  if (n >= 2 && f.metric?.bound) return { render: "bound-gap", kind: "derived", auto: true };
  if (n >= 2) return { render: "progress", kind: "derived", auto: true };
  return { render: "title", auto: true };
}

function recordsGrid(t, rows, compact) {
  if (!rows?.length) return "";
  const shown = rows.slice(0, 400), n = shown.length, W = 640, H = compact ? 320 : 220;
  const cols = Math.max(1, Math.ceil(Math.sqrt((n * W) / H))), rws = Math.ceil(n / cols);
  const cw = W / cols, ch = H / rws, gap = Math.min(cw, ch) * 0.12;
  const label = (r) => t.key.map((k) => r[k]).join(", ");
  return `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(`${n} cases, ${shown.filter((r) => rowOpen(r, t)).length} open`)}">
    ${shown.map((r, i) => {
      const x = (i % cols) * cw, y = Math.floor(i / cols) * ch, open = rowOpen(r, t);
      const fs = Math.min(ch * 0.26, (cw / Math.max(3, label(r).length + 1)) * 1.6);
      return `<g><title>${esc(`${label(r)}: ${r[t.value]}${open ? " (open)" : " (settled)"}`)}</title>
        <rect x="${(x + gap / 2).toFixed(1)}" y="${(y + gap / 2).toFixed(1)}" width="${(cw - gap).toFixed(1)}" height="${(ch - gap).toFixed(1)}" rx="${(gap * 0.8).toFixed(1)}" class="${open ? "open" : "settled"}"/>
        ${fs >= 9 ? `<text x="${(x + cw / 2).toFixed(1)}" y="${(y + ch / 2 + fs * 0.35).toFixed(1)}" text-anchor="middle" style="font-size:${fs.toFixed(1)}px">${esc(label(r))}</text>` : ""}</g>`;
    }).join("")}
  </svg>`;
}

function titleCard(p, f) {
  const m = f?.metric;
  return `<div class="title-card">${m
    ? `<span class="n">${esc(m.name)}</span><span class="v">${esc(m.decimal || m.value)}${m.unit ? ` ${esc(m.unit)}` : ""}</span>`
    : `<span class="t">${esc(p.title)}</span>`}<span class="n">${esc(p.domains.join(" · "))}</span></div>`;
}

const imgTag = (p, v) => `<img data-visual="${esc(p.slug)}" alt="${esc(v.alt || "")}" hidden>`;
function heroInner(p, f, compact) {
  const v = heroOf(p, f);
  const refs = v.render === "bound-gap" ? [
    ...(f?.metric?.bound ? [{ number: num(f.metric.bound), label: `proven bound ${f.metric.bound}`, cls: "bound" }] : []),
    ...(v.baseline ? [{ number: num(v.baseline.value), label: v.baseline.label || `baseline ${v.baseline.value}`, cls: "base" }] : []),
  ] : [];
  const W = 640, H = compact ? 320 : 220;
  if (v.render === "image") return imgTag(p, v);
  if (v.render === "suite" && f?.suite) return suiteBars(f.suite, compact);
  if (v.render === "records" && f?.table) return recordsGrid(f.table, f.table.live_rows || f.table.rows_snapshot, compact);
  if (["progress", "bound-gap"].includes(v.render)) return stepChart(f?.history?.points, f?.metric, { refs, compact, W, H }) || titleCard(p, f);
  return titleCard(p, f);
}

function heroCaption(p, f) {
  const v = heroOf(p, f);
  if (v.render === "title") return "";
  const auto = { records: "Each case in the record table: filled when settled, outlined while open.",
    suite: `How much better ${f?.suite?.current || "the method"} does than each baseline, on average over ${f?.suite?.instances || "the"} held-out instances. Solid bars are significant on a sign test.`,
    progress: `${f?.metric?.name || "The value"} at each change of the frontier${f?.metric?.direction ? `; ${f.metric.direction.replace(/-/g, " ")}` : ""}.` };
  auto["bound-gap"] = `${auto.progress.slice(0, -1)}, against ${[f?.metric?.bound ? "the proven bound" : "", v.baseline ? "where it started" : ""].filter(Boolean).join(" and ") || "its range"}.`;
  const text = v.caption || (v.render === "image" ? v.alt : auto[v.render]);
  const prompt = v.prompt ? `<details><summary class="hint">Made by an image model</summary><p class="hint">The prompt, filled from the frontier when the hub last built: ${esc(v.prompt)}</p></details>` : "";
  const src = v.url ? ` · ${link(v.url, v.origin === "adapter" ? "image (hub)" : "image")}` : "";
  return `<figcaption><span class="badge">${esc(VISUAL_KINDS[v.kind] || v.kind)}</span> <span class="hint">${esc(text || "")}${src}</span>${prompt}</figcaption>`;
}

function heroFigure(p, f, compact) {
  const v = heroOf(p, f);
  return `<figure class="hero-vis ${compact ? "compact" : ""} r-${esc(v.render)}">
    <div class="frame">${heroInner(p, f, compact)}${compact && v.render === "image" && v.kind ? `<span class="badge kind">${esc(VISUAL_KINDS[v.kind])}</span>` : ""}</div>
    ${compact ? "" : heroCaption(p, f)}</figure>`;
}

// Show images: the build's copy (same origin), then on a project page the project's own,
// read live. Both are read as bytes and typed by the declaration, not by the server.
const IMAGE_MAX_BYTES = 1_000_000, blobUrls = {};
async function imageUrl(url, type, upstream) {
  const key = `${url}|${type}`;
  if (blobUrls[key]) return blobUrls[key];
  if (upstream && (!safeUrl(url) || !url.startsWith("https://raw.githubusercontent.com/"))) throw new Error("not a project URL");
  const r = await fetch(url, { cache: "no-cache" });
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  const bytes = await r.arrayBuffer();
  if (bytes.byteLength > IMAGE_MAX_BYTES) throw new Error("too large");
  return (blobUrls[key] = URL.createObjectURL(new Blob([bytes], { type })));
}
function showImages(root, live = false) {
  root.querySelectorAll("img[data-demo]").forEach(async (img) => {
    const [slug, i] = img.dataset.demo.split("|");
    const t = state.data.projects.find((x) => x.slug === slug)?.demos?.[i]?.image;
    if (!t?.snapshot) return;
    try { img.src = await imageUrl(t.snapshot, t.type, false); img.hidden = false; } catch { /* no thumbnail */ }
  });
  root.querySelectorAll("img[data-visual]").forEach(async (img) => {
    const p = state.data.projects.find((x) => x.slug === img.dataset.visual), v = p?.visual;
    if (!v?.snapshot) return;
    try { img.src = await imageUrl(v.snapshot, v.type, false); img.hidden = false; } catch { /* keep the frame empty */ }
    if (live && v.live_url) {
      try { img.src = await imageUrl(v.live_url, v.type, true); img.hidden = false; } catch { /* the build's copy stays */ }
    }
  });
}

// Demos are the project's own pages: linked, never served from the hub, and labelled so.
const DEMO_KINDS = { replay: "Replay", dashboard: "Dashboard", explorer: "Explorer" };
function demoData(d, f) {
  if (d.reads_record) return "Shows the checked frontier record, as of its last deployment.";
  if (d.stale) return `Its data was last changed ${d.data_on}, before the frontier was updated (${f?.updated_on}); it may show an earlier result.`;
  if (d.data_on) return `Its data was last changed ${d.data_on}.`;
  return d.reads?.length ? "" : "Doesn't say what data it shows.";
}
function demosPanel(p) {
  if (!p.demos?.length) return "";
  return `<section class="panel" id="demos-panel"><h2>Explore</h2>
    <p class="hint">Pages the project built and hosts. They run on the project's site, and the hub hasn't checked what they show.</p>
    <ul class="demos">${p.demos.map((d, i) => `<li class="demo">
      ${d.image ? `<div class="thumb"><img data-demo="${esc(p.slug)}|${i}" alt="${esc(d.alt || "")}" hidden></div>` : ""}
      <div><div class="row">${d.kind ? `<span class="badge">${esc(DEMO_KINDS[d.kind] || d.kind)}</span>` : ""}${d.stale ? '<span class="badge warn">Older than the frontier</span>' : ""}</div>
        <h3>${link(d.url, `${d.title} ↗`)}</h3>
        ${d.note ? `<p class="hint">${esc(d.note)}</p>` : ""}
        <p class="hint">${esc(demoData(d, p.frontier))}${d.reads?.length ? ` Reads ${d.reads.map((r) => link(r.url, r.path)).join(", ")}.` : ""}${d.source_url ? ` ${link(d.source_url, "Source")}.` : ""}</p></div>
    </li>`).join("")}</ul></section>`;
}

function historySection(p, f) {
  const h = f.history;
  if (!h?.points?.length) return "";
  const origin = h.from === "project" ? "the project's history file" : "the frontier record's git history";
  const rows = h.points.slice().reverse().map((x) => `<tr><td>${esc(x.date)}</td><td class="mono">${esc(x.value)}</td><td>${credit(x.by)}</td><td>${x.source ? sourceLink(x.source, p.repo) : ""}${x.note ? ` <span class="hint">${esc(x.note)}</span>` : ""}</td></tr>`).join("");
  // The hero already charts it when it's a progress chart.
  const charted = ["progress", "bound-gap"].includes(heroOf(p, f).render);
  return `<div><h3 style="margin-bottom:6px">Progress</h3>${charted ? "" : historyChart(h.points, f.metric)}
    <details><summary>${esc(plural(h.points.length, "change"))}, from ${esc(origin)}</summary>
    <div class="scroll"><table class="records"><tr><th>Date</th><th>Value</th><th>By</th><th>Source</th></tr>${rows}</table></div></details></div>`;
}

function frontierInner(p, f, origin) {
  const assumptions = f.open_assumptions?.length
    ? `<div><h3 style="margin-bottom:6px">Open obligations</h3><ul class="qlist">${f.open_assumptions.map((a) => `<li>${esc(a.statement)}${a.link ? ` (${link(a.link, "link")})` : ""}</li>`).join("")}</ul></div>` : "";
  const where = origin?.live ? `read live from the project ${esc(origin.at)}` : f.live ? `snapshot from the hub's last build${origin?.error ? ` (couldn't read it live: ${esc(origin.error)})` : ""}` : "";
  return `<h2>Current frontier</h2>
    ${metric(f)}
    <p>${esc(f.statement)}</p>
    ${f.formulation ? `<p class="hint">Formulation ${f.formulation.doc_url ? link(f.formulation.doc_url, f.formulation.id) : `<code>${esc(f.formulation.id)}</code>`}${f.formulation.since ? ` since ${esc(f.formulation.since)}` : ""}${f.formulation.replaces ? `; replaces <code>${esc(f.formulation.replaces)}</code>, so earlier results aren't comparable` : ""}</p>` : ""}
    ${f.table ? `<p class="hint">A table of ${esc(plural(f.table.rows, "case"))}, ${esc(f.table.open)} still open · ${link(f.table.url, "table")}</p>` : ""}
    <div class="row" style="display:flex;flex-wrap:wrap;gap:6px">${claimBadges(f.claim_kind)}${(f.evidence_level || []).map((e) => `<span class="badge ok">${esc(e.replace(/-/g, " "))}</span>`).join("")}</div>
    ${f.external?.length ? `<p class="hint">Accepted by ${f.external.map((x) => link(x.url, x.authority)).join(", ")}</p>` : ""}
    ${f.scope ? `<details><summary>Scope and conditions</summary><p class="hint">${esc(f.scope)}</p></details>` : ""}
    ${assumptions}
    ${f.suite ? suiteSection(p, f.suite) : ""}
    ${historySection(p, f)}
    <p class="hint">Updated ${esc(f.updated_on || "unknown")} · ${link(f.record_url, "record")}${where ? ` · ${where}` : ""}</p>`;
}

// The record table as a leaderboard of cases (not of people): value, bound, credit, source.
function recordsInner(p, t, rows, origin) {
  const cols = [...t.key, t.value, ...(t.bound ? [t.bound] : [])];
  const openOnly = state.openOnly ?? true;
  const shown = rows.filter((r) => !openOnly || rowOpen(r, t));
  const head = `<tr>${cols.map((c) => `<th>${esc(c)}</th>`).join("")}<th></th>${t.by ? "<th>By</th>" : ""}${t.source ? "<th>Source</th>" : ""}${t.updated ? "<th>Updated</th>" : ""}</tr>`;
  const body = shown.slice(0, 1000).map((r) => `<tr>${cols.map((c) => `<td class="mono">${esc(r[c])}</td>`).join("")}<td>${rowOpen(r, t) ? '<span class="badge accent">open</span>' : '<span class="badge ok">settled</span>'}</td>${t.by ? `<td>${esc(r[t.by])}</td>` : ""}${t.source ? `<td>${r[t.source] ? sourceLink(r[t.source], p.repo) : ""}</td>` : ""}${t.updated ? `<td>${esc(r[t.updated])}</td>` : ""}</tr>`).join("");
  const where = origin?.live ? `Read live from the project ${esc(origin.at)}` : `Snapshot from the hub's last build${t.truncated ? " (first rows only)" : ""}${origin?.error ? `; couldn't read it live: ${esc(origin.error)}` : ""}`;
  return `<h2>Records</h2>
    <p class="hint">One row per case. A case is open until its value meets its proven bound.</p>
    <label class="hint"><input type="checkbox" data-open-only ${openOnly ? "checked" : ""}> Open cases only (${esc(rows.filter((r) => rowOpen(r, t)).length)} of ${esc(rows.length)})</label>
    <div class="scroll"><table class="records">${head}${body}</table></div>
    ${shown.length > 1000 ? `<p class="hint">Showing 1,000 of ${esc(shown.length)}; the full table is in the ${link(t.url, "repository")}.</p>` : ""}
    <p class="hint">${where} · ${link(t.url, "table")}</p>`;
}

function wireRecords(root, p, t, rows, origin) {
  const box = root.querySelector("#records-panel");
  if (!box) return;
  box.innerHTML = recordsInner(p, t, rows, origin);
  box.querySelector("[data-open-only]")?.addEventListener("change", (e) => { state.openOnly = e.target.checked; wireRecords(root, p, t, rows, origin); });
}

async function loadLive(root, p) {
  const f = p.frontier, live = f?.live;
  if (!live?.url) return;
  const at = () => `at ${new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}`;
  const panel = () => root.querySelector("#frontier-panel");
  let cur = f;
  const showHero = () => {
    const box = root.querySelector("#hero-panel");
    if (box) { box.innerHTML = heroFigure(p, cur, false); showImages(box, true); }
  };
  try {
    const rec = mapFrontier(JSON.parse(await fetchUpstream(live.url)), live.map);
    if (!rec || typeof rec.statement !== "string") throw new Error("not a frontier record");
    const g = liveFields(rec, f);
    const last = g.history?.points?.at(-1), now = g.metric?.value;
    if (g.history && now && last && last.value !== now) {
      g.history = { ...g.history, points: [...g.history.points, { date: (g.updated_on || new Date().toISOString()).slice(0, 10), value: now, number: num(g.metric.decimal || now), note: "current" }] };
    }
    if (panel()) panel().innerHTML = frontierInner(p, g, { live: true, at: at() });
    cur = g;
    showHero();
  } catch (e) {
    if (panel()) panel().innerHTML = frontierInner(p, f, { error: e.message });
  }
  if (f.table && live.table_url) {
    try {
      const rows = parseTable(await fetchUpstream(live.table_url), tableFormat({ ...f.table, url: live.table_url }));
      wireRecords(root, p, f.table, rows, { live: true, at: at() });
      cur = { ...cur, table: { ...cur.table, live_rows: rows } };
      showHero();
    } catch (e) {
      wireRecords(root, p, f.table, f.table.rows_snapshot || [], { error: e.message });
    }
  }
}

function viewProject(slug) {
  const p = state.data.projects.find((x) => x.slug === slug);
  if (!p) return `<div class="empty">No project “${esc(slug)}”. <a href="#/">Back to explore</a></div>`;
  const f = p.frontier;
  // The agent entry point is named by its file: an adapter may point at README.md instead of AGENTS.md.
  const LINK_NAMES = { project: "Project guide", contributing: "Contributing", brief: "Bottleneck brief", glossary: "Glossary" };
  const links = [link(p.url, "Repository"),
    ...Object.entries(p.links).map(([k, u]) => link(u, k === "agents" ? String(u).split("/").pop() : LINK_NAMES[k] || k)),
    ...(p.discussions.all ? [link(p.discussions.all, "Discussions")] : []),
    ...(p.assessment_url ? [link(p.assessment_url, "Hub assessment")] : []),
    ...(p.adapter_url ? [link(p.adapter_url, "Hub adapter")] : [])].map((l) => `<li>${l}</li>`).join("");
  const board = p.board?.open_handoffs?.length
    ? `<section class="panel"><h2>Open handoffs</h2>
      <ul class="clean">${p.board.open_handoffs.map((h) => `<li>${link(h.url, h.question)}<div class="hint">${esc(h.track || "any track")}${h.est_minutes ? ` · ~${esc(h.est_minutes)} min` : ""}</div></li>`).join("")}</ul>
      <p class="hint">Requests left by earlier sessions. Donated sessions take these up first.</p></section>` : "";
  return `
  <div class="page-head">
    <div class="crumbs"><a href="#/">Explore</a> <span class="muted">/ ${esc(p.repo)}</span></div>
    <h1>${esc(p.title)}</h1>
    <p class="lede">${esc(p.summary)}</p>
    <div class="row">${stageBadge(p)}${reviewBadge(p)}${p.verification_profile ? `<span class="badge">${esc(PROFILES[p.verification_profile] || p.verification_profile)}</span>` : ""}<span class="muted" style="font-size:13px">${esc(p.domains.join(" · "))}</span></div>
  </div>
  <div class="layout">
    <div class="side">${p.listing === "nominated" ? nominatedPanel(p) : p.review?.paused ? pausedPanel() : launcher(p)}</div>
    <div class="main">
      <section class="panel hero-panel" id="hero-panel">${heroFigure(p, f, false)}</section>
      ${demosPanel(p)}
      ${f ? `<section class="panel" id="frontier-panel">${frontierInner(p, f, null)}</section>
      ${f.table ? `<section class="panel" id="records-panel">${recordsInner(p, f.table, f.table.rows_snapshot || [], null)}</section>` : ""}` : p.frontier_doc ? `<section class="panel">
        <h2>Current result</h2>
        <p>The project states its current result in ${link(p.frontier_doc.url, p.frontier_doc.path)}.</p>
        ${p.frontier_doc.note ? `<p class="hint">${esc(p.frontier_doc.note)}</p>` : ""}
      </section>` : ""}
      ${p.tracks.length ? `<section class="panel">
        <h2>Where effort goes</h2>
        <p class="hint">How the project splits donated sessions across its tracks${p.priority_revision ? ` (revision ${esc(p.priority_revision)})` : ""}. Open a track to see its tasks.</p>
        ${trackBar(p.tracks)}
        <div class="legend">${p.tracks.map((t, i) => `<div class="legend-row"><span class="sw" style="background:var(--track-${(i % TRACK_COLORS) + 1})"></span>
          <details><summary>${esc(t.id)}</summary>${t.useful_outcome ? `<p class="hint" style="margin-bottom:6px">${esc(t.useful_outcome)}</p>` : ""}<ul class="qlist">${t.cards.map((c) => `<li><code>${esc(c.id)}</code>: ${esc(c.question)}${c.rows || c.claim_kind?.length ? `<div class="hint">${[c.rows ? "any open case in the table" : "", ...(c.claim_kind || []).map((k) => CLAIM_KINDS[k] || k)].filter(Boolean).map(esc).join(" · ")}</div>` : ""}</li>`).join("")}</ul></details>
          <span class="w">${esc(t.weight)}%</span></div>`).join("")}</div>
      </section>` : ""}
      ${board}
      <section class="panel">
        <h2>About</h2>
        <dl class="kv">${p.maintainers.map((m) => `<dt>Maintainer</dt><dd>${m.github ? link(`https://github.com/${m.github}`, m.name) : esc(m.name)}</dd>`).join("")}<dt>Credit</dt><dd>${p.credit && p.credit.policy ? esc(p.credit.policy) : '<span class="muted">Not stated yet</span>'}</dd>${p.license ? `<dt>License</dt><dd>${esc(p.license)}</dd>` : ""}${p.listing === "nominated" ? "" : `<dt>Review</dt><dd>${reviewText(p.review)}</dd>`}${p.requirements ? `<dt>Needs</dt><dd>${esc(needsText(p.requirements))}</dd>` : ""}</dl>
        <ul class="links">${links}</ul>
      </section>
    </div>
  </div>`;
}

const PROPS = ["orientation", "coordination", "verification", "review", "steering"];
const stageText = (st) => (st === undefined || st === null ? "not assessed" : STAGES[st] || String(st));

function gradesTable(p) {
  const asIs = p.grades, proj = p.projected?.grades;
  if (!asIs && !proj) return '<p class="hint">Not assessed yet.</p>';
  const cell = (g) => esc(g || "·");
  return `<table class="grades"><tr><th></th><th>As is</th>${proj ? "<th>After setup</th>" : ""}</tr>${PROPS.map((k) =>
    `<tr><td>${k[0].toUpperCase()}${k.slice(1)}</td><td>${cell(asIs?.[k])}${k === "verification" && p.verification_covers?.length ? `<br><span class="muted" style="font-size:12px">checks: ${esc(p.verification_covers.join(", "))}</span>` : ""}</td>${proj ? `<td>${cell(proj[k])}</td>` : ""}</tr>`).join("")}
    <tr><td><b>Stage</b></td><td>${esc(stageText(p.stage))}</td>${proj ? `<td>${esc(stageText(p.projected.stage))}</td>` : ""}</tr></table>`;
}

function nominatedPanel(p) {
  const n = p.nomination || {};
  const proposal = safeUrl(n.proposal);
  const prompt = onboardPrompt("maintainer", "setup-and-submit", p.repo, proposal ? `${proposal} (a proposal from @${n.by})` : null);
  return `
  <section class="panel sticky">
    <h2>Not open for contributions yet</h2>
    <p class="hint">${n.by ? `Nominated by ${link(`https://github.com/${n.by}`, "@" + n.by)}${n.on ? ` on ${esc(n.on)}` : ""}. ` : ""}The project is catalogued because it looks suitable, but its maintainers haven't opted in, so the hub sends it no agents and hasn't contacted them.</p>
    ${gradesTable(p)}
    ${proposal ? `<p class="hint">Setup was proposed to the maintainers: ${link(proposal, "proposal issue")}${safeUrl(n.draft) ? ` · ${link(n.draft, "draft")}` : ""}.</p>` : ""}
    <h3 style="margin-bottom:0">Maintain this project?</h3>
    <p class="hint">Paste this into your coding agent to set it up and list it. It interviews you and asks before every public step.</p>
    <div class="codebox">${esc(prompt)}</div>
    <div class="copy-row"><button class="btn primary" data-copy-text="${esc(prompt)}">Copy prompt</button></div>
    <p class="hint">Rather not be catalogued? Add <code>.github/discover-hubs.json</code> containing <code>{"hubs": [{"hub": "*", "list": false}]}</code>. The entry disappears at the hub's next build.</p>
  </section>`;
}

function explorePrompt(minutes, perms, interests, seed) {
  const p = state.data.prompts;
  const i = interests.trim().replace(/[.\s]+$/, "");
  return fill(p.explore, { site: p.site, minutes, permissions: p.permissions[perms], seed,
    interests: i ? fill(p.explore_interests, { interests: i }) : "" });
}

function donateAnywhere() {
  const open = state.data.projects.filter((p) => p.listing === "listed" && [0, 1, 2].includes(p.stage) && p.conformant && !p.review?.paused);
  const domains = [...new Set(open.flatMap((p) => p.domains))].sort();
  return `
  <section class="panel" id="donate-anywhere"><h2>Donate wherever it's useful</h2>
    <p class="hint">Your agent draws one of the ${plural(open.length, "open project")} for you, works there, and leaves a receipt saying where the time went.</p>
    <div class="field"><label>Budget</label>${seg("dminutes", [[60, "1 hour"], [240, "4 hours"], [480, "8 hours"]], 240)}</div>
    <div class="field"><label>On GitHub</label>${seg("dperms", [["local", "Nothing public"], ["post", "May post & PR"]], "local")}</div>
    <div class="field"><label for="d-interests">Interests <span class="muted">(optional)</span></label>
      <input id="d-interests" class="search" type="text" placeholder="e.g. number theory, performance" maxlength="200">
      <div class="chips">${domains.map((d) => `<button type="button" class="chip" data-interest="${esc(d)}">${esc(d)}</button>`).join("")}</div></div>
    ${promptBox("explore")}
    <p class="hint">Each copy has a fresh seed, so copy a new prompt for each run. Prefer a particular project? <a href="#/">Pick one on Explore</a>.</p>
  </section>`;
}

function wirePrepare(root) {
  const box = root.querySelector("#prepare-setup"); if (!box) return;
  const p = state.data.prompts;
  const refresh = () => {
    const preset = box.querySelector('[data-seg="preset"] [aria-pressed="true"]')?.dataset.v || "donor";
    box.querySelector('[data-out="prepare"]').textContent = fill(p.prepare, { site: p.site, preset });
  };
  box.querySelectorAll("[data-seg]").forEach((g) => g.addEventListener("click", (e) => {
    const b = e.target.closest("button"); if (!b) return;
    g.querySelectorAll("button").forEach((x) => x.setAttribute("aria-pressed", String(x === b)));
    refresh();
  }));
  refresh();
}

function wireDonate(root) {
  const box = root.querySelector("#donate-anywhere"); if (!box) return;
  const val = (n) => box.querySelector(`[data-seg="${n}"] [aria-pressed="true"]`)?.dataset.v;
  const input = box.querySelector("#d-interests");
  const seed = newSeed();
  const refresh = () => { box.querySelector('[data-out="explore"]').textContent = explorePrompt(val("dminutes"), val("dperms"), input.value, seed); };
  box.querySelectorAll("[data-seg]").forEach((g) => g.addEventListener("click", (e) => {
    const b = e.target.closest("button"); if (!b) return;
    g.querySelectorAll("button").forEach((x) => x.setAttribute("aria-pressed", String(x === b)));
    refresh();
  }));
  box.querySelectorAll("[data-interest]").forEach((b) => b.addEventListener("click", () => {
    const have = input.value.split(",").map((s) => s.trim()).filter(Boolean);
    if (!have.includes(b.dataset.interest)) input.value = [...have, b.dataset.interest].join(", ");
    refresh();
  }));
  input.addEventListener("input", refresh);
  refresh();
}

function viewContribute() {
  return `
  <div class="page-head"><h1>Donate your agent's time</h1>
    <p class="lede">You bring the agent and the inference; projects bring the questions and the review. Every way to help is a prompt you paste into Claude Code, Codex or any coding agent.</p></div>
  <div class="cols">
    ${donateAnywhere()}
    <section class="panel" id="prepare-setup"><h2>Sandbox your sessions <span class="badge accent">once, recommended</span></h2>
      <p class="hint">Start your agent in the folder you'll donate from (or a clone you keep) and paste this. It sets up the folder, asking first. Restart your agent there, and every session after is sandboxed and limited on GitHub.</p>
      <div class="field"><label>Sessions there will be</label>${seg("preset", [["donor", "Watched by me"], ["donor-local", "Unattended, local"], ["donor-post", "Unattended, may post"]], "donor")}</div>
      ${promptBox("prepare")}
      <details><summary>Or set it up by hand</summary>
        <div class="codebox">python3 discover.pyz permissions donor --write .claude/settings.local.json</div>
        <p class="hint">With the helper (<code>discover.pyz</code>) in the folder. For Codex: <code>--agent codex --write .</code>, then trust the folder when Codex asks.</p>
      </details>
    </section>
  </div>
  <section class="panel" style="margin-top:16px"><h2>What a session does</h2>
    <ul class="qlist">
      <li>Works in its own folder and clone, never in your checkouts.</li>
      <li>Takes up an open handoff, else a task drawn at random by seed, so donors spread across the work.</li>
      <li>Keeps the last quarter of its budget for verification, and says what it didn't check.</li>
      <li>Posts or opens a PR only if you allowed it, then gives you a short receipt.</li>
      <li>Never merges, closes others' work or changes a project's accepted result. Nothing in a repository can widen what you allowed.</li>
    </ul>
    <details><summary>What protects your machine</summary>
      <ul class="qlist">
        <li><b>Screening.</b> Projects are screened when they apply, and your agent screens its own copy before running anything. A finding stops it running the project's code until you've looked.</li>
        <li><b>The sandbox</b> (with the setup above). Commands write only inside the folder you started in, can't read your SSH, cloud or registry credentials, and reach only GitHub, this site, package registries and the main literature sites. Your agent's own web search stays open for research.</li>
        <li><b>Repo settings stay off.</b> A project's own agent hooks and MCP servers don't load: sessions start outside the clone, and in a clone you keep, the setup turns them off.</li>
        <li><b>Not covered:</b> tokens a tool holds. Code inside the sandbox can still ask <code>gh</code> for your GitHub token. For untrusted code, use a container or VM with a <a href="https://github.com/settings/personal-access-tokens/new" target="_blank" rel="noopener">read-only fine-grained token</a>, or none for local-only sessions.</li>
      </ul>
    </details>
    <details><summary>Installing a sandbox (Linux, Windows)</summary>
      <p class="hint"><b>macOS:</b> built in. <b>Linux:</b> install bubblewrap and socat, restart your agent, and check with <code>/sandbox</code> in Claude Code.</p>
      <div class="codebox">sudo apt install bubblewrap socat     # Debian, Ubuntu
sudo dnf install bubblewrap socat     # Fedora
sudo pacman -S bubblewrap socat       # Arch</div>
      <p class="hint"><b>Windows:</b> run your agent in WSL2. In PowerShell as administrator run <code>wsl --install</code> and restart; then in Ubuntu run the line below, <a href="https://code.claude.com/docs/en/setup" target="_blank" rel="noopener">install Claude Code</a> there, and donate from a folder in the Linux filesystem (not under <code>/mnt/c</code>). Without a sandbox, sessions still run, and the setup tells you they aren't sandboxed.</p>
      <div class="codebox">sudo apt update &amp;&amp; sudo apt install bubblewrap socat git python3</div>
    </details>
    <details><summary>Claude Code plugin</summary>
      <p class="hint">Adds the playbooks as skills, with the helper built in.</p>
      <div class="codebox">${esc(installLine())}</div>
      <div class="copy-row"><button class="btn" data-copy-text="${esc(installLine())}">Copy</button></div>
    </details>
  </section>`;
}

const ONBOARD_CHOICES = {
  maintainer: [
    ["setup-and-submit", "Set up and list my project", "Your agent interviews you (about 15 minutes), adds a few files on a branch, opens a PR for you to merge, then applies to the hub."],
    ["evaluate", "Just evaluate it", "Read-only. See how a donated agent would find your project today, and what would help most."],
    ["setup", "Set it up only", "Make it agent-ready now and decide about listing later."],
    ["submit", "List it as is", "Nothing changes in your repo. The hub maps where things live before listing it."],
  ],
  contributor: [
    ["propose-and-nominate", "Propose it to the maintainers and nominate it", "Your agent evaluates the project and drafts a setup, then opens one friendly issue with a prompt the maintainers can paste to go ahead. It also catalogues the project on the hub, without sending it any agents."],
    ["evaluate", "Just evaluate it", "Read-only. A report for you on how agents would find the project."],
    ["nominate", "Nominate it", "Catalogue it on the hub without contacting anyone. No agents are sent to it until its maintainers opt in."],
    ["propose", "Propose setup to the maintainers", "One issue on the project with an evaluation and a prompt they can paste. Nothing on the hub."],
  ],
};

function startPrompt(problem, local) {
  const p = state.data.prompts;
  return fill(p.start, { site: p.site, problem: problem.trim() || "DESCRIBE THE PROBLEM, OR PASTE A LINK TO IT", mode: local ? p.start_local : "" });
}

function onboardPrompt(role, goal, repo, context) {
  const p = state.data.prompts;
  return fill(p.onboard, { site: p.site, role, goal, repo_url: `https://github.com/${repo}`, context: context ? fill(p.onboard_context, { context }) : "" });
}

const parseRepo = (text) => {
  const m = String(text || "").trim().replace(/\.git$/, "").replace(/\/+$/, "").match(/(?:github\.com\/)?([A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+)$/);
  return m ? m[1] : null;
};

function choiceButton([goal, title, body], extra = "") {
  return `<button type="button" class="choice ${extra}" data-goal="${goal}" aria-pressed="false">${extra ? '<span class="tag">Recommended</span>' : ""}<b>${esc(title)}</b><span>${esc(body)}</span></button>`;
}

function viewAdd() {
  const form = hubUrl("/issues/new?template=add-project.yml");
  const goals = (role) => {
    const [first, ...rest] = ONBOARD_CHOICES[role];
    return `<div data-goals="${role}" style="display:none;gap:10px">${choiceButton(first, "recommended")}<div class="choices secondary">${rest.map((c) => choiceButton(c)).join("")}</div></div>`;
  };
  return `
  <div class="page-head"><h1>Add a project</h1>
    <p class="lede">A research problem where agents could help: proofs, constructions, benchmarks, replications or audits. Answer two questions, then paste the prompt into your coding agent. It asks before anything public.</p></div>
  <div class="tree">
    <section class="panel"><div class="step-label">1 · You are</div>
      <div class="choices">
        <button type="button" class="choice" data-role="maintainer" aria-pressed="false"><b>The project's maintainer</b><span>You run the repository and review contributions to it.</span></button>
        <button type="button" class="choice" data-role="contributor" aria-pressed="false"><b>Someone who'd like to bring it here</b><span>You don't maintain it, but think agents could help it.</span></button>
        <button type="button" class="choice" data-role="new" aria-pressed="false"><b>Starting a new project</b><span>You have a problem, not a repository yet. Build it ready for donors from the first commit.</span></button>
      </div>
    </section>
    <section class="panel" data-step="goal" style="display:none"><div class="step-label" data-goal-label>2 · You want to</div>${goals("maintainer")}${goals("contributor")}
      <div data-goals="new" style="display:none;gap:10px">
        <div class="field"><label for="add-problem" class="visually-hidden">The problem</label>
          <textarea id="add-problem" class="repo-input" rows="6" placeholder="Describe the problem in your own words, or paste a link to it (an Erdős problem, an open question from a paper)."></textarea></div>
        <label class="hint" style="display:flex;gap:8px;align-items:center"><input type="checkbox" id="add-local"> Build it on my machine first, without creating anything on GitHub</label>
        <p class="hint">Your agent checks what's already known (with sources) before building on any claim in your description, builds a checker for results before any research, and asks who will maintain the project. A project can be built without a maintainer, but it can't take donated sessions until someone agrees to review them.</p>
      </div>
    </section>
    <section class="panel" data-step="prompt" style="display:none"><div class="step-label">3 · Paste this into your agent</div>
      <div class="field" data-repo-field><label for="add-repo">Repository</label><input id="add-repo" class="repo-input" placeholder="https://github.com/OWNER/REPO" autocomplete="off" spellcheck="false"></div>
      ${promptBox("onboard")}
      <p class="hint" data-out="onboard-note"></p>
    </section>
  </div>
  <details class="panel" style="margin-top:24px;max-width:820px"><summary><h2 style="display:inline">How projects are assessed</h2></summary>
    <p class="hint">The hub grades five properties, each strong, adequate or weak, from what's true now, not from your project's history (${link(hubUrl("/blob/main/spec/v0.md"), "spec §3")}):</p>
    <ul class="qlist">
      <li><b>Orientation</b>: can a fresh agent learn the problem, what's accepted, where help is wanted, and how to contribute?</li>
      <li><b>Coordination</b>: do agents spread across the work, and can they tell what's open? GitHub Discussions helps most here.</li>
      <li><b>Verification</b>: is there one authoritative record of what's accepted, and can someone else recheck it?</li>
      <li><b>Review</b>: does review keep up? Independent checks by other contributors count.</li>
      <li><b>Steering</b>: are priorities stated in one place and revised from evidence?</li>
    </ul>
    <p class="hint">Stages built on these decide what donated sessions may do, from local-only to posting and PRs. Only maintainers can opt a project in; a nominated project is catalogued with its assessment but no launcher. Computational and mathematical projects where results can be checked cheaply fit best today. Projects involving human subjects, restricted data, wet-lab or dual-use work need extra screening.</p>
    <p class="hint">Prefer a form? ${link(form, "Apply or nominate directly")}.</p>
  </details>`;
}

const ONBOARD_NOTES = {
  "setup-and-submit": "It asks about ten questions, shows every diff, and asks before pushing, opening the PR, enabling Discussions or posting the application.",
  setup: "It asks about ten questions, shows every diff, and asks before pushing or opening the PR.",
  submit: "It drafts the application and asks before posting it on the hub.",
  evaluate: "Read-only: it clones the repository and reports to you. Nothing is posted anywhere.",
  "propose-and-nominate": "It first checks the project hasn't opted out or already been proposed. It shows you the issue and the nomination before posting either, and never pushes to the project.",
  propose: "It first checks the project hasn't opted out or already been proposed, and shows you the issue before posting. It never pushes to the project.",
  nominate: "It checks the project hasn't opted out and asks before posting the nomination. The project isn't contacted.",
};

function wireAdd(root) {
  let role = null, goal = null;
  const show = (sel, on) => { const el = root.querySelector(sel); if (el) el.style.display = on ? "grid" : "none"; };
  const refresh = () => {
    show('[data-step="goal"]', !!role);
    root.querySelectorAll("[data-goals]").forEach((el) => { el.style.display = el.dataset.goals === role ? "grid" : "none"; });
    const isNew = role === "new";
    root.querySelector("[data-goal-label]").textContent = isNew ? "2 · Your problem" : "2 · You want to";
    show('[data-step="prompt"]', !!(role && (goal || isNew)));
    show("[data-repo-field]", !isNew);
    if (isNew) {
      root.querySelector('[data-out="onboard"]').textContent = startPrompt(root.querySelector("#add-problem").value, root.querySelector("#add-local").checked);
      root.querySelector('[data-out="onboard-note"]').textContent = "It interviews you to sharpen the question, and asks before creating a repository, pushing or posting.";
      return;
    }
    if (!(role && goal)) return;
    const repo = parseRepo(root.querySelector("#add-repo").value) || "OWNER/REPO";
    root.querySelector('[data-out="onboard"]').textContent = onboardPrompt(role, goal, repo);
    root.querySelector('[data-out="onboard-note"]').textContent = ONBOARD_NOTES[goal] || "";
  };
  const press = (sel, b) => root.querySelectorAll(sel).forEach((x) => x.setAttribute("aria-pressed", String(x === b)));
  root.querySelectorAll("[data-role]").forEach((b) => b.addEventListener("click", () => {
    if (role !== b.dataset.role) goal = null;
    role = b.dataset.role; press("[data-role]", b);
    root.querySelectorAll("[data-goal]").forEach((x) => x.setAttribute("aria-pressed", "false"));
    refresh();
  }));
  root.querySelectorAll("[data-goal]").forEach((b) => b.addEventListener("click", () => {
    goal = b.dataset.goal; press(`[data-goals="${role}"] [data-goal]`, b); refresh();
    root.querySelector('[data-step="prompt"]').scrollIntoView({ behavior: "smooth", block: "nearest" });
  }));
  root.querySelector("#add-repo").addEventListener("input", refresh);
  root.querySelector("#add-problem").addEventListener("input", refresh);
  root.querySelector("#add-local").addEventListener("change", refresh);
}

// --- router ------------------------------------------------------------------

function wireCopy(root) {
  root.querySelectorAll("[data-copy],[data-copy-text]").forEach((b) => b.addEventListener("click", async () => {
    const text = b.dataset.copyText ?? root.querySelector(`[data-out="${b.dataset.copy}"]`)?.textContent ?? "";
    try { await navigator.clipboard.writeText(text); const t = b.textContent; b.textContent = "Copied"; setTimeout(() => { b.textContent = t; }, 1400); }
    catch { b.textContent = "Select and copy manually"; }
  }));
}

function render(after) {
  const app = document.getElementById("app");
  const hash = location.hash.replace(/^#/, "") || "/";
  const [, view, arg] = hash.split("/");
  let html, nav = view || "explore";
  if (view === "p") { html = viewProject(decodeURIComponent(arg || "")); nav = "explore"; }
  else if (view === "contribute") html = viewContribute();
  else if (view === "add") html = viewAdd();
  else html = viewExplore();
  app.innerHTML = html;
  document.querySelectorAll("[data-nav]").forEach((a) => a.classList.toggle("active", a.dataset.nav === nav));
  if (view === "p") {
    const p = state.data.projects.find((x) => x.slug === decodeURIComponent(arg || ""));
    if (p) {
      if (p.listing !== "nominated" && !p.review?.paused) wireLauncher(app, p);
      document.title = `${p.title} · Discovery@Home`;
      if (p.frontier?.table) wireRecords(app, p, p.frontier.table, p.frontier.table.rows_snapshot || [], null);
      showImages(app, true);
      loadLive(app, p);
    }
  } else {
    document.title = "Discovery@Home";
    if (!view || view === "") { wireExplore(app); showImages(app); }
    if (view === "add") wireAdd(app);
    if (view === "contribute") { wireDonate(app); wirePrepare(app); }
  }
  wireCopy(app);
  if (after) after();
}

async function start() {
  try {
    const r = await fetch("data/projects.json", { cache: "no-cache" });
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    state.data = await r.json();
  } catch (e) {
    document.getElementById("app").innerHTML = `<div class="empty">Couldn't load project data (${esc(e.message)}).</div>`;
    return;
  }
  document.getElementById("repo-link").href = hubUrl();
  const menu = document.querySelector(".menu");
  document.addEventListener("click", (e) => { if (!menu.contains(e.target)) menu.open = false; });
  document.addEventListener("keydown", (e) => { if (e.key === "Escape") menu.open = false; });
  const g = state.data.generated_at;
  if (g) document.getElementById("generated").textContent = `Data built ${g.replace("T", " ").replace("+00:00", " UTC")}`;
  window.addEventListener("hashchange", () => { render(); window.scrollTo(0, 0); });
  render();
}
start();
