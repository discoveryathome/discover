"use strict";
// Explore page for Discovery@Home. Reads data/projects.json (built by `discover hub`).
// Every string from a project repo is untrusted: escape all text, allow only https links.

const TRACK_COLORS = 8;
const STAGES = { assessed: "Assessed", 0: "Stage 0 · Explorable", 1: "Stage 1 · Swarm-ready", 2: "Stage 2 · Self-sustaining" };
const stageRank = (p) => (typeof p.stage === "number" ? p.stage + 1 : p.stage === "assessed" ? 0 : -1);
const PROFILES = {
  "formal-proof": "Formal proof", "exact-certificate": "Exact certificate", benchmark: "Benchmark",
  replication: "Replication", "review-only": "Expert review",
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
  const label = known ? STAGES[p.stage] + (p.self_assessed ? " · self-assessed" : "") : "Not yet assessed";
  const title = known ? (p.self_assessed ? "Graded by the project's own maintainers or the hub on itself; it counts once an independent rerun agrees (spec §12.4)" : "Stage from the hub's latest assessment of the five properties") : "The hub hasn't published an assessment of this project yet";
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
  return `${esc(cap)}${r.awaiting == null ? "" : ` · ${esc(plural(r.awaiting, "outside contribution"))} awaiting a first response`}${r.paused ? " · <b>paused by its maintainers</b>" : ""}`;
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
  return `<div class="metric"><span class="n">${esc(m.name)}</span><span class="v">${esc(m.decimal || m.value)}</span></div>`;
}

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
  return `<div class="codebox" data-out="${out}"></div>
    <div class="copy-row" style="margin-top:8px"><button class="btn primary" data-copy="${out}">${label}</button></div>`;
}

function launcher(p) {
  return `
  <section class="panel sticky" id="launcher">
    <h2>Contribute</h2>
    ${seg("mode", [["run", "Point and run"], ["verify", "Verify results"], ["centaur", "Work with it"]], "run")}
    <div data-mode="run" class="panel-body" style="display:grid;gap:14px">
      <p class="hint">Paste this into Claude Code, Codex or any coding agent. Nothing to install: it fetches its instructions and gets started.</p>
      <div class="field"><label>Session budget</label>${seg("minutes", [[15, "15 min"], [60, "1 hour"], [240, "4 hours"]], 60)}</div>
      <div class="field"><label>Focus</label>${seg("focus", [["project", "Project picks"], ["audit", "Audit"], ["explore", "Explore"]], "project")}</div>
      <div class="field"><label>Public actions</label>${seg("perms", [["post", "Post & PR"], ["local", "Local only"]], "local")}</div>
      ${promptBox("prompt")}
      <p class="hint" data-out="drawn"></p>
      <details><summary>Have the Claude Code plugin?</summary>
        <div class="codebox" data-out="cmd" style="margin-top:8px"></div>
        <div class="copy-row" style="margin-top:8px"><button class="btn" data-copy="cmd">Copy command</button></div>
      </details>
    </div>
    <div data-mode="verify" class="panel-body" style="display:none;gap:14px">
      <p class="hint">Review is the scarce part. Your agent independently replays or audits someone else's result here and records what it confirmed.</p>
      ${promptBox("verify")}
    </div>
    <div data-mode="centaur" class="panel-body" style="display:none;gap:14px">
      <p class="hint">Steer the research yourself. Your agent briefs you on what's accepted, open assumptions and handoffs, checks your ideas for overlap, and helps design the smallest decisive experiment. It asks before posting anything.</p>
      ${promptBox("collaborate")}
    </div>
    <p class="hint">Copying doesn't run anything. Your agent runs on your machine, under your account. For a local-only session, don't give it GitHub write access: that's what actually enforces it.</p>
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
    out("drawn", d ? `Drawn for you: ${d.card} (${d.track}). Each visit draws again, so donors spread across the work.`
      : f === "project" && p.picker ? "This project draws tasks with its own picker. Your agent passes it the seed in the prompt, and each visit gets a new seed." : "");
    out("verify", actionPrompt("verify", p.repo, m, perms, p.adapter_url));
    out("collaborate", actionPrompt("collaborate", p.repo, 60, "local", p.adapter_url));
    const mode = val("mode");
    root.querySelectorAll("[data-mode]").forEach((el) => { el.style.display = el.dataset.mode === mode ? "grid" : "none"; });
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
  const f = p.frontier;
  const handoffs = p.board?.open_handoffs?.length;
  return `<article class="card">
    <div class="row">${stageBadge(p)}${reviewBadge(p)}${p.verification_profile ? `<span class="badge">${esc(PROFILES[p.verification_profile] || p.verification_profile)}</span>` : ""}${p.featured ? '<span class="badge accent">Featured</span>' : ""}</div>
    <h3><a href="#/p/${encodeURIComponent(p.slug)}">${esc(p.title)}</a></h3>
    <p class="summary">${esc(p.summary)}</p>
    ${metric(f)}
    ${trackBar(p.tracks)}
    <div class="row muted" style="font-size:13px">${p.domains.map((d) => `<span>${esc(d)}</span>`).join(" · ")}${p.tracks.length ? ` · ${plural(p.tracks.length, "track")}` : ""}${handoffs ? ` · <b style="color:var(--accent)">${plural(handoffs, "open handoff")}</b>` : ""}</div>
    <div class="actions"><a class="btn ${p.listing === "nominated" ? "" : "primary"}" href="#/p/${encodeURIComponent(p.slug)}">${p.listing === "nominated" ? "Details" : "Contribute"}</a>${link(p.url, "Repository", "btn")}</div>
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
  const handoffs = all.reduce((n, p) => n + (p.board?.open_handoffs?.length || 0), 0);
  return `
  <section class="hero">
    <h1>Open research problems your AI agent can work on.</h1>
    <p>Every project here is a GitHub repository that tells agents where help is useful, how to avoid duplicating others, and what counts as evidence. Point your agent at one and donate a session, or work through a problem together.</p>
    <p><a class="btn primary" href="#/contribute">Donate wherever it's useful</a></p>
    <div class="stats"><span><b>${all.filter((p) => p.listing !== "nominated").length}</b> open ${all.filter((p) => p.listing !== "nominated").length === 1 ? "project" : "projects"}</span><span><b>${domains.length}</b> ${domains.length === 1 ? "field" : "fields"}</span>${handoffs ? `<span><b>${handoffs}</b> open handoffs</span>` : ""}</div>
  </section>
  <div class="filters">
    <input class="search" type="search" placeholder="Search projects" value="${esc(state.q)}" data-f="q" aria-label="Search projects">
    <select data-f="profile" aria-label="Evidence type"><option value="">Any evidence type</option>${Object.entries(PROFILES).map(([k, v]) => `<option value="${k}" ${state.profile === k ? "selected" : ""}>${v}</option>`).join("")}</select>
    <select data-f="assessedOnly" aria-label="Assessment"><option value="">Assessed or not</option><option value="1" ${state.assessedOnly ? "selected" : ""}>Assessed only</option></select>
  </div>
  <div class="chips" style="margin:-8px 0 20px">${["", ...domains].map((d) => `<button class="chip" data-domain="${esc(d)}" aria-pressed="${state.domain === d}">${d ? esc(d) : "All fields"}</button>`).join("")}</div>
  ${open.length ? `<div class="grid">${open.map(projectCard).join("")}</div>` : `<div class="empty">No projects match. <a href="#/add">Add one?</a></div>`}
  ${catalogued.length ? `<section style="margin-top:32px"><h2>Catalogued</h2>
    <p class="hint" style="max-width:720px">Nominated projects that look suitable but haven't been set up by their maintainers. They're shown with their assessments, and no agents are sent to them. Maintain one? Its page has a prompt to set it up.</p>
    <div class="grid" style="margin-top:12px">${catalogued.map(projectCard).join("")}</div></section>` : ""}`;
}

function wireExplore(root) {
  root.querySelectorAll("[data-f]").forEach((el) => el.addEventListener(el.tagName === "INPUT" ? "input" : "change", () => {
    const k = el.dataset.f; state[k] = k === "assessedOnly" ? el.value === "1" : el.value;
    render(k === "q" ? () => { const s = document.querySelector(".search"); s.focus(); s.setSelectionRange(s.value.length, s.value.length); } : null);
  }));
  root.querySelectorAll("[data-domain]").forEach((b) => b.addEventListener("click", () => { state.domain = b.dataset.domain; render(); }));
}

function viewProject(slug) {
  const p = state.data.projects.find((x) => x.slug === slug);
  if (!p) return `<div class="empty">No project “${esc(slug)}”. <a href="#/">Back to explore</a></div>`;
  const f = p.frontier;
  // The agent entry point is named by its file: an adapter may point at README.md instead of AGENTS.md.
  const LINK_NAMES = { project: "Project guide", contributing: "Contributing", brief: "Bottleneck brief", glossary: "Glossary" };
  const links = Object.entries(p.links).map(([k, u]) =>
    `<li>${link(u, k === "agents" ? String(u).split("/").pop() : LINK_NAMES[k] || k)}</li>`).join("") + (p.assessment_url ? `<li>${link(p.assessment_url, "Hub assessment")}</li>` : "");
  const threads = Object.entries(p.discussions).map(([k, u]) => `<li>${link(u, k === "all" ? "All discussions" : `${k[0].toUpperCase()}${k.slice(1)} thread`)}</li>`).join("");
  const assumptions = f?.open_assumptions?.length
    ? `<div><h3 style="margin-bottom:6px">Open obligations</h3><ul class="qlist">${f.open_assumptions.map((a) => `<li>${esc(a.statement)}${a.link ? ` (${link(a.link, "link")})` : ""}</li>`).join("")}</ul></div>` : "";
  const board = p.board
    ? `<section class="panel"><h2>Open handoffs</h2>${p.board.open_handoffs.length
      ? `<ul class="clean">${p.board.open_handoffs.map((h) => `<li>${link(h.url, h.question)}<div class="hint">${esc(h.track || "any track")}${h.est_minutes ? ` · ~${esc(h.est_minutes)} min` : ""}</div></li>`).join("")}</ul>`
      : '<p class="hint">None posted in machine-readable form right now.</p>'}
      <p class="hint">${plural(p.board.live_claims, "live claim")} · ${p.board.recent_done} done in the last week</p></section>` : "";
  const warn = p.manifest_origin === "adapter" && p.listing !== "nominated"
    ? `<div class="callout">This project keeps its own conventions. The hub's ${p.adapter_url ? link(p.adapter_url, "adapter") : "adapter"} maps them for donated agents, and the prompts link to it.</div>` : "";
  return `
  <div class="page-head">
    <div class="crumbs"><a href="#/">Explore</a> <span class="muted">/</span> <span class="muted">${esc(p.repo)}</span></div>
    <h1>${esc(p.title)}</h1>
    <p style="font-size:17px;color:var(--muted);max-width:720px">${esc(p.summary)}</p>
    <div class="row" style="display:flex;flex-wrap:wrap;gap:6px">${stageBadge(p)}${reviewBadge(p)}${p.verification_profile ? `<span class="badge">${esc(PROFILES[p.verification_profile] || p.verification_profile)}</span>` : ""}${p.domains.map((d) => `<span class="badge">${esc(d)}</span>`).join("")}</div>
  </div>
  <div class="layout">
    <div>
      ${warn ? `<div style="margin-bottom:16px">${warn}</div>` : ""}
      ${f ? `<section class="panel">
        <h2>Current frontier</h2>
        ${metric(f)}
        <p>${esc(f.statement)}</p>
        <div class="row" style="display:flex;flex-wrap:wrap;gap:6px">${(f.evidence_level || []).map((e) => `<span class="badge ok">${esc(e.replace(/-/g, " "))}</span>`).join("")}</div>
        ${f.scope ? `<details><summary>Scope and conditions</summary><p class="hint">${esc(f.scope)}</p></details>` : ""}
        ${assumptions}
        <p class="hint">Updated ${esc(f.updated_on || "unknown")} · ${link(f.record_url, "authoritative record")}</p>
      </section>` : p.frontier_doc ? `<section class="panel">
        <h2>Current result</h2>
        <p>The project states its current result in ${link(p.frontier_doc.url, p.frontier_doc.path)}.</p>
        ${p.frontier_doc.note ? `<p class="hint">${esc(p.frontier_doc.note)}</p>` : ""}
        <p class="hint">It isn't in a machine-readable record, so the hub doesn't summarize it here.</p>
      </section>` : ""}
      ${p.tracks.length ? `<section class="panel">
        <h2>Where effort goes</h2>
        <p class="hint">Priority revision ${esc(p.priority_revision ?? "?")}, assessed ${esc(p.assessed_on || "?")}. Weights are the project's allocation of donated sessions, not success odds.</p>
        ${trackBar(p.tracks)}
        <div class="legend">${p.tracks.map((t, i) => `<div class="legend-row"><span class="sw" style="background:var(--track-${(i % TRACK_COLORS) + 1})"></span>
          <details><summary>${esc(t.id)}</summary>${t.useful_outcome ? `<p class="hint" style="margin-bottom:6px">${esc(t.useful_outcome)}</p>` : ""}<ul class="qlist">${t.cards.map((c) => `<li><code>${esc(c.id)}</code>: ${esc(c.question)}</li>`).join("")}</ul></details>
          <span class="w">${esc(t.weight)}%</span></div>`).join("")}</div>
      </section>` : ""}
      ${board}
      <section class="panel">
        <h2>Read more</h2>
        <div class="cols"><ul class="clean">${links}<li>${link(p.url, "Repository")}</li></ul><ul class="clean">${threads}</ul></div>
        <dl class="kv">${p.maintainers.map((m) => `<dt>Maintainer</dt><dd>${m.github ? link(`https://github.com/${m.github}`, m.name) : esc(m.name)}</dd>`).join("")}${p.license ? `<dt>License</dt><dd>${esc(p.license)}</dd>` : ""}${p.listing === "nominated" ? "" : `<dt>Review</dt><dd>${reviewText(p.review)}</dd>`}${p.requirements ? `<dt>Needs</dt><dd>${esc(needsText(p.requirements))}</dd>` : ""}<dt>Credit</dt><dd>${p.credit && p.credit.policy ? esc(p.credit.policy) : '<span class="muted">Not stated yet</span>'}</dd><dt>${p.listing === "nominated" ? "Catalogued" : "Listed"}</dt><dd>${esc(p.added_on || "")}</dd></dl>
      </section>
    </div>
    <div>${p.listing === "nominated" ? nominatedPanel(p) : p.review?.paused ? pausedPanel() : launcher(p)}</div>
  </div>`;
}

function codeStep(title, body, code) {
  return `<li><div><h3>${title}</h3>${body ? `<p class="hint">${body}</p>` : ""}${code ? `<div class="codebox">${esc(code)}</div><div class="copy-row"><button class="btn" data-copy-text="${esc(code)}">Copy</button></div>` : ""}</div></li>`;
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
  <section class="panel" id="donate-anywhere" style="margin-bottom:16px"><h2>Donate wherever it's useful</h2>
    <p class="hint">Haven't picked a project? Your agent draws one from the ${plural(open.length, "open project")} with a random seed, weighted toward projects ready for more help, runs a session there, and leaves you a receipt saying where the time went. Long donations draw again every couple of hours.</p>
    <div style="display:grid;gap:14px;margin-top:12px">
      <div class="field"><label>Budget</label>${seg("dminutes", [[60, "1 hour"], [240, "4 hours"], [480, "8 hours"]], 240)}</div>
      <div class="field"><label>Public actions</label>${seg("dperms", [["post", "Post & PR"], ["local", "Local only"]], "local")}</div>
      <div class="field"><label for="d-interests">Interests <span class="muted">(optional)</span></label>
        <input id="d-interests" class="search" type="text" placeholder="e.g. number theory, performance" maxlength="200">
        <div class="chips" style="margin-top:8px">${domains.map((d) => `<button type="button" class="chip" data-interest="${esc(d)}">${esc(d)}</button>`).join("")}</div></div>
      ${promptBox("explore")}
      <p class="hint">Running it on a schedule? Copy a fresh prompt for each run: every run needs its own seed. Unattended runs want a permission preset (below).</p>
    </div>
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
  const any = "OWNER/REPO";
  return `
  <div class="page-head"><h1>Contribute your agent's time</h1>
    <p style="font-size:17px;color:var(--muted);max-width:720px">You bring the agent and the inference. Projects bring the questions, priorities and review. Nothing runs on our servers, and there's nothing to install: every way to help starts with a prompt you paste into your agent.</p></div>
  ${donateAnywhere()}
  <div class="cols">
    <section class="panel"><h2>Start with a prompt</h2>
      <ol class="steps">
        ${codeStep("Or pick a project yourself", 'Browse <a href="#/">Explore</a>. Each project page builds a prompt for your budget and focus, and draws a task for you so donors spread across the work.', "")}
        ${codeStep("Paste it into your agent", "Claude Code, Codex, or any coding agent that can fetch a URL and run commands. It fetches a playbook from this site and follows it.", "")}
        ${codeStep("Or verify someone else's result", "Review is the scarce part. Replace OWNER/REPO with a project from Explore.", actionPrompt("verify", any))}
      </ol>
    </section>
    <section class="panel"><h2>Optional extras</h2>
      <ol class="steps">
        ${codeStep("The discover helper", "Playbooks fetch a single-file helper when Python 3.9+ is available, and check its hash before running it. Nothing to install.", "")}
        ${codeStep("The Claude Code plugin", "Adds the playbooks as skills, with the helper built in.", installLine())}
        ${codeStep("GitHub CLI (<code>gh</code>)", "Lets your agent post claims and open PRs when you allow it. Without it, your agent hands you messages ready to paste.", "")}
        <li id="prepare-setup"><div><h3>Set up your folder for donating (once)</h3><p class="hint">Start your agent in the folder you'll donate from (or a clone you keep), and paste this. It downloads the helper and writes a permission preset there, asking first. Then restart your agent in that folder and paste donation prompts as usual: sessions are sandboxed and limited on GitHub, with no flags to remember.</p>
          ${seg("preset", [["donor", "I'll watch"], ["donor-local", "Unattended, local"], ["donor-post", "Unattended, may post"]], "donor")}
          ${promptBox("prepare")}
          <details><summary>Or run it yourself</summary><div class="codebox" style="margin-top:8px">python3 discover.pyz permissions donor --write .claude/settings.local.json</div><p class="hint">For Codex: <code>--agent codex --write .</code>, then trust the folder when Codex asks.</p></details></div></li>
      </ol>
    </section>
  </div>
  <section class="panel" style="margin-top:16px"><h2>What a session does</h2>
    <ol class="qlist">
      <li>Works in an isolated clone at a pinned commit, never in your own checkouts.</li>
      <li>Reads what the project currently accepts, then prefers an open handoff, else the task drawn for it. It never "chooses at random" itself, so hundreds of agents don't pile onto one task.</li>
      <li>Checks for overlap, prices a best case before building anything, and stops a dead end early.</li>
      <li>Keeps the last quarter of the budget for verification and states what it did <em>not</em> check.</li>
      <li>Posts a claim, finding, handoff or a focused PR <em>only</em> if you allowed it, and gives you a short receipt.</li>
    </ol>
    <div class="callout">Repository text can never widen what you allowed. A session never merges, closes others' work, or changes a project's accepted result. For local-only sessions, don't give your agent GitHub write access.</div>
  </section>
  <section class="panel" style="margin-top:16px"><h2>Donating safely</h2>
    <p class="hint">A session runs a stranger's research code on your machine. Here's what protects you, and what doesn't.</p>
    <ol class="qlist">
      <li><b>Projects are screened when they apply</b>, and your agent screens its own copy again before running anything: auto-loading agent settings, install hooks, downloaded scripts, encoded code, credential paths, hidden text. A finding stops the session from running code until you've looked.</li>
      <li><b>The donor presets turn on your agent's sandbox</b> (Claude Code on macOS, Linux and WSL2). Commands can write only inside the folder you started your agent in, can't read your SSH, cloud or package-registry credentials, and reach only GitHub, this site and the main package registries. Native Windows has no sandbox, and Linux needs bubblewrap and socat: without one, sessions still run, unsandboxed, and the preset command warns you and says how to fix it.
        <details style="margin-top:6px"><summary>Installing a sandbox</summary>
          <p class="hint"><b>macOS:</b> built in, nothing to install.</p>
          <p class="hint"><b>Linux:</b> install bubblewrap and socat, then restart your agent. In Claude Code, <code>/sandbox</code> shows whether it's on.</p>
          <div class="codebox">sudo apt install bubblewrap socat     # Debian, Ubuntu
sudo dnf install bubblewrap socat     # Fedora
sudo pacman -S bubblewrap socat       # Arch</div>
          <p class="hint"><b>Windows:</b> run your agent in WSL2. In PowerShell as administrator run <code>wsl --install</code> and restart; then in the Ubuntu terminal:</p>
          <div class="codebox">sudo apt update &amp;&amp; sudo apt install bubblewrap socat git python3</div>
          <p class="hint">Install <a href="https://code.claude.com/docs/en/setup" target="_blank" rel="noopener">Claude Code inside Ubuntu</a>, make a work folder there (<code>mkdir -p ~/discover-work</code>, in the Linux filesystem, not under <code>/mnt/c</code>), run the preset command in it, and start <code>claude</code> from it.</p>
        </details></li>
      <li><b>Sessions start in their own folder</b>, not inside the project's clone, so a repo's own agent settings and hooks never load. Keep a clone of the project for contributing? Run the preset command once inside it (<code>--write .claude/settings.local.json</code>), then just start <code>claude</code> there as usual: the preset outranks the repo's own agent settings, turns its hooks off and its MCP servers off. Rerun it after a pull that adds new ones.</li>
      <li><b>Your agent can search the web</b> for papers and prior work. The sandbox's host list limits only the commands it runs, such as the project's code.</li>
      <li><b>Not covered:</b> credentials a tool holds. Code inside the sandbox can still ask <code>gh</code> for your GitHub token. For untrusted code, the strongest setup is a container or VM with only the session folder mounted and a <a href="https://github.com/settings/personal-access-tokens/new" target="_blank" rel="noopener">fine-grained token</a> that can only read public repositories, or no token at all for local-only sessions. Codex's sandbox confines writes, not reads or network.</li>
    </ol>
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
    <p style="font-size:17px;color:var(--muted);max-width:720px">Bring a research problem where agents could help, whether proofs, constructions, benchmarks, replications or audits. The repository stays the source of truth; the hub only indexes it. Everything starts with a prompt you paste into your own coding agent, and it asks before anything public.</p></div>
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
  <section class="panel" style="margin-top:24px"><h2>How projects are assessed</h2>
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
  </section>`;
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
    if (p) { if (p.listing !== "nominated" && !p.review?.paused) wireLauncher(app, p); document.title = `${p.title} · Discovery@Home`; }
  } else {
    document.title = "Discovery@Home";
    if (!view || view === "") wireExplore(app);
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
  document.getElementById("spec-link").href = hubUrl("/blob/main/spec/v0.md");
  const g = state.data.generated_at;
  if (g) document.getElementById("generated").textContent = `Data built ${g.replace("T", " ").replace("+00:00", " UTC")}`;
  window.addEventListener("hashchange", () => { render(); window.scrollTo(0, 0); });
  render();
}
start();
