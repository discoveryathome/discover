# Re-assessment: discovery-at-home (the hub, listed on itself)

- **Project:** `discovery-at-home` · https://github.com/discoveryathome/discover
- **Mode:** re-assess, from [`2026-10-17-claude-reassess.md`](2026-10-17-claude-reassess.md) (at `41aca7a`). `discover hub-check` at this commit reports `assessment-changes` for this entry (DISCOVERY.md, README.md, ROADMAP.md, discover.json, discover/frontier.json, discover/catalog.json, discover/priority-log.md changed).
- **Assessed:** 2026-10-19 at `6016f38` (`origin/main`, "Back the frontier: adapter-test record, a reproduce check, current state matches the records"). Window 2026-10-05 to 2026-10-19. `process_changed_on` is 2026-10-16, so the measurements count 2026-10-16 to 2026-10-19 only.
- **Consent, credit, license:** consent in `discover.json` `hubs` and credit in `credit.policy`, both unchanged. **License: new**, Apache-2.0 at the root `LICENSE` (`28687a0`). I read it: standard Apache 2.0 terms, which permit use and contribution. Spec §3.3 has required a license for Stage 0 since `02fbbe4`.
- **Rubric:** spec v0 §3 at `6016f38`. Changes since `41aca7a`: the license requirement (§3.3), Verification *Coverage* and *Restricted inputs*, Steering *Finished projects*, and declared-capacity semantics (§4 `review`). Only Coverage and the declared-capacity rule bear on this project.
- **Assessor:** Claude Opus 5.5, run unattended. **Probe:** a fresh Claude Haiku subagent. It was given only the standard donation prompt (`discover prompt discoveryathome/discover --minutes 15 --permissions local --seed cc0fdd2a3c6f362cbf307e977cdf5316`), told to stay read-only and to stop after orienting and answer the four questions. It took about 64 s of wall time and 12 tool calls, and read commit `6016f38`.
- **Self-assessed** (spec §12.4), more so than before: 28 of the 30 commits since `41aca7a` carry the same `Claude-Session` trailer as the session that launched this assessment. The work being graded and the grading come from one maintainer's agent session. This record counts toward a stage only after an independent rerun agrees (`independent-rerun`, #25, and `rerun-orientation-probe`, #4).

## What changed since `41aca7a`

30 commits, 86 files. The ones that bear on grades:

- **The previous record's Stage 1 blockers.** Every one was addressed:
  - DISCOVERY.md "Current state" now matches the frontier and `assessments/`.
  - The hub's own records and integer-mult-bounds' record are merged (#23, #24).
  - The frontier corrects "projected grades held" (Orientation and Review were both one grade higher).
  - The six-adapter claim has a record, `discover/records/2026-10-17-adapter-tests.md`.
  - The frontier gained `reproduce`, `reproduce_minutes`, `prerequisites` and `sources`.
  - `discover.json` declares `review.per_week: 5000` (`c6dc608`).
- **The priority log** has revision 2 (2026-10-17): new weights, reasons, a stop rule and a next-review trigger. The catalog was rebuilt to match, with new cards and issues #25-#27, and `assessment-record-format` (#3) retired and closed.
- **First donated-session activity on the hub's own cards.** All of it is from the maintainer's account:
  - `done` blocks on #1, #5 and #26;
  - `handoff` blocks on #1 (second-pilot) and #5 (rubric);
  - open PRs #28, #29 and #30, opened 2026-10-18 18:45 UTC and not yet answered.
- **Card issue bodies regenerated.** The claiming rule is now "skip it only if the task takes under five minutes" on every open card issue, which was previous suggestion 2.
- **Unrelated to grades:** donor-safety tooling (`screen`, `presets`, `prepare`), the `explore` playbook and seeded hub-wide draw, the site move to discoveryathome.org, and 20 new tests.

## Grades

| Property | Grade | Moved? | Evidence |
|---|---|---|---|
| Orientation | **strong** | regraded: adequate → strong | The entry chain changed, so I reran the probe. Starting from AGENTS.md → DISCOVERY.md → `discover/frontier.json`, it answered all four questions with line citations, in about a minute. **Q1:** the problem (DISCOVERY.md:7-12). **Q2:** every listed project has a merged record, all self-assessed, `author-checked`. It quoted the frontier's scope exactly: three projects of three shapes, plus six unlisted repos for adapter tests, not yet a replication or conjecture listing or a donor-tier probe (`frontier.json:3-8`). **Q3:** the bottleneck is independent confirmation (DISCOVERY.md:28-40). Its seed drew `verify-assessments` / `rerun-orientation-probe` (#4), and it checked that #4 and #25 have no claim or handoff. **Q4:** claim on the card issue or a `CLAIM:` issue, PR an assessment ending in a `discover-assessment` block, maintainer review with an independent rerun preferred, and `hub-check --strict` as the frontier check (DISCOVERY.md:49-61). All of these match the repository. The previous record's three contradictions are fixed, and this probe didn't have to resolve any disagreement between the docs. One judgment call: on Q2 it called applied-butterfly-mult "the strongest entry" at Stage 1 without saying integer-mult-bounds is also Stage 1. I count that as framing, not a wrong answer, since the result and scope it gave are the frontier's. A stricter reader would grade adequate on that point. |
| Coordination | adequate | regraded, unchanged | **Spread:** a weighted catalogue (five tracks, 30/25/20/15/10, matching DISCOVERY.md's table) and a seeded draw (`discover pick`). The draw ignores live claims: `discover board repo` reports 0 open handoffs and 0 claims, because it can't read the `github-issues` transport (#27 is open; Discussions are still off). That caps spread at adequate. **Live state** (coordination probe, by the assessor): no track has two open handoffs. There is one on `second-pilot` (#1, "third-party replication shape", 2026-10-18) and one on `rubric` (#5, duplicate-rate cutoffs). Neither has been taken: there are no `claim` blocks and no `responds_to` anywhere in #1-#6 or #25-#30. Finding them took reading every card issue, so adequate, not strong. **Duplicate rate:** unknown. The window since 2026-10-16 has 5 PRs and 5 message blocks, all from one account, under 20. |
| Verification | **adequate** | regraded: weak → adequate | **Authoritative record:** `discover/frontier.json`, with a declared check, `reproduce` (`discover.py hub-check --registry registry/projects --strict`), plus `reproduce_minutes: 1` and its prerequisites (Python 3.9+, `gh` signed in). **Probe:** I ran it from a fresh shallow clone of `6016f38`. It exited 0 in 17 s wall time, with 4 info findings: the entry docs of all three listings changed since their records, and integer-mult-bounds' adapter targets were edited. No discovery of prerequisites was needed. Spot-check: every `sources` entry exists on `main`. The registry's stage and grades match each record's block. The commits the adapter-test record cites (`e549cb8`, `bf92715`, `222da63`, `1620daa`, `292d6d4`) exist and are what it says. **Coverage:** `computation` only. The check confirms the records exist, parse and match the registry; it doesn't check that the grades are right. No grade has had an independent rerun (§9.1, #25), and the adapter-test record was "reconstructed on 2026-10-19" with its probe transcripts uncommitted (record lines 3-5), so its probe comparisons rest on the author's account. That's an unchecked step, so at most adequate. It's above weak because every claim is now pinned to commits and has a stated rerun method someone else can follow. Declared tests: `make test` ran 56 tests, OK, in 5.8 s, and `make sync` left the tree clean. Those check the tooling, not the frontier. |
| Review | **adequate** | regraded: unknown → adequate | **Measured:** unknown. Since `process_changed_on` there have been 5 contributions (#23, #24, #28, #29, #30), all by the maintainer, under 20. #23 and #24 were self-merged in 9 minutes. #28-#30 have no review or comment after about 34 hours. **Declared capacity:** `discover.json` `review.per_week: 5000` (`c6dc608`), with no `note` on who reviews. Under §3.2 and §3.3, declared capacity stands in until there's data, at most adequate, as with applied-butterfly-mult's listed record. See *Doesn't fit the rubric* for why this number deserves a second look. |
| Steering | adequate | regraded, unchanged | `discover/priority-log.md` revision 2 (2026-10-17) is current. It gives reasons per track, a limits section, a next experiment, a stop rule and a next-review trigger (first independent rerun, an outside application, or 30 days), and none of those triggers has fired. The previous record's staleness is fixed. Not strong, for two reasons. The frontier changed after the revision (`updated_on` 2026-10-19, `6016f38`), and §3.2 measures from "whichever is later". There's also no feedback channel shown to be read: every comment on the card issues is the maintainer's own. |

## Stage

**Computed: Stage 1 (Swarm-ready), self-assessed.** Applying §3.3 mechanically:

- **Stage 0:** consent (`discover.json` `hubs`), a disclosed credit policy, a license (Apache-2.0), and Orientation ≥ adequate.
- **Stage 1:** Orientation strong; Coordination, Verification and Review ≥ adequate. Review is met through the declared-capacity exception.
- **Stage 2:** blocked, because not every property is strong.

Under §12.4 the stage counts only after an independent rerun by a different assessor agrees. Until then the listing should label it self-assessed, and launcher permissions should use the last independently confirmed stage, which is none.

What stands between this record and a Stage 1 that counts:

1. **An independent rerun** (#25 / #4) by an assessor outside the maintainer's account. It should check two calls in particular: the Orientation call above (strong versus adequate on Q2's framing), and whether 5,000 a week is a credible declaration.
2. **Fragile grades.** Orientation rests on one probe run, and Review on a declaration alone. If a rerun grades Q2 adequate, or the open PRs #28-#30 are still unanswered once there's enough data, the computed stage falls back to 0.

What blocks Stage 2: Coordination (the board can't see the issues transport, #27, and handoffs have no visible lifecycle), Verification (independent reruns of the records, and committed adapter-test transcripts), Review (measured data), and Steering (a demonstrably read feedback channel).

## Suggestions (don't affect grades)

1. **Respond to #28-#30, or say who reviews.** Add a `note` to `review` (§4), so the 5,000 figure has a reviewer named behind it.
2. **Refresh the frontier.** Its statement says the hub is "Stage 0". If this record lands, that becomes stale, so update the frontier in the same PR.
3. **Close the loop on handoffs.** When a `done` follows from an earlier handoff, add `responds_to`. Until #27 lands, consider listing open handoffs in DISCOVERY.md or on a pinned issue, so `board` isn't the only route.
4. **Commit the adapter-test transcripts,** or regenerate them when the four unrerun adapters are rerun. The record says itself that this is open.
5. **Clarify ROADMAP's dates.** ROADMAP.md says "Status as of 2026-10-17", but the file was edited on 2026-10-18.
6. **Fix `discover board` for a remote repo.** `discover board OWNER/NAME` fails with "pass --repo", because the positional argument is a path, which a donor won't expect.
7. **Close #1, or retitle it.** #1 (`assess-different-shape`) has a `done` and a `handoff` but stays open under its original title. Retitling it to the remaining shape would make the open work clearer.

## Doesn't fit the rubric

- **A declared capacity alone unlocks Stage 1, on the maintainer's word.** The hub has one listed maintainer, and it declared 5,000 PRs a week, roughly 700 a day. No `note` says who reviews (agents? a rota?), and three of the maintainer's own PRs are waiting. The rubric takes the declaration as given, and the computed stage moves 0 → 1 on it. A plausibility rule (capacity per listed reviewer, or a required `note` above some number), or a cap on what a declaration alone can unlock, would close this gap. PR #29 (open) works on the measured side of Review, not the declared one.
- **Steering's "whichever is later" clock.** A frontier edit that only backs existing claims (`6016f38`) makes a two-day-old priority revision count as stale for strong. That penalizes fixing the record. The clock could run from the last change to the frontier's `statement` or scope, rather than `updated_on`.
- **Coverage vocabulary on a review-only project.** `computation`, `formal proof` and `reviewed argument` are shaped for theorems. For a hub whose claims are assessment grades, the analogue of "the argument is checked" is an independent rerun of the probes. I recorded `computation`, which is the closest fit. A `rerun` or `reproduced` value would fit meta and benchmark projects better.
- **Same-session self-assessment.** §12.4's `self_assessed` flag doesn't distinguish "the maintainer's project" from "the same agent session that just made the changes being graded". This run is the second case. That doesn't change any grade, but a reviewer would want to know.
- **Coordination probe with fewer than two handoffs per track.** The playbook says to "find two open handoffs on one track". No track has two, so I took the two that exist on different tracks. The playbook doesn't say what to do in this case.
- **Probe timing** is about a minute against a 15-minute budget, as before, so the budget doesn't discriminate for this repo.

Notes on this run: unattended. The screen (`discover screen repo`, helper hash checked) found 0 high and 4 warnings. All four are documentation text: ROADMAP.md:142 and :173 describe sandbox behaviour, and site/app.js:415-416 are `sudo` install lines shown to users for bubblewrap. All are benign. The only code run was the declared `reproduce` and `make test`/`make sync`, in a disposable shallow clone (`check/`). The probe ran `discover pick` read-only. The session folder uses about 7 MB. No posts, issues, PRs or pushes.

## For the hub's tools

```discover-assessment
{
  "schema": "discover-assessment/v0",
  "project": "discovery-at-home",
  "repo": "discoveryathome/discover",
  "assessed_commit": "6016f38572cce74d464dc9195c7b57a0dcfcf920",
  "assessed_on": "2026-10-19",
  "window": "2026-10-05/2026-10-19",
  "rubric": "v0",
  "assessor": "claude",
  "probe_model": "claude-haiku",
  "mode": "re-assess",
  "previous": "assessments/discovery-at-home/2026-10-17-claude-reassess.md",
  "self_assessed": true,
  "entry_paths": [
    "AGENTS.md",
    "DISCOVERY.md",
    "README.md",
    "ROADMAP.md",
    "LICENSE",
    "discover.json",
    "discover/frontier.json",
    "discover/catalog.json",
    "discover/priority-log.md",
    "discover/records/2026-10-17-adapter-tests.md"
  ],
  "grades": {
    "orientation": "strong",
    "coordination": "adequate",
    "verification": "adequate",
    "review": "adequate",
    "steering": "adequate"
  },
  "stage": 1,
  "adapter_dependent": [],
  "verification_covers": ["computation"]
}
```
