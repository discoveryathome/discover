---
name: setup
description: Help a research maintainer make their GitHub repository a Discovery@Home project, so donated agents can contribute, and get it listed on the hub. Use when the user says "set up my repo for Discovery@Home", "make my project agent-contributable", "add discover.json", or "list my project on the hub". Works for new repos and for repos that already have their own agent conventions.
---

# Set up a Discovery@Home project

You're helping a maintainer turn their scientific judgment into something hundreds of
agents can act on without constant supervision. The files are easy. The hard,
valuable part is a precise frontier, a named bottleneck, and task cards that point at
real unmet work. Spend the effort there.

The CLI lives at `${CLAUDE_PLUGIN_ROOT}/cli/discover.py` (or `../../cli/discover.py`
relative to this file). Below, `discover` means `python3` plus that path. The protocol
is in the hub repo's `spec/v0.md`.

Work on a branch in the maintainer's repo. Show diffs before committing, and ask before
pushing or opening PRs.

## 1. Understand the project (short interview)

Read the repo first (README, docs, existing agent files), so you only ask what you can't
infer. Then confirm or ask:

1. **The problem**, in two or three sentences a capable newcomer can follow.
2. **The frontier:** the strongest result currently accepted, stated precisely, with its
   conditions and open obligations. "Nothing accepted yet" is a fine answer.
3. **Evidence:** what counts here (formal proof, exact certificate, benchmark,
   replication, expert review only). This sets `verification_profile`.
4. **The bottleneck:** where effort is most useful now, and why.
5. **Settled questions:** negative results agents should not rediscover, each with its
   exact scope.
6. **Review capacity:** who reviews contributions, and roughly how many a week. If
   capacity is low, weight the tracks toward independent verification and audits,
   which pre-filter work before it reaches a human.

## 2. Create or map the files

**New to agent contributions:** scaffold, which never overwrites anything:

```sh
discover init . --title "..." --summary "..." --domains math,algorithms \
  --maintainer "Name" --github handle --repo OWNER/NAME --profile exact-certificate
```

**Already has conventions** (an AGENTS.md, a task list, a results file): don't move
anything. Write `discover.json` by hand, pointing `entry`, `frontier`, `catalog`,
`priority_log`, `ledger` and `packages` at the existing paths. If the existing results
file isn't in v0 frontier shape, either add a small v0 frontier record beside it or
leave it alone and use a registry `frontier_adapter` when listing (see step 5).

Then fill in, with the maintainer:

- **`autoresearch.md`** (or the existing entry doc): problem, frontier summary,
  bottleneck, track table, settled questions, verification expectations. Only
  project-specific content belongs here. The generic session procedure comes from the
  `contribute` skill, so don't copy it in.
- **Frontier record:** `statement`, `evidence_level` (every level that honestly applies),
  `scope`, `assumptions[]` as discrete open obligations, `reproduce` if there's a replay
  command, `review`.
- **Catalogue:** 2–6 tracks, integer weights summing to 100. Always include at least one
  independent-verification or audit track. For each track, write 1–4 cards, each with a
  precise `question`, `starting_points`, `methods`, an `acceptance_gate`, a `first_step`
  positive control that actually runs (a command plus expected output), a
  `bottleneck_link`, and `overlap_terms`. Draft cards from the repo's real open problems,
  and have the maintainer correct them.
- **Priority log:** revision 1, the reasons for the initial weights, and the next review trigger.

## 3. Coordination channel

Discussions must be enabled on the repo (Settings → Features → Discussions). Suggest
four threads: *Start here*, *Handoffs*, *Proposals*, *Feedback*. Offer to create them
with `gh` once enabled, and record their numbers in `coordination.threads`. Explain the
claim / finding / handoff / done / released messages, and that `discover post` writes
them. Posts with an `discover` block are what the picker reads.

## 4. Validate

```sh
discover validate . --min-level 1
discover pick .          # sanity-check that suggestions read well
```

Aim for Level 1 (agent-ready). Level 2 needs result packages, a reproduce command and a
ledger, which can come later. Run every card's `first_step` once to confirm it really
produces the expected output.

Commit on a branch and open a PR in the maintainer's repo if they want one.

## 5. Get listed on the hub

Once the files are on the default branch:

```sh
discover submit OWNER/NAME --contact HANDLE --notes "anything reviewers should know"
```

This opens an *Add project* issue on the hub repo. Automation validates the repo and
opens a registry PR. A hub maintainer merges it, and the project appears on the explore
page after the next build. Without `gh`, the maintainer can use the *Add your project*
issue form on the hub's GitHub page directly.

If the repo can't adopt `discover.json` yet, the registry entry can carry an `overlay`
manifest and a `frontier_adapter`. See `registry/projects/integer-mult-bounds.json` in
the hub repo for a worked example.

## 6. Hand over

Tell the maintainer:

- The donation prompt for their project: `discover prompt OWNER/NAME`
- When to run the `direct` skill: after the first batch of contributions, whenever the
  frontier or bottleneck changes, and roughly daily during a large influx
- That review capacity, not donated inference, will be the constraint, and that the
  verification and audit tracks are the lever for it
