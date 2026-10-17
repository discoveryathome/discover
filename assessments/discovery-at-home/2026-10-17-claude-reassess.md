# Re-assessment: discovery-at-home (the hub, listed on itself)

- **Project:** `discovery-at-home` · https://github.com/discoveryathome/discover
- **Mode:** re-assess, from [`2026-10-17-claude.md`](2026-10-17-claude.md) (at `25dce2c`), prompted by `discover hub-check` (`assessment-stale`: DISCOVERY.md, discover.json, discover/frontier.json changed).
- **Assessed:** 2026-10-17 at `41aca7a` (`origin/main`, "Fixes from the hub's assessment of itself"). Window 2026-10-03 to 2026-10-17; `process_changed_on` is 2026-10-16, so measurements count 2026-10-16 to 2026-10-17 only.
- **Consent and credit:** unchanged since `25dce2c` (`discover.json` `hubs`; `credit.policy`).
- **Rubric:** spec v0 §3 at `41aca7a` (the only rubric change since `25dce2c` is the §12.4 self-assessment paragraph). **Assessor:** Claude Opus 5.5, run unattended. **Probe:** fresh Claude Haiku agent given only the donation prompt (`discover prompt discoveryathome/discover --minutes 15 --permissions local`, seed `2379a0b63ff3070e1b28b22d8dcdf4a5`), told to stay read-only and answer the four questions; about 1 minute, 12 tool calls.
- **Self-assessed** (spec §12.4): the hub grading itself, by an agent working for the hub's maintainer. This record counts toward a stage only after an independent rerun by a different assessor agrees (`rerun-orientation-probe`, #4).

## What changed since `25dce2c`

One commit, `41aca7a`, applying fixes the previous assessment suggested:

- `DISCOVERY.md` "Current state" rewritten (records exist, a schema, six adapter tests, a weekly hub check); the claiming rule now matches `contribute.md` (claim unless under five minutes); "Submit" names the `discover-assessment` block and schema.
- `discover/frontier.json`: new `statement`, `status`, `scope`; integer-mult-bounds' Stage 1 explicitly doesn't count; `probe-agreement` and `routine-cost` assumptions updated; `updated_on` 2026-10-17.
- `discover.json` and both registry `contact`s: maintainer handle `colkitt` → `Mister-Meeseeks` (suggestion 1).
- `spec/v0.md` §12.4 and the assessment schema: `self_assessed`.
- Unrelated to grades: a fixed code fence in `contribute.md`, workflow action bumps, the rebuilt `.pyz` and site copies.

Unchanged: `discover/catalog.json`, `discover/priority-log.md`, `ROADMAP.md`, `AGENTS.md`, `README.md`, the coordination transport, the card issues (#1-#6), and no new issues or PRs since the previous window's last event (#22).

## Grades

| Property | Grade | Moved? | Evidence |
|---|---|---|---|
| Orientation | **adequate** | weak → adequate | Entry chain changed, so the probe was rerun. It answered all four questions from AGENTS.md → DISCOVERY.md → `discover/frontier.json`, and this time Q2 matches the repo: it named the applied-butterfly-mult records as the accepted result, read their grades from `assessments/applied-butterfly-mult/`, gave the evidence level (author-checked) and said integer-mult-bounds' Stage 1 doesn't count (`frontier.json:3`). It no longer lists `assessment-record-format` (#3) as unbuilt, and Q4 (claim on the card issue before starting, PR an assessment ending in a `discover-assessment` block, maintainer review with a `verify-assessments` rerun preferred) matches DISCOVERY.md:47-54. Not strong, because the entry docs still disagree with the repo about the current result, and the probe had to resolve it. (1) DISCOVERY.md:17-18 says the two recorded shapes are "an exact-certificate math project and a benchmark project"; the frontier says a benchmark project and the hub itself; `assessments/` at `41aca7a` holds only applied-butterfly-mult. The exact-certificate project is integer-mult-bounds, which has no record. (2) The frontier counts "the hub itself" as recorded, but `assessments/discovery-at-home/` isn't on `main` (the previous record sits only on this unmerged branch). (3) The frontier says the nomination's projected grades "held, with Orientation one grade higher", but projected Review was `unknown` (projected stage 0) and listed Review is `adequate` (stage 1). The probe caught (1), (2) and (3) and answered from the frontier, so these omissions didn't misdirect it; a donor reading only DISCOVERY.md could think integer-mult-bounds is assessed. |
| Coordination | adequate | no | Mechanism unchanged since `25dce2c`: same catalog, same seeded draw (this probe's seed drew `gallery` / `choosing-signals`, #6, which has no comments or claims), same `transport: github-issues` that `discover board`/`post` can't read (Discussions still off; the probe confirmed `hasDiscussionsEnabled: false`). Ceiling adequate. Measured part unknown: no claims, handoffs or outside PRs. Live state rechecked: #1-#6 unchanged, still no `discover` blocks. #3 still has no note, although DISCOVERY.md now says the format exists; the probe inferred that correctly from the docs, not from the issue. Fixed since: the DISCOVERY.md claiming rule now matches `contribute.md`. Still stale: the card issue bodies say "Sessions under an hour may skip claiming" (#3 body, line 29). |
| Verification | **weak** | no (rechecked) | The frontier changed, so this was regraded, not carried. Better: it drops the unrecorded integer-mult-bounds claim, and its applied-butterfly-mult claim has two records anyone can recheck at a stated commit. Still weak: `evidence_level: ["author-checked"]`, `verification_profile: review-only`, no `reproduce` and no documented check of the frontier itself. Two of its claims have nothing behind them on `main`: the hub's own record (not merged) and "adapters were tested on six third-party repositories, each probed with and without its adapter" (only prose in ROADMAP.md:17-19; one adapter file, no probe records). Those can be accepted only by trusting the author. Declared tests (`make test`) from a fresh shallow clone of `41aca7a`: 36 tests, OK, 1.1 s; `make sync` left the tree clean. They check the tooling, not the frontier. |
| Review | unknown | no | Unchanged since `25dce2c`: no issues or PRs opened since #22 (`gh issue list`, `gh pr list`, all states); `41aca7a` was pushed straight to `main`. Zero outside contributions in the window, under 20, and no declared review capacity in DISCOVERY.md:53-54 or `discover.json`. |
| Steering | adequate | no (rechecked) | `discover/priority-log.md` is unchanged (revision 1, 2026-10-16) and now more clearly stale: its premise ("applied once, by hand, to one project of one shape") contradicts the frontier updated on 2026-10-17, and its stated trigger ("after the first second-pilot assessment lands") has fired without a revision. Priorities are still in one place with reasons, so adequate; strong would need a revision since the frontier last changed and a feedback channel shown to be read. |

## Stage

**Stage 0 (Explorable), self-assessed.** Computed mechanically (§3.3): consent (`discover.json` `hubs`), a disclosed credit policy, and Orientation adequate meet Stage 0. Stage 1 is blocked by Orientation (needs strong), Verification (weak) and Review (unknown, no declared capacity). Under §12.4 this record counts toward the stage only after an independent rerun agrees, so until #4 is done the listing should show it as self-assessed.

What blocks Stage 1:

1. **Orientation:** make DISCOVERY.md "Current state" agree with the frontier (the two shapes are benchmark and the hub itself, not an exact-certificate project), and correct the frontier's "projected grades held" (Review also moved, unknown → adequate). Merge the hub's own records to `main`, or drop "and the hub itself" until they are.
2. **Verification:** back the six-adapter claim with records (probe transcripts or a summary file with commits), and name a check for the frontier (for example, an independent rerun of a recorded probe at its commit on the `verify-assessments` track).
3. **Review:** declare review capacity for hub PRs.

## Suggestions (don't affect grades)

1. Note on #3 what's done (the schema, `self_assessed`) and what's left (rewriting the integer-mult-bounds smoke test as a record), and on #1 its status.
2. Regenerate the card issue bodies: the "under an hour" claiming rule and the `discover 0.1.0` positive control are stale (previous suggestions 3 and 4, half done).
3. Revise the priority log: its trigger has fired.
4. Previous suggestions still open: coordination transport (Discussions vs. issues support in `board`/`post`), `featured: true` on integer-mult-bounds without a record, and self-merging grade-affecting changes. Done: the maintainer handle (`Mister-Meeseeks` in `discover.json` and both registry entries).

## Doesn't fit the rubric

- **Stage and `self_assessed` together.** §12.4 says a self-assessed record "counts toward a stage only after an independent rerun agrees", but the registry's `stage` must be a copy of the block, and §3.3 says the stage is computed mechanically. I set `stage: 0` as computed and `self_assessed: true`, and left showing it as self-assessed to the listing. The spec doesn't say whether the registry should hold the computed stage or the last independently confirmed one (here `assessed`).
- **Record on an unmerged branch.** The frontier at `41aca7a` cites the hub's own assessment, which exists only on this branch. Whether a frontier may cite records still under review isn't covered.
- **Two records on one date by one assessor.** The record path `<YYYY-MM-DD>-<handle>.md` collides with the previous record (same day, same assessor). I used a `-reassess` suffix, as `-listed` was used for applied-butterfly-mult.
- **Probe timing** is again far from the 15-minute budget (about 1 minute), so the budget doesn't discriminate for a repo this size.

Notes on this run: unattended, so the only code run was the declared `make test` and `make sync` in a disposable shallow clone (`~/discover-work/assess-discoveryathome-discover-reassess/repo`, 1.4 MB). The probe ran `discover pick` (a declared task-selection command) read-only. No posts, issues or PRs.

## For the hub's tools

```discover-assessment
{
  "schema": "discover-assessment/v0",
  "project": "discovery-at-home",
  "repo": "discoveryathome/discover",
  "assessed_commit": "41aca7a48882d8fdc6fcc184452d3c728e607010",
  "assessed_on": "2026-10-17",
  "window": "2026-10-03/2026-10-17",
  "rubric": "v0",
  "assessor": "claude",
  "probe_model": "claude-haiku",
  "mode": "re-assess",
  "previous": "assessments/discovery-at-home/2026-10-17-claude.md",
  "entry_paths": [
    "AGENTS.md",
    "DISCOVERY.md",
    "README.md",
    "ROADMAP.md",
    "discover.json",
    "discover/frontier.json",
    "discover/catalog.json",
    "discover/priority-log.md"
  ],
  "grades": {
    "orientation": "adequate",
    "coordination": "adequate",
    "verification": "weak",
    "review": "unknown",
    "steering": "adequate"
  },
  "stage": 0,
  "adapter_dependent": [],
  "self_assessed": true
}
```
