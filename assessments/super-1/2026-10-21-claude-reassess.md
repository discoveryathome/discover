# Re-assessment: rohanarun/Super-1

Updates [`2026-10-19-claude.md`](2026-10-19-claude.md), at commit `6f13c72` (2026-10-20).
Since the assessed commit `78c47fe`, one commit changed the repository: it added
`AGENTS.md`, `CONTRIBUTING.md` and `CONTRIBUTORS.md` (`git diff --stat 78c47fe..6f13c72`:
three files added, nothing else changed). The adapter was refreshed to the same commit in
the same PR.

Rubric v0. Window 2026-10-07/2026-10-21. Assessor: Claude, in the hub maintainer's
session. No probes were rerun: the change adds entry and contributing docs and touches
no research file, so the grades below were rechecked by reading.

## Grades

| Property | Grade | Since 2026-10-19 |
|---|---|---|
| Orientation | adequate | regraded, unchanged |
| Coordination | weak | regraded, unchanged (live state improved; spread didn't) |
| Verification | adequate | unchanged since `78c47fe` |
| Review | adequate | unchanged since `78c47fe` |
| Steering | adequate | unchanged since `78c47fe` |

### Orientation: adequate (regraded, unchanged)

`AGENTS.md` is now the entry point. It gives a reading order (`auto-research.md`, then
`CONTRIBUTING.md`), five rules, and how to report. `CONTRIBUTING.md` answers question 4
(how to claim, submit and have work checked) for outsiders directly: `[claim]` issues,
the result layout, preregistration, the evidence check, and how to report a problem.
That's a real improvement for a newcomer. Question 2 (the strongest accepted result) is
unchanged: the README's headline still isn't reconciled with the later matched-context
run that rejected its hypothesis, and only the adapter points that out. The grade rests
on the adapter, as before, and stays adequate; strong needs the project's own docs to
answer question 2.

### Coordination: weak (regraded, unchanged)

- **Spread: weak.** `CONTRIBUTING.md` ("Kinds of contribution") describes four kinds of
  work, but there's still no enumerated list of open, donor-sized tasks: E00–E06 in
  `auto-research/EXPERIMENTS.md` remain draft proposals that train or evaluate. Agents
  still choose from prose. Duplicate rate: unknown (one outside contributor in the
  window).
- **Live state: adequate (was weak).** There's now a public channel with a stated
  convention: a `[claim] <experiment or task>` issue for substantial work
  (`CONTRIBUTING.md`, "Before you start"), and a handoff issue or focused PR for results
  (`AGENTS.md`, rule 5). No claim or handoff issues exist yet, so there's no lifecycle to
  observe; telling open from taken work still means reading the registry, reports and
  PRs.

The axis takes the lower half: weak. An enumerated list of open tasks that a donated
session can do (audits, reproductions, parity checks) would lift spread to adequate.

### Verification, Review, Steering

Unchanged since `78c47fe`: no file they rest on changed. Review stays capped at adequate
(fewer than 20 contributions in the window).

## Stage: 0 (Explorable)

- **Consent: by the hub maintainer's report.** The project's maintainer agreed to a
  listing in conversation with the hub maintainer (Mister-Meeseeks), who confirmed it
  for this listing on 2026-10-21. There's still no consent record in the repository
  (`discover.json` or `.github/discover-hubs.json`) and no approval of the registry PR
  by the maintainer, so the hub can't verify it itself (§11.4). The registry records
  the source as the hub maintainer's report. A record in the repo, or the maintainer's
  approval of the PR, would make it checkable.
- **Credit policy: yes.** `CONTRIBUTING.md` ("Credit and AI disclosure"): useful
  contributions stay credited in `CONTRIBUTORS.md`, including ones later superseded or
  not merged; contributors add themselves in their PR and disclose AI assistance. This
  answers [issue #14](https://github.com/rohanarun/Super-1/issues/14), which is still
  open.
- **License: yes.** MIT, unchanged.
- **Grades:** Orientation adequate meets Stage 0.

**Stage 1** is still blocked by Orientation (needs strong) and Coordination (needs
adequate).

## Changes to the adapter in this PR

- Entry point, contributing guide, coordination (`[claim]` issues, handoff issues) and
  credit now point to the project's new files.
- **Compute.** `CONTRIBUTING.md` now says external contributors run experiments on their
  own compute and at their own cost, and `AGENTS.md` asks for explicit approval of the
  exact experiment and budget. The adapter previously put all training and evaluation
  out of a donated session's scope. It now reads the project's rules as: a donated
  session may run an experiment only with its person's explicit approval of the exact
  experiment and budget, on their own machine or account, after preregistering it, and
  otherwise stays with work that neither trains nor evaluates. This is the hub's
  reading, flagged for the maintainer to correct.

## Suggestions (don't affect grades)

- Close or answer issue #14, now that `CONTRIBUTING.md` states the policy.
- A short list of open tasks a donated session can do without training (named audits,
  replays of specific historical results, parity checks) would lift Coordination.
- Reconcile the README's headline with the matched-context run's decision, so the
  project's own docs answer "what's established now".

```discover-assessment
{
  "schema": "discover-assessment/v0",
  "project": "super-1",
  "repo": "rohanarun/Super-1",
  "assessed_commit": "6f13c725b95765e94555acc70fc08a8b1a724aba",
  "assessed_on": "2026-10-21",
  "window": "2026-10-07/2026-10-21",
  "rubric": "v0",
  "assessor": "claude",
  "probe_model": "none rerun; carried from 2026-10-19 (claude-sonnet probes)",
  "mode": "re-assess",
  "previous": "assessments/super-1/2026-10-19-claude.md",
  "self_assessed": false,
  "entry_paths": [
    "AGENTS.md",
    "CONTRIBUTING.md",
    "README.md",
    "auto-research.md",
    "auto-research/README.md",
    "auto-research/EXPERIMENTS.md",
    "auto-research/SCALING_1B.md",
    "auto-research/RESEARCH_CATALOG.md",
    "auto-research/RUN_REGISTRY.json",
    "auto-research/REPORT_TEMPLATE.md",
    "auto-research/PROTOCOL_TEMPLATE.json",
    "auto-research/AGENT_PROMPTS.md",
    "auto-research/reports/matched-scratch-fineweb-20261017-v1.md",
    "scripts/verify_evidence.py",
    "LICENSE"
  ],
  "grades": {
    "orientation": "adequate",
    "coordination": "weak",
    "verification": "adequate",
    "review": "adequate",
    "steering": "adequate"
  },
  "stage": 0,
  "adapter_dependent": ["orientation"],
  "verification_covers": ["computation"]
}
```
