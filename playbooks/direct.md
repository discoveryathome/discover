---
name: direct
description: Run a maintainer priority review for a Discovery@Home project - reassess tracks and task cards from verified evidence, triage the contribution queue, and publish one reviewable priority revision. Use when a maintainer says "review priorities", "update the task catalogue", "what should the next hundred sessions work on", "triage the PR queue", or after the accepted result or bottleneck changes.
---

# Direct a Discovery@Home project

Directing turns evidence into the next allocation of donated effort. It's a review, not
a scheduled job. Run it when the accepted result or the bottleneck changes, a bounded
negative result closes a route, a batch of reviews lands, or the board shows repeated
overlap or a neglected bottleneck. During a large influx, roughly daily.

Being asked to direct means you may **propose** a priority revision. Merging PRs,
closing others' work, changing the record of accepted results, and announcing anything
each still need the maintainer's explicit go-ahead.

{{TOOLS}}

## 1. Gather evidence, keeping the kinds separate

From the freshly fetched default branch:

- The record of what's accepted, and its review
- The priority log since the last revision
- The coordination channel: live claims, open handoffs, recent completions per card
  (`discover board --repo OWNER/NAME --json` does this for Discussions)
- Open PRs (`gh pr list -R OWNER/NAME --state open --limit 500 --json
  number,title,createdAt,headRefOid`) and the review ledger
- Independent verifications recorded under packages' `verifications/` folders
- The feedback thread, and new packages' *Open next questions*

Sort everything into **accepted results**, **independently verified findings**,
**unreviewed proposals**, and **failed bounded searches**. Don't infer a new result or
a universal barrier from unreviewed claims, assignment weights, or reaction counts.

Measure progress by verified mechanisms, closed obligations, review time saved and
reusable evidence. **Never** by PR count, claimed numbers, or compute spent. Record
missing data rather than inventing it.

## 2. Triage the queue

Review is usually the constraint, so make it cheap to spend well:

- **Group near-duplicates.** Cluster open PRs and claims by the object varied and the
  claim made. Present each cluster as one row: the strongest member, what the others
  add, and the check that would separate them. One decision per cluster, not per PR.
- **Route verification.** Mark which results need an independent check before you'll
  accept them, so verify sessions find them first.
- **Flag saturation.** Cards with many recent completions and no accepted progress need
  narrowing, an `existing_checks` entry, or pausing.
- **Surface stale handoffs.** Open handoffs nobody has taken may need a smaller first
  step or a better track. Mark handoffs that have been taken up, so newcomers don't
  mistake them for open.
- **Record dispositions** in the ledger: reviewed head, disposition, evidence level,
  credit. Recheck the current head before recommending closing incorporated work.

## 3. Decide per track

For each affected track, choose **continue, narrow, expand, pause or replace**, and
write:

1. The current bottleneck, and the evidence that changed the previous assessment
2. What the next bounded experiment would decide
3. A stop rule, and what evidence would reopen a paused route
4. The rebalanced weights, keeping real exploration and independent verification.
   Duplicate work points to narrower scopes or better coordination; it doesn't by
   itself prove a route is exhausted.

Promote good *Open next questions* and handoffs into cards where they're central.
Package questions never enter the catalogue automatically.

## 4. One reviewable patch

In a single branch or PR:

- **Catalogue:** weights still sum to 100. Add, narrow or remove cards; keep IDs for
  unchanged questions; fill `existing_checks` for saturated cards; bump
  `priority_revision` and `assessed_on`.
- **Priority log:** a dated entry with the base and sources, old and new allocation,
  reasons, limits, the next experiment, and the next review trigger.
- **Entry doc:** update its diagnosis and track table to match.
- If the project changed how it coordinates or reviews, move `process_changed_on`
  forward in `discover.json` and say what changed.
- With the helper, `discover validate .` passes; any project tests for the catalogue
  pass.

Donation prompts point at the repo, so they never need editing.

## 5. Announce (with permission)

If authorized, post a short update in the coordination channel linking the revision:
what changed and why, and that in-flight work should reassess at its next checkpoint
rather than be abandoned. Post new handoffs for central missing pieces.
