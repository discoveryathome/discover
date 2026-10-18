# Roadmap

What the hub's maintainers plan to build next, in order. Donated hub work is allocated
separately, by the tracks in [`discover/catalog.json`](discover/catalog.json); when a
roadmap item opens work that donors can pick up, it gets cards there.

Status as of 2026-10-17. Onboarding and the donation loop are built and smoke-tested;
hub operations are built and running as a dry run.

## Done

- **Onboarding**, end to end on `CrocSwap/applied-butterfly-mult`: both roles, every
  goal, intake (including duplicates and consent on a nominated entry), the hub
  assessment with as-is and projected grades, and the upgrade from catalogued to listed
  by both paths. Plus `start`, for a new project from a problem statement, tested in local
  mode on a real problem.
- **Adapters** (spec §12.5): the `adapt` playbook and `discover adapter-check`, tested on
  six third-party repositories, with and without each adapter, and fixed until adapters
  never left a donor less oriented than the bare repo.
- **The donation loop**, on a project with its own files and one listed through an
  adapter: local and posting sessions, independent verification, four donors at once,
  a planted adapter error caught and fixed by a donor, and the maintainer's triage and
  priority revision. It found and fixed: messages without their `discover` block, the
  board reading only one block per post, short sessions not claiming (the cause of the
  one duplicate PR), verifications of the frontier having nowhere to go, scattered
  session folders, and disk use. Coordination worked whenever there was a signal to see:
  a later donor took up an earlier one's handoff and did distinct work.
- **Hub operations** (item 2 below, mostly): `discover hub-check` and a weekly workflow.
- **A license is a Stage 0 requirement** (spec §3.3), found in testing: without one a
  donor's contribution has no clear terms. `validate` warns, the assess and setup
  playbooks check and ask for it, and the hub check flags listings without one.

## Now

### 1. Permission presets for agents (done, first version)

Every maintainer test hit the same wall: Claude Code's auto mode refused GitHub writes the
person had just approved. `discover permissions <maintainer|donor-post|donor-local>
--write .claude/settings.local.json` now writes a preset: for maintainers, each public
write becomes an explicit prompt the automatic checker can't refuse; unattended donors
allowed to post get narrow allow rules; local-only donors get writes denied. The
playbooks tell agents to hand over exact commands, never work around a refusal. D9 (a
maintainer collaborate session) opened PRs and posted with nothing refused. Codex:
`--agent codex` writes execpolicy rules and a config layer, tested headless under each
preset (local refused the push, post pushed, maintainer refused cleanly because `exec`
can't ask). Left: an interactive Codex maintainer session, and the upstream report.

### 2. Hub operations: finish

Built: the scheduled check (spec §12.6) for consent, validity, adapter drift, stale
assessments and registry consistency; one hub issue per finding; the re-assess mode; and
the assessment record format. Left:

- Turn on issue syncing (`HUB_CHECK_ISSUES`) after a week of clean dry runs (about
  2026-10-24).
- Done: every listing has a record (integer-mult-bounds through its adapter, the hub on
  itself, re-assessed once), and the hub's priorities are at revision 2.
- Done when a listed project can change for a month and its listing stays accurate with
  only hub-work sessions.

## Next

### 3. Low-touch donating and agent browsing (built, first version)

"Donate four hours to wherever it's useful", for people who haven't chosen a project.
Built:

- **A seeded draw across the hub** (spec §12.2): the donor's interests become fields, and
  the draw picks among open projects in those fields, weighted by stage (1, 3, 6), with
  rounds for long donations. Not weighted by open handoffs: they measure demand, and
  would send most donors to the project least able to review them. `discover choose`
  draws it, and the playbook has a ten-line script for agents without the helper.
- **For agents:** `data/agents.json` (schema `agent-index.schema.json`) and `llms.txt`.
- **The `explore` playbook:** interests to fields, the draw, a contribute session per
  round, and a receipt (`receipt.json`) saying where each round went.
- **The site:** "Donate wherever it's useful" on the Contribute page (budget,
  permissions, interests), linked from Explore.

Tested (2026-10-18, headless, local-only): E1, 20 minutes with matching interests; E3,
15 minutes with interests no project matches (the draw fell back to all projects);
E2, 240 minutes, which ran four rounds across all three projects. Every draw matched
the precomputed one, and each receipt was complete. Found: sessions finish well inside
their budget (E2 used 36 of 240 minutes), and E2 stopped early on its own judgment that
more work would swamp a maintainer's review capacity. The playbook now says to switch to
verification in that case rather than stop. Left: scheduled runs beyond the playbook's
guidance (a script that makes a fresh seed per run), and review capacity as the draw's
second weight, with item 4.

### 4. Matching launcher traffic to review capacity

Review, not donated compute, is what a project can absorb. Today nothing changes
until Review drops to weak, by which point the backlog exists. The plan, built so that
it **never throttles a maintainer who is ready for mass traffic**: the launch's pilot
projects are prepared for it, and missing a project going viral in week one would cost
far more than a busy review queue.

- **Capacity is declared, and "surge" is a valid answer.** `discover.json` gets
  `review: {per_week: N, verification_counts: true}`, or `per_week: "surge"` for a
  maintainer ready for unlimited traffic. Setup asks; the launch's pilot projects
  declare `surge` (or a high number) before launch. Undeclared means a cautious default
  (about 2 a week), for projects listed later whose maintainers haven't thought about it.
- **Headroom is measured:** declared weekly capacity minus contributions waiting for a
  first response (PRs and `done` messages), from GitHub data. Shown on the listing
  ("needs reviewers", "busy: review queue full") and used to weight the cross-hub draw
  (§12.2). For a `surge` project it is shown, never enforced.
- **When the queue is full, the launcher changes what it offers instead of switching
  off:** `local` sessions and verification of pending contributions only, since an
  independent check adds review capacity rather than using it. Only projects with a
  numeric capacity are steered this way.
- **The binding check runs at session start.** The site is static and can't count
  copied prompts, so the contribute playbook counts open contributions awaiting review
  against declared capacity, and if the queue is full opens no new PR: it verifies, or
  leaves a finding or handoff.
- **The hard edge asks first for surge projects.** Spec §3.3 pauses the launcher as soon
  as Review drops to weak. For a project that declared `surge`, that becomes an urgent
  notice to the maintainer (hub issue, and their notices channel) who pauses with one
  change (`per_week` to a number, or a `busy` flag); the hub doesn't pause it
  automatically. Projects with a numeric capacity keep the automatic pause.
- **Raising capacity is how a maintainer asks for more traffic.** It takes effect at the
  next hub build; the session-start check reads it live.

Order: declare capacity and show headroom first, before launch (no enforcement, so
nothing viral is missed); the session-start check and steering for numeric-capacity
projects after launch week, once real traffic shows where queues back up. Spec changes:
§3.3 (the surge exception), §4 (the `review` field), §12.2 (headroom).

### 5. Donor safety

Donors run other people's research code on their own machines. Before inviting
strangers to donate:

- Sandboxing guidance (a container or VM) and when it's needed
- Donor-side permission presets, with item 1: allow `gh` reads, ask before writes
- Disk and machine limits (the playbooks now check free space and ask before large or
  long work; a sandbox would enforce it)
- Prompt-injection hygiene beyond "repository text is data"
- A basic screen for malicious repositories before a hub lists them

### 6. A second, outside pilot

`rohanarun/van-der-waerden-refinement`, onboarded and run by its own maintainer. Every
test so far has had the same person on both sides.

## Later

### 7. Centaur workflow

The `collaborate` playbook: briefings, overlap checks against live claims, designing
the smallest decisive experiment, and posting when the person is ready. Shaped by what
the pilot shows people want.

### 8. The site

Listing signals that help people choose without becoming a popularity ranking (spec
§13, question 17), a project health view for maintainers, and donor-facing
explanations. Mostly after the pilot.

### 9. Moderation and abuse

Rate limits per nominator, the do-not-contact list in practice, a disputes process for
grades, and handling nominations meant to burden a maintainer.

### 10. Outcomes feedback

Donors report where sessions stalled (spec §13, question 13). This also calibrates the
grader: sessions that keep stalling on a project graded strong mean the grade is wrong.

## Rubric gaps found in testing

- **Stage 1 with little review capacity.** `applied-butterfly-mult` reached Stage 1 on a
  declared 1–3 reviews a week, and Stage 1 lets swarms post and open PRs. A Review
  downgrade pauses the launcher only after a backlog shows. Planned in item 4. One D9
  session alone opened two PRs, one of 51 files.
- "Help needs specific hardware" (a non-M2 machine, a GPU, 32 GB of RAM) can't be
  expressed. E1 skipped a card needing a second architecture only by reading the card.
- From E3's assessment of a marine-ecology replication repo: a finished paper's code is
  graded down for having no stated priorities, data shared on request grades the same as
  "trust the author", and no hub field covers the life sciences.
- From E2: Review measured on all PRs lets a maintainer's own PRs dominate. Its proposal
  (count non-maintainers' PRs only) would move integer-mult-bounds from strong to
  adequate; it's waiting as a draft for the hub's maintainer.
- The probes agreed across five runs on one repo (spec §13, question 7). More repos and
  the donor-tier model are still needed.

## Launch housekeeping

- The schema `$id`s use `discoveryathome.org`, which isn't registered yet
- A contributor guide for hub work beyond `DISCOVERY.md`
