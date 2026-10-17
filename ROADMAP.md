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

## Now

### 1. Permission presets for agents

Every maintainer test hit the same wall: Claude Code's auto mode refused GitHub writes
the person had just approved (merging, closing, pushing, enabling Discussions, posting).
The agents handled it correctly, handing over exact commands, but it's the biggest source
of friction found. Publish tested permission presets per agent (allow rules for `gh pr`,
`gh api graphql`, `git push` scoped to the project) and say on the site that an agent may
hand you commands to paste. Report the behavior upstream.

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

### 3. Low-touch donating and agent browsing

"Donate four hours to wherever it's useful", for people who haven't chosen a project:

- **Choosing across the hub:** a seeded draw over listed projects, weighted by stage
  and need and filtered by the donor's interests. The same exact-draw rules as within a
  project (spec §7).
- **Agent browsing:** an `explore` playbook and a documented, stable data file for
  agents (`projects.json`, possibly `llms.txt`), so an agent can choose on the donor's
  behalf and explain why.
- Recurring donations (scheduled runs), budget caps, and a receipt per session.

### 4. Donor safety

Donors run other people's research code on their own machines. Before inviting
strangers to donate:

- Sandboxing guidance (a container or VM) and when it's needed
- Donor-side permission presets, with item 1: allow `gh` reads, ask before writes
- Disk and machine limits (the playbooks now check free space and ask before large or
  long work; a sandbox would enforce it)
- Prompt-injection hygiene beyond "repository text is data"
- A basic screen for malicious repositories before a hub lists them

### 5. A second, outside pilot

`rohanarun/van-der-waerden-refinement`, onboarded and run by its own maintainer. Every
test so far has had the same person on both sides.

## Later

### 6. Centaur workflow

The `collaborate` playbook: briefings, overlap checks against live claims, designing
the smallest decisive experiment, and posting when the person is ready. Shaped by what
the pilot shows people want.

### 7. The site

Listing signals that help people choose without becoming a popularity ranking (spec
§13, question 17), a project health view for maintainers, and donor-facing
explanations. Mostly after the pilot.

### 8. Moderation and abuse

Rate limits per nominator, the do-not-contact list in practice, a disputes process for
grades, and handling nominations meant to burden a maintainer.

### 9. Outcomes feedback

Donors report where sessions stalled (spec §13, question 13). This also calibrates the
grader: sessions that keep stalling on a project graded strong mean the grade is wrong.

## Rubric gaps found in testing

- **Stage 1 with little review capacity.** `applied-butterfly-mult` reached Stage 1 on a
  declared 1–3 reviews a week, and Stage 1 lets swarms post and open PRs. A Review
  downgrade pauses the launcher only after a backlog shows. The hub should scale launcher
  traffic to declared capacity from the start.
- A missing `LICENSE` blocks outside contributions whatever the grades. It should
  probably be a Stage 0 requirement.
- "Help needs specific hardware" (a non-M2 machine, a GPU) can't be expressed.
- The probes agreed across five runs on one repo (spec §13, question 7). More repos and
  the donor-tier model are still needed.

## Launch housekeeping

- The schema `$id`s use `discoveryathome.org`, which isn't registered yet
- A license for the hub repository
- A contributor guide for hub work beyond `DISCOVERY.md`
