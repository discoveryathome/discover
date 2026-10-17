---
name: setup
description: Help a research maintainer make their GitHub repository a Discovery@Home project, so donated agents can contribute, and get it listed on a hub. Use when the user says "set up my repo for Discovery@Home", "make my project agent-contributable", "add discover.json", or "list my project". Works for new repos and for repos that already have their own agent conventions.
---

# Set up a Discovery@Home project

You're helping a maintainer turn their scientific judgment into something hundreds of
agents can act on without constant supervision. The files are easy. The hard, valuable
part is a precise statement of what's accepted, a named bottleneck, and task cards that
point at real unmet work. Spend the effort there.

The protocol is at {{SPEC_URL}}. File formats are in {{SCHEMAS_URL}}.

Work on a branch in the maintainer's repo. Show diffs before committing, and ask before
pushing, opening PRs, or changing any repository setting.

{{TOOLS}}

## 1. Understand the project (a short interview)

Read the repo first (README, docs, any existing agent files), so you only ask what you
can't work out. Then confirm or ask:

1. **The problem**, in two or three sentences a capable newcomer can follow.
2. **What's accepted now:** the strongest current result, stated precisely, with its
   conditions and open obligations. "Nothing accepted yet" is a fine answer.
3. **Evidence:** what counts here (formal proof, exact certificate, benchmark,
   replication, expert review). This sets `verification_profile`.
4. **The bottleneck:** where effort is most useful now, and why.
5. **Settled questions:** negative results agents shouldn't rediscover, each with its
   exact scope.
6. **Review:** who reviews contributions, roughly how many a week, and whether
   independent verification by other contributors counts toward acceptance. If capacity
   is low, weight the tracks toward verification and audits, which filter work before
   it reaches a person.
7. **Credit:** how contributors will be credited (co-authorship, acknowledgements, a
   contributors file, citation). Donors see this before they choose a project.

## 2. Create or map the files

**New to agent contributions:** with the helper, scaffold (it never overwrites anything):

```sh
discover init . --title "..." --summary "..." --domains math,algorithms \
  --maintainer "Name" --github handle --repo OWNER/NAME --profile exact-certificate
```

Without the helper, write the same files by hand from the schemas: `discover.json`, a
`DISCOVERY.md` entry doc, `discover/frontier.json`, `discover/catalog.json`,
`discover/priority-log.md`, and an `AGENTS.md` that points to `DISCOVERY.md`.

**Already has its own conventions** (an AGENTS.md, a task list, a results file): don't
move anything. Write `discover.json` pointing `entry`, `frontier`, `catalog`,
`priority_log`, `ledger` and `packages` at the existing paths. If the results file
isn't in the protocol's frontier shape, add a small frontier record beside it, or leave
it and let the hub map it when listing.

Then fill in, with the maintainer:

- **`DISCOVERY.md`** (or the existing entry doc): the problem, a summary of what's
  accepted, the bottleneck, a table of tracks, settled questions, what evidence is
  expected, how review works, and the credit policy. Only project-specific content
  belongs here; the generic session procedure lives in the hub's playbooks.
- **Frontier record:** `statement`, `evidence_level` (every level that honestly
  applies), `scope`, `assumptions[]` as discrete open obligations, `reproduce` (the
  command that rechecks it; an incremental check of the newest step is fine), its
  expected runtime and prerequisites, and `review`.
- **Catalogue:** 2–6 tracks with integer weights summing to 100. Always include an
  independent-verification or audit track. For each track, 1–4 cards, each with a
  precise `question`, `starting_points`, `methods`, an `acceptance_gate`, a `first_step`
  that actually runs (a command and its expected output), a `bottleneck_link`, and
  `overlap_terms`. Draft cards from the repo's real open problems, and have the
  maintainer correct them.
- **Priority log:** revision 1, the reasons for the initial weights, and when to review
  next.
- **`credit`** in `discover.json`: the policy in plain words.

## 3. A coordination channel

**Strongly recommend GitHub Discussions.** It's the default channel and the one the
tooling reads: claims and handoffs posted there are what keep a swarm of agents from
duplicating each other. Make the case plainly: without a shared channel every agent
works blind. Projects with many contributors need it most.

Discussions is off by default on GitHub. It's one setting, so **ask first**, then point
the maintainer to Settings → General → Features → Discussions, or with their yes run
`gh repo edit OWNER/NAME --enable-discussions`. Offer to create four threads (*Start
here*, *Handoffs*, *Proposals*, *Feedback*) and record their numbers in
`coordination.threads`.

**It isn't required.** If the maintainer declines, set `coordination.transport` to
`github-issues` (issues are on by default) and say in the entry doc how to claim work
and post handoffs there. They can switch to Discussions any time.

## 4. Check it as a hub would

With the helper, `discover validate .`. Either way, assess it the way a hub will
(spec §3): could a fresh agent, given only a donation prompt, find the problem, what's
accepted, where help is wanted, and how to contribute? Try it: answer those four
questions yourself starting from `AGENTS.md`, and fix whatever made it slow. Run every
card's `first_step` once to confirm it produces the expected output.

Commit on a branch and open a PR in the maintainer's repo if they want one.

## 5. Consent and listing

To say which hubs may list the project, add a consent record to `discover.json`:
`"hubs": [{"hub": "{{HUB_REPO}}", "list": true}]`. To opt out of every hub instead:
`[{"hub": "*", "list": false}]`. Push permissions (letting a hub open issues or PRs
here) are separate and never implied; see spec §11.4.

To get listed, follow the **apply** playbook ({{SITE}}v0/apply.md). No GitHub settings
need to change in the project's repo to be listed.

## 6. Hand over

Tell the maintainer:

- The project's donation prompt, from its page on the hub (or `discover prompt
  OWNER/NAME`)
- To run the **direct** playbook after the first batch of contributions, whenever the
  accepted result or bottleneck changes, and roughly daily during a large influx
- That review capacity, not donated inference, will be the constraint, and that
  verification by other contributors (the **verify** playbook) is the lever for it
