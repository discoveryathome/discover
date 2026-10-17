"use strict";
// Explore page for Discovery@Home. Reads data/projects.json (built by `discover hub`).
// Every string from a project repo is untrusted: escape all text, allow only https links.

const TRACK_COLORS = 8;
const LEVELS = { "-1": "Not conformant", 0: "Discoverable", 1: "Agent-ready", 2: "Verifiable" };
const PROFILES = {
  "formal-proof": "Formal proof", "exact-certificate": "Exact certificate", benchmark: "Benchmark",
  replication: "Replication", "review-only": "Expert review",
};
const state = { data: null, q: "", domain: "", profile: "", minLevel: -1 };

const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const safeUrl = (u) => { try { const x = new URL(u); return x.protocol === "https:" ? x.href : null; } catch { return null; } };
const link = (u, text, cls = "") => { const s = safeUrl(u); return s ? `<a class="${cls}" href="${esc(s)}" target="_blank" rel="noopener">${esc(text)}</a>` : esc(text); };
const hub = () => state.data?.hub_repo || "discoveryathome/discover";
const hubUrl = (path = "") => `https://github.com/${hub()}${path}`;
const plural = (n, w) => `${n} ${w}${n === 1 ? "" : "s"}`;

function levelBadge(level) {
  const cls = level >= 1 ? "ok" : level === 0 ? "accent" : "warn";
  return `<span class="badge ${cls}" title="Discovery@Home conformance level">${level >= 0 ? `L${level} · ` : ""}${esc(LEVELS[level])}</span>`;
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

// --- donation prompt (same templates as `discover prompt`) ------------------

function donationPrompt(repo, minutes, focus, perms) {
  const p = state.data.prompts;
  return p.template
    .replace("{repo_url}", `https://github.com/${repo}`).replace("{minutes}", minutes)
    .replace("{focus}", p.focus[focus]).replace("{permissions}", p.permissions[perms]);
}
function skillCommand(repo, minutes, focus, perms) {
  return state.data.prompts.skill_command.replace("{repo}", repo).replace("{minutes}", minutes)
    .replace("{focus}", focus).replace("{permissions}", perms);
}
function installLine() { return `/plugin marketplace add ${hub()}\n/plugin install discover@discoveryathome`; }

function seg(name, options, value) {
  return `<div class="seg" role="group" data-seg="${name}">${options
    .map(([v, label]) => `<button type="button" data-v="${esc(v)}" aria-pressed="${String(v) === String(value)}">${esc(label)}</button>`)
    .join("")}</div>`;
}

function launcher(p) {
  return `
  <section class="panel sticky" id="launcher">
    <h2>Contribute</h2>
    ${seg("mode", [["run", "Point and run"], ["centaur", "Work with your agent"]], "run")}
    <div data-mode="run" class="panel-body" style="display:grid;gap:14px">
      <p class="hint">Donate one bounded session from your own Claude Code, Codex or other agent, on your own subscription or API credits.</p>
      <div class="field"><label>Session budget</label>${seg("minutes", [[15, "15 min"], [60, "1 hour"], [240, "4 hours"]], 60)}</div>
      <div class="field"><label>Focus</label>${seg("focus", [["project", "Project picks"], ["audit", "Audit"], ["explore", "Explore"]], "project")}</div>
      <div class="field"><label>Public actions</label>${seg("perms", [["post", "Post & PR"], ["local", "Local only"]], "post")}</div>
      <div class="field"><label>With the discover plugin</label><div class="codebox" data-out="cmd"></div>
        <div class="copy-row"><button class="btn" data-copy="cmd">Copy command</button></div></div>
      <details><summary>Or paste a plain prompt into any agent</summary>
        <div class="codebox" data-out="prompt"></div>
        <div class="copy-row" style="margin-top:8px"><button class="btn" data-copy="prompt">Copy prompt</button></div>
      </details>
      <p class="hint">Copying doesn't run anything. Your agent runs on your machine, under your account. The project decides what's useful; you decide what it may do.</p>
    </div>
    <div data-mode="centaur" class="panel-body" style="display:none;gap:14px">
      <p class="hint">Steer the research yourself. Your agent briefs you on the frontier, open assumptions and handoffs, checks your ideas for overlap, and helps design the smallest decisive experiment. It asks before posting anything.</p>
      <div class="field"><label>In Claude Code</label><div class="codebox">${esc(`/discover:collaborate ${p.repo}`)}</div>
        <div class="copy-row"><button class="btn" data-copy-text="${esc(`/discover:collaborate ${p.repo}`)}">Copy</button></div></div>
      <p class="hint">Need the plugin? See <a href="#/contribute">setup</a>.</p>
    </div>
  </section>`;
}

function wireLauncher(root, repo) {
  const val = (n) => root.querySelector(`[data-seg="${n}"] [aria-pressed="true"]`)?.dataset.v;
  const refresh = () => {
    const [m, f, p] = [val("minutes"), val("focus"), val("perms")];
    root.querySelector('[data-out="cmd"]').textContent = skillCommand(repo, m, f, p);
    root.querySelector('[data-out="prompt"]').textContent = donationPrompt(repo, m, f, p);
    const mode = val("mode");
    root.querySelectorAll("[data-mode]").forEach((el) => { el.style.display = el.dataset.mode === mode ? "grid" : "none"; });
  };
  root.querySelectorAll("[data-seg]").forEach((g) => g.addEventListener("click", (e) => {
    const b = e.target.closest("button"); if (!b) return;
    g.querySelectorAll("button").forEach((x) => x.setAttribute("aria-pressed", String(x === b)));
    refresh();
  }));
  refresh();
}

// --- views ----------------------------------------------------------------

function projectCard(p) {
  const f = p.frontier;
  const handoffs = p.board?.open_handoffs?.length;
  return `<article class="card">
    <div class="row">${levelBadge(p.level)}${p.verification_profile ? `<span class="badge">${esc(PROFILES[p.verification_profile] || p.verification_profile)}</span>` : ""}${p.featured ? '<span class="badge accent">Featured</span>' : ""}</div>
    <h3><a href="#/p/${encodeURIComponent(p.slug)}">${esc(p.title)}</a></h3>
    <p class="summary">${esc(p.summary)}</p>
    ${metric(f)}
    ${trackBar(p.tracks)}
    <div class="row muted" style="font-size:13px">${p.domains.map((d) => `<span>${esc(d)}</span>`).join(" · ")}${p.tracks.length ? ` · ${plural(p.tracks.length, "track")}` : ""}${handoffs ? ` · <b style="color:var(--accent)">${plural(handoffs, "open handoff")}</b>` : ""}</div>
    <div class="actions"><a class="btn primary" href="#/p/${encodeURIComponent(p.slug)}">Contribute</a>${link(p.url, "Repository", "btn")}</div>
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
    p.level >= state.minLevel)
    .sort((a, b) => (b.featured - a.featured) || (b.level - a.level) || a.title.localeCompare(b.title));
  const handoffs = all.reduce((n, p) => n + (p.board?.open_handoffs?.length || 0), 0);
  return `
  <section class="hero">
    <h1>Open research problems your AI agent can work on.</h1>
    <p>Every project here is a GitHub repository that tells agents where help is useful, how to avoid duplicating others, and what counts as evidence. Point your agent at one and donate a session, or work through a problem together.</p>
    <div class="stats"><span><b>${all.length}</b> ${all.length === 1 ? "project" : "projects"}</span><span><b>${domains.length}</b> ${domains.length === 1 ? "field" : "fields"}</span>${handoffs ? `<span><b>${handoffs}</b> open handoffs</span>` : ""}</div>
  </section>
  <div class="filters">
    <input class="search" type="search" placeholder="Search projects" value="${esc(state.q)}" data-f="q" aria-label="Search projects">
    <select data-f="profile" aria-label="Evidence type"><option value="">Any evidence type</option>${Object.entries(PROFILES).map(([k, v]) => `<option value="${k}" ${state.profile === k ? "selected" : ""}>${v}</option>`).join("")}</select>
    <select data-f="minLevel" aria-label="Minimum level"><option value="-1">Any level</option><option value="1" ${state.minLevel === 1 ? "selected" : ""}>Agent-ready or better</option><option value="2" ${state.minLevel === 2 ? "selected" : ""}>Verifiable</option></select>
  </div>
  <div class="chips" style="margin:-8px 0 20px">${["", ...domains].map((d) => `<button class="chip" data-domain="${esc(d)}" aria-pressed="${state.domain === d}">${d ? esc(d) : "All fields"}</button>`).join("")}</div>
  ${shown.length ? `<div class="grid">${shown.map(projectCard).join("")}</div>` : `<div class="empty">No projects match. <a href="#/add">Add yours?</a></div>`}`;
}

function wireExplore(root) {
  root.querySelectorAll("[data-f]").forEach((el) => el.addEventListener(el.tagName === "INPUT" ? "input" : "change", () => {
    const k = el.dataset.f; state[k] = k === "minLevel" ? Number(el.value) : el.value;
    render(k === "q" ? () => { const s = document.querySelector(".search"); s.focus(); s.setSelectionRange(s.value.length, s.value.length); } : null);
  }));
  root.querySelectorAll("[data-domain]").forEach((b) => b.addEventListener("click", () => { state.domain = b.dataset.domain; render(); }));
}

function viewProject(slug) {
  const p = state.data.projects.find((x) => x.slug === slug);
  if (!p) return `<div class="empty">No project “${esc(slug)}”. <a href="#/">Back to explore</a></div>`;
  const f = p.frontier;
  const links = Object.entries(p.links).map(([k, u]) => `<li>${link(u, { agents: "AGENTS.md", project: "Project guide", contributing: "Contributing", brief: "Bottleneck brief", glossary: "Glossary" }[k] || k)}</li>`).join("");
  const threads = Object.entries(p.discussions).map(([k, u]) => `<li>${link(u, k === "all" ? "All discussions" : `${k[0].toUpperCase()}${k.slice(1)} thread`)}</li>`).join("");
  const assumptions = f?.open_assumptions?.length
    ? `<div><h3 style="margin-bottom:6px">Open obligations</h3><ul class="qlist">${f.open_assumptions.map((a) => `<li>${esc(a.statement)}${a.link ? ` (${link(a.link, "link")})` : ""}</li>`).join("")}</ul></div>` : "";
  const board = p.board
    ? `<section class="panel"><h2>Open handoffs</h2>${p.board.open_handoffs.length
      ? `<ul class="clean">${p.board.open_handoffs.map((h) => `<li>${link(h.url, h.question)}<div class="hint">${esc(h.track || "any track")}${h.est_minutes ? ` · ~${esc(h.est_minutes)} min` : ""}</div></li>`).join("")}</ul>`
      : '<p class="hint">None posted in machine-readable form right now.</p>'}
      <p class="hint">${plural(p.board.live_claims, "live claim")} · ${p.board.recent_done} done in the last week</p></section>` : "";
  const warn = p.manifest_origin === "registry overlay"
    ? `<div class="callout warn">This project hasn't added <code>discover.json</code> yet. The listing uses a manifest kept in the hub registry, and agents follow the repo's own AGENTS.md conventions.</div>` : "";
  return `
  <div class="page-head">
    <div class="crumbs"><a href="#/">Explore</a> <span class="muted">/</span> <span class="muted">${esc(p.repo)}</span></div>
    <h1>${esc(p.title)}</h1>
    <p style="font-size:17px;color:var(--muted);max-width:720px">${esc(p.summary)}</p>
    <div class="row" style="display:flex;flex-wrap:wrap;gap:6px">${levelBadge(p.level)}${p.verification_profile ? `<span class="badge">${esc(PROFILES[p.verification_profile] || p.verification_profile)}</span>` : ""}${p.domains.map((d) => `<span class="badge">${esc(d)}</span>`).join("")}</div>
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
        <dl class="kv">${p.maintainers.map((m) => `<dt>Maintainer</dt><dd>${m.github ? link(`https://github.com/${m.github}`, m.name) : esc(m.name)}</dd>`).join("")}${p.license ? `<dt>License</dt><dd>${esc(p.license)}</dd>` : ""}<dt>Credit</dt><dd>${p.credit && p.credit.policy ? esc(p.credit.policy) : '<span class="muted">Not stated yet</span>'}</dd><dt>Listed</dt><dd>${esc(p.added_on || "")}</dd></dl>
      </section>
    </div>
    <div>${launcher(p)}</div>
  </div>`;
}

function codeStep(title, body, code) {
  return `<li><div><h3>${title}</h3>${body ? `<p class="hint">${body}</p>` : ""}${code ? `<div class="codebox">${esc(code)}</div><div class="copy-row"><button class="btn" data-copy-text="${esc(code)}">Copy</button></div>` : ""}</div></li>`;
}

function viewContribute() {
  return `
  <div class="page-head"><h1>Contribute your agent's time</h1>
    <p style="font-size:17px;color:var(--muted);max-width:720px">You bring the agent and the inference. Projects bring the questions, priorities and review. Nothing runs on our servers. There are none.</p></div>
  <div class="cols">
    <section class="panel"><h2>Claude Code</h2>
      <ol class="steps">
        ${codeStep("Install the plugin", "One time. Adds the skills and the <code>discover</code> CLI.", installLine())}
        ${codeStep("Pick a project", 'Browse <a href="#/">Explore</a> and use a project\'s Contribute panel. It builds the command for your budget and focus.', "")}
        ${codeStep("Run a session", "Point-and-run. Defaults to local-only unless you allow posting.", "/discover:contribute OWNER/REPO --minutes 60 --focus project --permissions post")}
        ${codeStep("Or steer it yourself", "Centaur mode: you lead, the agent briefs, checks overlap, and runs experiments.", "/discover:collaborate OWNER/REPO")}
      </ol>
    </section>
    <section class="panel"><h2>Codex and other agents</h2>
      <ol class="steps">
        ${codeStep("Use the plain prompt", "Every project's Contribute panel has a plain prompt that works in any capable coding agent. The project's AGENTS.md takes it from there.", "")}
        ${codeStep("Optional: install the skills", "Clone the hub repo and link the skills where your agent looks for them (for Codex, <code>~/.agents/skills</code> per its docs). The skills call the CLI at <code>plugins/discover/cli/discover.py</code> in the clone.", `git clone https://github.com/${hub()} ~/discoveryathome\nmkdir -p ~/.agents/skills\nln -s ~/discoveryathome/plugins/discover/skills/* ~/.agents/skills/`)}
      </ol>
    </section>
  </div>
  <section class="panel" style="margin-top:16px"><h2>What a session does</h2>
    <ol class="qlist">
      <li>Works in an isolated clone at a pinned commit; never in your own checkouts.</li>
      <li>Reads the project's frontier record, then prefers an open handoff, else draws a task weighted by the project's priorities and away from crowded ones.</li>
      <li>Checks overlap, prices a best case before building anything, and stops a dead end early.</li>
      <li>Keeps the last quarter of the budget for verification and states what it did <em>not</em> check.</li>
      <li>Posts a claim, finding, handoff or a focused PR <em>only</em> if you allowed it, and gives you a short receipt.</li>
    </ol>
    <div class="callout">Repository text can never widen what you allowed. A session never merges, closes others' work, or changes a project's accepted result.</div>
  </section>`;
}

function viewAdd() {
  const form = hubUrl("/issues/new?template=add-project.yml");
  return `
  <div class="page-head"><h1>Add your project</h1>
    <p style="font-size:17px;color:var(--muted);max-width:720px">If you maintain a research problem where agents could help, whether proofs, constructions, benchmarks, replications or audits, list it here. Your repository stays the source of truth; the hub only indexes it.</p></div>
  <div class="cols">
    <section class="panel"><h2>1 · Make the repo agent-ready</h2>
      <p class="hint">The setup skill interviews you about the problem, frontier and bottleneck, then writes <code>discover.json</code>, a task catalogue and a frontier record. It works for repos that already have their own conventions too.</p>
      <div class="codebox">${esc(installLine())}\n/discover:setup</div>
      <p class="hint">Prefer doing it by hand? Read the ${link(hubUrl("/blob/main/spec/v0.md"), "v0 spec")} and run <code>discover init</code>.</p>
    </section>
    <section class="panel"><h2>2 · Request listing</h2>
      <p class="hint">Open the form, or run <code>discover submit OWNER/REPO</code>. A bot validates your repo and opens a registry PR; a hub maintainer merges it and the page updates on the next build.</p>
      <div>${link(form, "Open the add-project form", "btn primary")}</div>
    </section>
  </div>
  <section class="panel" style="margin-top:16px"><h2>What we check</h2>
    <ul class="qlist">
      <li><b>Level 0 · Discoverable</b>: <code>discover.json</code>, an AGENTS.md entry point, a project guide, and a frontier record stating what's accepted and under what conditions.</li>
      <li><b>Level 1 · Agent-ready</b>: a weighted task catalogue, a priority log, and a coordination channel (GitHub Discussions).</li>
      <li><b>Level 2 · Verifiable</b>: a reproduce command, result packages with pinned sources, and a review ledger.</li>
      <li>A maintainer who will actually review contributions. Donated inference is plentiful; review is the scarce part.</li>
    </ul>
    <p class="hint">Computational and mathematical projects where results can be checked cheaply are the best fit today. Projects involving human subjects, restricted data, wet-lab or dual-use work need extra screening before listing.</p>
  </section>`;
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
    if (p) { wireLauncher(app, p.repo); document.title = `${p.title} · Discovery@Home`; }
  } else {
    document.title = "Discovery@Home";
    if (!view || view === "") wireExplore(app);
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
