# Roadmap

What the hub's maintainers plan to build next, in order. Donated hub work is allocated
separately, by the tracks in [`discover/catalog.json`](discover/catalog.json); when a
roadmap item opens work that donors can pick up, it gets cards there.

Status as of 2026-10-17. Onboarding is built and smoke-tested end to end on
`CrocSwap/applied-butterfly-mult`: both roles, every goal, intake (including duplicates
and consent on a nominated entry), the hub assessment with as-is and projected grades,
and the upgrade from catalogued to listed by both paths (the repo's consent record, and
an application). The project stays listed at Stage 1 for item 1.

## Now

### 1. The donation loop, end to end

Onboarding is tested; what happens after listing isn't, under the prompt-first tooling.
On two listed projects, one with its own protocol files (`applied-butterfly-mult`) and
one listed through an adapter (`integer-mult-bounds`), run and check:

- `contribute` sessions: the seeded draw spreads donors, open handoffs are preferred,
  claims and handoffs post correctly, the receipt is honest
- `verify` sessions and their `verifications/` records
- the maintainer's side: triaging donated PRs, recording dispositions in the ledger
- a `direct` session producing a priority revision from that evidence
- on the adapter project: agents find their way through the adapter, use the project's
  own picker, and report drift when the adapter is wrong

Done when a batch of sessions runs without supervision and the maintainer can review
the output in one sitting.

### 2. Hub operations: adapters and keeping listings fresh

A listing goes stale as soon as its project changes. One loop covers both writing
adapters and keeping them current:

- A **scheduled hub run** (weekly, and on demand): recheck consent records, refresh
  boards, detect material changes to a project's entry chain since its last assessment,
  and flag adapters that no longer validate. Each flag opens a hub-work issue.
- A **re-assess** mode in the assess playbook: start from the previous record, say what
  changed, and rerun probes only where needed (spec §3.4).
- Adapters (spec §12.5) as a routine: written by the assess playbook, kept current by
  donors' drift reports and the scheduled run, retired when a repo adopts its own files.
  `integer-mult-bounds` has the first one. Also the nomination form's missing
  draft-branch field and an assessment record schema (spec §13, question 10).

Done when a listed project can change for a month and its listing stays accurate with
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
- Permission presets per agent, e.g. a Claude Code settings snippet that allows `gh`
  reads and asks before writes. Auto modes can block approved writes; the playbooks
  already fall back to commands to paste, and the site should say so.
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
