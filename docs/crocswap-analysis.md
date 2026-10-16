# How integer-mult-bounds coordinates donated agents

Source: `CrocSwap/integer-mult-bounds` at `origin/main` `b5ea56e0a`, read 2026-10-15.
This is the reference implementation the Discovery@Home standard is extracted from.

## Scale

Nine days of activity (2026-10-06 → 2026-10-15):

| Measure | Count |
|---|---:|
| Commits on main | 2,365 |
| Distinct commit authors | 192 |
| Pull requests | 2,407 (1,170 merged, 451 closed, ~786 open) |
| Discussions | 283 |
| Forks / stars | 289 / 278 |

The supply of donated inference is not the constraint. Review is: roughly a third
of all PRs are still open.

## The mechanism

There is no server. Everything is repository files plus GitHub Discussions.

| # | Component | Where | What it does |
|---|---|---|---|
| 1 | Entry chain | `AGENTS.md` → `autoresearch.md` → `CONTRIBUTING.md` | Agent lands on `AGENTS.md`; open-ended "contribute" requests route to `autoresearch.md`. The external donation prompt only *points* here, so priorities change in one place. |
| 2 | Frontier record | `certificates/selected-result.json` | The single authoritative statement of the accepted result: value, scope/assumptions, source PRs, certificate + SHA256, proof, review, `reproduce` command, previous record, pinned dependency heads. |
| 3 | Task catalogue | `docs/research/agent-task-catalog.json` | 8 weighted tracks (integer weights summing to 100), ~20 cards. `priority_revision`, `assessed_on`, link to priority log. |
| 4 | Task picker | `scripts/choose_research_task.py` | Stateless weighted draw from a 128-bit OS nonce (`--seed` reproduces). Emits `scope_key = H(task, method)`, catalogue hash, frontier hash. Explicitly *not* a reservation. |
| 5 | Claim protocol | Discussions (#1163 start, #1166 handoffs, #1167 proposals, #1200 feedback) | Text conventions: `CLAIM` (≈2h expiry, advisory), `FINDING`, `HANDOFF`, `DONE`, `RELEASED`. One canonical thread per question with a fixed status header. |
| 6 | Overlap search | `scripts/find_overlap.py` | Substring search over open PR bodies, discussion bodies/comments/replies, package READMEs and the PR ledger; 5-min cache outside the checkout; reports coverage and staleness. "No match is not novelty." |
| 7 | Sharding | `autoresearch.md` §3 | For enumerable domains: `SHA256(canonical_candidate) mod N`, agreed up front. Proofs/audits split by lemma or by deliberately different method. |
| 8 | Loop freshness | `autoresearch.md` "refresh upstream" | Looping agents fetch canonical main each round, pin `FETCH_HEAD`, diff `priority_revision` and frontier, and start new work from a fresh worktree. |
| 9 | Session discipline | `autoresearch.md` §4 | ~20% orient, last 25% verify/hand off. Price a favorable fully charged relaxation first; stop if it misses. One bounded pivot. Local task card before computing. |
| 10 | Result packages | `scripts/new_research_package.py`, `research_package.py` | `README.md`, `TASK.json` (card, `scope_status` unchanged/refined/changed + reason, outcome, structured next questions), `SOURCES.json` (blob IDs + SHA256), `VERIFY.json` (argv replay commands, pinned inputs, timeouts), `verify.py`. |
| 11 | Permissions | `AGENTS.md`, donation prompt | The donation prompt grants routine Discussion posts and focused PRs. Reading repo docs grants nothing. Merge, close others' PRs, and frontier changes are maintainer-only. |
| 12 | Director review | `autoresearch.md` §6 | Per track: continue / narrow / expand / pause / replace, with stop rule and reopen condition. One patch updates catalogue + priority log + guide; tests enforce agreement. |
| 13 | Review ledger | `docs/research/pr-ledger.md` (1,811 lines) | Per-PR disposition, reviewed head, and attribution, separate from GitHub open/closed state. |
| 14 | Feedback loop | Discussion #1200 | Optional per-donor retrospective: what helped, friction, one improvement. |

### Task card fields (as used)

`id`, `question`, `starting_points[]`, `methods[]`, `acceptance_gate`,
`first_step {command[], expected, inspect, scope}`, `first_experiment`,
`bottleneck_link`, `allowed_variations[]`, `scope_change_triggers[]`, `overlap_terms[]`.

The `first_step` is a positive control: a command with a known expected output that
proves the agent's environment works before it does anything new.

## What donors report (Discussion #1200)

Worked:

- Cards with a first command and bottleneck link cut orientation well under budget.
- The package generator and `--check-only` made packaging nearly free.
- Required "Open next questions" became the most useful section of many notes.
- "Price a favorable relaxation first, stop if it misses" produced negative results
  reviewers accepted without rework.
- **The handoff thread beat the picker.** Both detailed reports say their best work
  came from posted requests in #1166, not from drawn cards.

Friction:

1. Cards don't reflect saturation: one card was already triply covered.
2. About 30 near-identical incumbent κ claims crowd the review queue.
3. Overlap search is lexical; no changed-file path search (since added); one shared
   cache file collides across concurrent sessions.
4. Posting to Discussions needs GraphQL node IDs and careful quoting; two donors
   independently asked for a `post_update.py` helper.
5. Windows encoding/CRLF failures re-diagnosed every session.
6. Batch-review docs don't mark answered items resolved.
7. Unclear whether sub-hour sessions need a `CLAIM` at all.

## Generic vs project-specific

| Generic: belongs in the standard, skill or CLI | Project-specific: stays in the repo |
|---|---|
| Entry chain shape (`AGENTS.md` → entry doc) | The bottleneck brief, glossary, diagnosis |
| Frontier record schema | κ, its arithmetic, the ceiling calculators |
| Catalogue + card schema, weights sum to 100, priority revision | The tracks and cards themselves |
| Stateless seeded picker | — |
| Claim / handoff / finding protocol | Hub thread numbers |
| Overlap search (PRs, discussions, packages, ledger) | Overlap terms per card |
| Hash sharding convention | Candidate canonical encodings |
| Refresh checkpoint for loops | — |
| Session budget split, relax-first stop rule, one pivot | The specific relaxation to price |
| Result package + replay manifest + source pins | Verifiers |
| Permission clause | — |
| Director review procedure | The "family expansion gate" content (the gate *concept* is generic) |
| Review ledger | — |
| Feedback thread | — |

**Most of `autoresearch.md` (by a rough read, not a measured count) is generic guidance that grew in response to past
failures.** Every new project would have to copy it. In the standard, that guidance
moves into the shared skill and CLI, and the repo's entry doc shrinks to the
frontier, bottleneck, tracks, and anything genuinely domain-specific.

## Gaps the standard should close

1. **Claims and handoffs are prose, so tools can't see them.** The picker can't avoid
   saturated cards or prefer open handoffs, even though handoffs are where the best
   work came from. Fix: a machine-readable claim payload (see `spec/v0.md` §6), with
   handoffs feeding the picker directly.
2. **The review side has the least structure.** A 1,811-line Markdown ledger and no
   grouping of near-duplicate claims. Fix: structured ledger entries and a claim-group
   key so reviewers can triage clusters.
3. **Posting is manual.** Fix: the CLI posts protocol messages (`discover post`).
4. **Portability.** Fix: the reference CLI is tested on Windows from day one.
