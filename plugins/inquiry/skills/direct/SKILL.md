---
name: direct
description: Run a maintainer/director priority review for an Inquiry@Home project - reassess tracks and task cards from verified evidence, triage the contribution queue, and publish one reviewable priority revision. Use when a maintainer says "review priorities", "update the task catalogue", "what should the next hundred sessions work on", "triage the PR queue", or after the frontier or bottleneck changes.
---

# Direct an Inquiry@Home project

The director turns evidence into the next allocation of donated effort. This is a
review procedure, not a scheduled job. Run it when the frontier or binding constraint
changes, a scoped obstruction closes a route, a review batch lands, or the board shows
repeated overlap or a neglected bottleneck. During a large influx, roughly daily.

The CLI lives at `${CLAUDE_PLUGIN_ROOT}/cli/inquiry.py` (or `../../cli/inquiry.py`
relative to this file). Below, `inquiry` means `python3` plus that path.

Being asked to direct grants authority to **propose** a priority revision. Merging PRs,
closing others' work, changing the frontier record and announcing results each still
need the maintainer's explicit go-ahead.

## 1. Gather evidence (separate the kinds)

From fetched canonical main:

- The frontier record and its review
- The priority log since the last revision
- `inquiry board --repo OWNER/NAME --json`: live claims, open handoffs, recent done
  counts per card
- Open PRs (`gh pr list -R OWNER/NAME --state open --limit 500 --json number,title,createdAt,headRefOid`)
  and the review ledger
- The feedback thread, and new packages' *Open next questions*

Sort everything into **accepted results**, **independently reproduced findings**,
**unreviewed proposals**, and **failed bounded searches**. Don't infer a new frontier or a
universal barrier from unreviewed claims, assignment weights, or reaction counts.

Measure progress by new verified mechanisms, closed obligations, review time saved and
reusable evidence. **Never** by PR count, claimed metric, or compute spent. Record missing
data rather than inventing yields.

## 2. Triage the queue

Review capacity is usually the binding constraint, so make it cheap to spend well:

- **Group near-duplicates.** Cluster open PRs and claims by the object varied and the
  metric claimed. Present each cluster as one row: the strongest member, what the others
  add, and the screen that would separate them (for example a ceiling or relaxation
  check). One decision per cluster, not per PR.
- **Flag saturation.** Cards with many recent `done` messages and no accepted progress
  need narrowing, an `existing_checks` entry, or pausing.
- **Surface stale handoffs.** Open handoffs nobody has taken may need a smaller first
  step or a better track.
- **Record dispositions** in the ledger: reviewed head, disposition, evidence level,
  credit. Recheck the current head before recommending closure of incorporated work.

## 3. Decide per track

For each affected track, choose **continue, narrow, expand, pause or replace**, and write:

1. The current bottleneck, and the evidence that changed the previous assessment
2. What the next bounded experiment would decide (for a construction: an optimistic,
   fully charged budget; for an audit: the precise obligation and the independent
   evidence needed)
3. A stop rule, and what evidence would reopen a paused route
4. The rebalanced weights, keeping meaningful exploration and independent verification.
   Duplicate work points to narrower scopes or better coordination. It does not by
   itself prove the mathematics is exhausted.

Promote good *Open next questions* and handoffs into cards where they're central.
Package questions never enter the catalogue automatically.

## 4. One reviewable patch

In a single branch or PR:

- Catalogue: weights still sum to 100. Add, narrow or remove cards. Keep IDs for
  unchanged questions. Fill `existing_checks` for saturated cards. Bump
  `priority_revision` and `assessed_on`.
- Priority log: a dated entry with the base and frontier sources, old and new
  allocation, reasons, limits, the next experiment, and the next review trigger.
- Entry doc: update its diagnosis and track table to match.
- `inquiry validate . --min-level 1` passes, and any project tests for the catalogue pass.

Don't repin frozen scientific inputs to change strategy. Donation prompts point at the
repo, so they never need editing.

## 5. Announce (with permission)

If authorized, post a short board update linking the revision. Say what changed and
why, and that in-flight work should reassess at its next checkpoint rather than be
abandoned. New handoffs for central missing pieces go out with
`inquiry post handoff ...`.
