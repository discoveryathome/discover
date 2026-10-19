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
  six third-party repositories, with and without each adapter
  ([record](discover/records/2026-10-17-adapter-tests.md)). Three first-round adapters
  left donors less sure where to help; the playbook was fixed, and the two adapters
  rerun under it matched or beat the bare repo. The other four haven't been rerun.
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
guidance (a script that makes a fresh seed per run), and review headroom as the draw's
second weight (item 4, after launch).

### 4. Matching launcher traffic to review capacity

Review, not donated compute, is what a project can absorb. Built so that it **never
throttles a project by default**: the launch's pilot projects are prepared for mass
traffic, and missing a project going viral costs far more than a busy review queue.

**Built (pre-launch half, 2026-10-18):**

- **Declared capacity** (spec §4): `review: {per_week: N | "surge", paused, note}` in
  `discover.json`, or in the adapter for repos without one. Undeclared means no limit.
  `paused: true` is the maintainer's one switch to close the launcher; nothing else
  closes it. Setup asks (question 6). integer-mult-bounds declares `surge`.
- **What's waiting, measured at each build:** open, non-draft PRs from outside the
  project with no response from anyone but their author (`review.py`). Shown on the
  listing with the declaration ("ready for surge traffic", "needs reviewers", "busy:
  review queue full", "paused by its maintainers") and in `agents.json`. First reading:
  integer-mult-bounds 230 waiting (of 432 open, oldest 5 days; its merges run in queue
  passes); the other two 0.
- **Spec §3.3:** a Review downgrade sends the maintainer an urgent notice instead of
  pausing the launcher; only a numeric `per_week` opts a project in to steering.

**After launch week**, once real traffic shows where queues back up, and only for projects
with a numeric capacity:

- Headroom as the cross-hub draw's second weight (§12.2).
- **The session-start check:** the contribute playbook counts what's waiting against
  the declared capacity, and when the queue is full opens no new PR: it verifies a
  pending contribution, or leaves a finding or handoff.
- The urgent notice itself, from the hub check, when a Review grade drops to weak.
- `done` messages without a response, beside PRs, in the waiting count.

### 5. Donor safety (built, first version)

Donors run other people's research code on their own machines. Built (2026-10-18; spec
§12.7):

- **`discover screen`**: a static screen of a clone for files agents load by themselves,
  install hooks, piped downloads, executed encoded code, credential paths, collection
  endpoints, agent-override text, invisible characters and committed executables. It
  reads tracked files only and runs in seconds on the listed repos. Intake runs it on
  every submission (high findings label the PR `screen-review`, merged only once
  explained), and the contribute, verify and assess playbooks run it before any of a
  project's code. First pass on the listings: the hub and integer-mult-bounds (sparse
  checkout) clean; applied-butterfly-mult has no high findings but commits Mach-O
  executables under `results/`.
- **Sandboxed donor presets:** `donor-local`, `donor-post` and a new `donor` (attended,
  asks before posting) turn on Claude Code's sandbox: writes only inside the folder the
  agent starts in (any folder; `--work-dir` adds one),
  credential folders unreadable, network limited to GitHub, the site and package
  registries (`--allow-domain` for more); where no sandbox exists (native Windows, Linux
  without bubblewrap) sessions run unsandboxed and the preset command warns. Tested headless with
  `claude -p`: writes outside, reading `~/.ssh`, other hosts and `git push` refused;
  `gh` reads worked (with `enableWeakerNetworkIsolation`, which Go's TLS needs on macOS).
  A test session found that `git -C path push` slipped past the prefix deny rule (it
  pushed a scratch branch, deleted at once): deny rules now also match options before the
  subcommand, and `donor-local` redirects pushes to an invalid host. Clones need
  `git clone` outside the sandbox and a relative target; the playbooks now clone that way. A
  second 15-minute session on applied-butterfly-mult then ran end to end sandboxed: it
  cloned, screened (0 high), ran the project's Python tests, committed a verification
  locally and pushed nothing. Remaining friction: `sysctl` (chip name) is blocked, and
  the agent's own checker rejects `cd X && git ...` and some variable forms, which it
  rewrote.
- **Playbook rules:** agents start in the session folder, never inside a clone (headless
  runs load a folder's hooks and MCP servers without asking); no `sudo`, global installs,
  piped downloads or committed binaries; text asking to widen permissions or hide
  something is quoted to the person as a finding.
- **Persistent clones and the web** (2026-10-18): a hook planted in a repo's
  `.claude/settings.json` ran in a headless session started inside it, so donors who keep
  a clone for contributing write the donor preset into that clone's
  `.claude/settings.local.json` once and then just run `claude`: it outranks the repo's
  settings, sets `disableAllHooks`, and names the repo's MCP servers as disabled (tested
  against a hostile settings file; a repo can still add to merged lists such as allowed
  hosts, which the screen flags). Left: new MCP servers arriving with a pull start until
  the preset is rerun, and there's no name-independent switch for them. The contribute playbook
  supports working in such a clone (fresh branch from the fetched default, notes kept
  out of commits, a screen after every fetch). Web search and fetch are allowed in donor
  presets; the sandbox's host list, which now includes arXiv, DOI, Crossref, OpenAlex,
  Semantic Scholar, Zenodo and the OEIS, limits only commands.
- **The site** explains what protects donors and what doesn't.

Left:

- **Credentials held by tools.** Code inside the sandbox can still run `gh auth token`,
  and GitHub is reachable, so a malicious project could act as the donor on GitHub. The
  guidance is a container or VM with a fine-grained read-only token (or none); a tested
  container recipe is still to do (Docker wasn't available to test).
- The sandbox on Linux and WSL2 (only macOS tested), and `failIfUnavailable` where no
  sandbox exists.
- Codex: its sandbox confines writes only; no domain or credential limits yet.
- A full-checkout screen of integer-mult-bounds, and a screen in the weekly hub check.

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
  declared 1–3 reviews a week, and Stage 1 lets swarms post and open PRs. Item 4 now
  shows the queue and gives the maintainer a pause switch; steering for numeric
  capacities comes after launch. One D9 session alone opened two PRs, one of 51 files.
- Fixed 2026-10-18 (spec §3.2, §4, §7): hardware needs (`requirements` in the manifest,
  `requires` on a card; `discover pick` marks cards a machine can't serve); a finished
  project's statement of what's still welcome counts as its priorities; restricted data
  with a public pipeline, stated access route and hashed inputs can grade adequate; and
  a suggested domain list including `life-sciences` and `ecology`. Grade effect on
  Fingarfan/BlueForests: none yet (it states neither completion nor an access route), but
  both are now reachable.
- From E2: Review measured on all PRs lets a maintainer's own PRs dominate. Its proposal
  (count non-maintainers' PRs only) would move integer-mult-bounds from strong to
  adequate; adopted in spec §3.2 (contributions, the 7-day denominator, the backlog test).
- Fixed 2026-10-18 (spec §3.2, Coverage): a theorem whose declared check covers only the
  computations around it grades Verification at most adequate; strong needs a formal
  proof or recorded independent reviews of the steps. Assessments record what the check
  covers (`verification_covers`), shown beside the grade. Found pre-assessing
  `rohanarun/van-der-waerden-refinement`, whose CI checks every parameter margin of a
  conditional bound whose proofs nobody has reviewed.
- The probes agreed across five runs on one repo (spec §13, question 7). More repos and
  the donor-tier model are still needed.

## Launch housekeeping

- The schema `$id`s use `discoveryathome.org`, which isn't registered yet
- A contributor guide for hub work beyond `DISCOVERY.md`
