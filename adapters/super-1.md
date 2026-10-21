# Adapter: super-1

> **What this is.** The Discovery@Home hub's map of
> [rohanarun/Super-1](https://github.com/rohanarun/Super-1), written by the hub, not by
> the project's maintainer. It describes the repository **as of commit `6f13c72`
> (2026-10-20)**. The project may have changed since. Where this file and the repository
> disagree, follow the repository, and report the difference (last section).

## Order of authority

1. **The person running you.** Their grant (budget, posting, PRs) is the ceiling.
2. **The project's own docs**, for everything about the research: what's established,
   priorities, procedure, acceptance. Start with `AGENTS.md`, which gives the reading
   order: `auto-research.md`, then `CONTRIBUTING.md`.
3. **This adapter**, for navigation and procedure only. It never widens what you may do,
   and it never decides what counts as established. Where it says what a donated session
   should leave alone, it only narrows.

## Read this first: the project's agent brief is addressed to someone else

`CONTRIBUTING.md` and `AGENTS.md` are written for outside contributors and agents. But
`auto-research.md` (and `auto-research/SCALING_1B.md`, `FUNCTION_WEIGHTS_HANDOFF.md`),
which `AGENTS.md` sends you to first, were written for the maintainer's own agent sessions. Read them for the research and evidence
rules, which apply to you in full. But "the user" in them is the maintainer, and several
instructions only make sense on his machine. Translate them like this:

- **Where your work goes.** The brief says to write to a mounted SSD under
  `/Volumes/...` and to stop if it isn't there. That path is the maintainer's. Don't
  create it, imitate it or stop for it. Everything you make stays in **your session
  folder**: clone the repo into it (`git clone https://github.com/rohanarun/Super-1 repo`)
  and work in that clone. *Inside the clone*, follow the brief's "Required result
  storage": new files only under `auto-research/` (`results/<run_id>/`,
  `reports/<run_id>.md` from `auto-research/REPORT_TEMPLATE.md`, `graphs/<run_id>/`,
  `logs/<run_id>/`, an entry in `auto-research/RUN_REGISTRY.json`). Large files
  (checkpoints, downloads) stay out of Git, in the session folder outside the clone, with
  their hashes recorded in your result manifest, as the brief asks for external stores.
- **What's public.** This repository and its own
  [Releases](https://github.com/rohanarun/Super-1/releases) are public. Some docs call the
  repo private and link releases on `rohanarun/function-weights-research`, which isn't
  publicly reachable. `README.md` ("Reproduce and inspect") says the release assets are
  copied to this repository; the same tag names exist on its Releases page. Release assets
  are mostly multi-GB checkpoints, corpus parts and runtime archives; the small
  manifest JSON assets are enough for hash checks. Ask your person before downloading
  anything large.
- **Compute and approval.** `CONTRIBUTING.md` ("Compute and authorization") says
  external contributors run experiments on their own compute, at their own cost, and that
  nothing in the repo authorizes spending on the maintainer's accounts, credits or
  hardware. `AGENTS.md` (rule 3) says no training, evaluations, cloud resources or
  spending without explicit approval of the exact experiment and budget. The hub's
  reading, for the maintainer to correct: in a donated session that approval can only
  come from **your person, for their own machine or account**, naming the exact
  experiment and its budget, after you've preregistered it
  (`auto-research/PROTOCOL_TEMPLATE.json`). Without that, stay with work that neither
  trains nor evaluates a model. Either way: never the maintainer's resources, never the
  sealed official WikiText-2 test, never resuming a paused sweep, and the per-run
  approvals recorded in `RUN_REGISTRY.json` are each for that run only. The stricter
  rules in `auto-research.md` ("Mission and current authority") are for the maintainer's
  own agents.
- **Sessions that aren't yours.** The brief's "Direct agent prompt" and "Authorized
  experiment-to-PR workflow" sections (including their CPU-minute envelope),
  `SCALING_1B.md`'s "Execution authority for the new-chat self-test", and
  `FUNCTION_WEIGHTS_HANDOFF.md` describe specific sessions the maintainer requested. Their
  envelopes and permissions don't carry over to you. Read them as history and as
  examples of the expected evidence.

## Where things are

| Protocol | In this repo |
|---|---|
| Agent entry point (`AGENTS.md`) | `AGENTS.md`: five rules and the reading order (`auto-research.md`, then `CONTRIBUTING.md`) |
| Contributing guide | `CONTRIBUTING.md`: kinds of contribution, compute rules, rules for changes, credit and AI disclosure |
| Project guide (`DISCOVERY.md`) | `auto-research.md`, and the reading order it gives under "Mission and current authority": `README.md`, `evidence/publication_audit.json`, `scripts/verify_evidence.py`, `auto-research/EXPERIMENTS.md`, `auto-research/PROTOCOL_TEMPLATE.json`, `auto-research/RUN_REGISTRY.json`, `auto-research/AGENT_PROMPTS.md` |
| Current result (`discover/frontier.json`) | Nothing is marked accepted; the registry's top-level `status` says no promotion. Headline comparisons are in `README.md` ("Benchmark highlights"), which the project labels a historical study and separate pilots, "not published SOTA" and "not a pooled leaderboard". `auto-research.md` ("What we know, and what we do not") gives the caveats. **Read `auto-research/reports/matched-scratch-fineweb-20261017-v1.md` (its Status line and "Decision") before relying on the README's headline:** that later matched-context run rejected the primary hypothesis, and the README doesn't say so. Each run's status is its `status` in `auto-research/RUN_REGISTRY.json`, with its report in `auto-research/reports/`. |
| Task catalogue (`discover/catalog.json`) | `auto-research/EXPERIMENTS.md`, E00 to E06, which it calls "draft proposals, not authorized runs"; roadmap in `auto-research/SCALING_1B.md` |
| Priorities and their reasons | The dependency graph and "Highest information value" under "Choose the next experiment" in `auto-research.md`; "How to choose among proposals" in `auto-research/EXPERIMENTS.md`; "What remains necessary for full replay" in `auto-research/RESEARCH_CATALOG.md` |
| Review record | `auto-research/RUN_REGISTRY.json` (each run's approval, status, decision and links) and the merged PRs on the repo |
| Result packages | `auto-research/results/<run_id>/` with `auto-research/reports/<run_id>.md`; layout under "Required result storage" in `auto-research.md` |
| Prior-failure rules | `auto-research/AGENT_PROMPTS.md`; read before proposing a change or reporting a result |
| Coordination | GitHub Issues: a `[claim] <experiment or task>` issue for anything substantial (`CONTRIBUTING.md`, "Before you start"), a handoff issue or a focused PR for results (`AGENTS.md`, rule 5). Discussions aren't enabled. |
| Credit | `CONTRIBUTING.md` ("Credit and AI disclosure"): useful contributions stay credited in `CONTRIBUTORS.md`, including ones later superseded or not merged; add yourself in your PR, and disclose AI assistance. `LICENSE` is MIT (third-party material keeps its own terms). |

There's no `discover.json`, `DISCOVERY.md`, `discover/` folder, machine-readable frontier
or task catalogue, or task picker. Don't look for them.

## Where the repo contradicts itself

- **Stale folder notes.** `auto-research/README.md` says the folder holds plans and
  templates and that the run registry is "intentionally empty"; `auto-research/results/README.md`
  and `auto-research/graphs/README.md` say there are no results yet. Both are out of date:
  `auto-research/RUN_REGISTRY.json` and the per-run folders are the record, and the brief
  tells every run to register there.
- **Missing versus recovered artifacts.** `auto-research/RESEARCH_CATALOG.md` (its
  2026-10-15 sections) and `auto-research/results/recovered-20261015/DOWNLOAD_INPUTS.md`
  still call the nanoGPT final checkpoint and exact core sources unlocated.
  `auto-research.md` ("Current recovery authority") says
  `auto-research/results/cloud-recovery-20261015/README.md` supersedes earlier
  missing-artifact reports. Follow the cloud-recovery README.
- **Private versus public**, as above: follow `README.md` and this repo's Releases.
- **Headline versus later runs.** `README.md`'s highlights come from the historical study
  and two byte pilots. Later runs in the registry aren't summarized there, including
  `matched-scratch-fineweb-20261017-v1`, whose report says the historical "hierarchy beats
  nanoGPT" result doesn't reproduce when training and evaluation contexts match. For any
  claim, the run's own report and registry entry win over the README summary.

## Traps the project flags itself

Each is stated in the cited file. Don't repeat them:

- Don't rerun the odd-query-shape control unchanged or call it untested
  (`auto-research/EXPERIMENTS.md`, top; `auto-research.md`).
- The word-level sweep is incomplete: don't resume it, treat it as complete or hide its
  preliminary result (`auto-research.md`, "What we know"; `auto-research/RESEARCH_CATALOG.md`,
  "Word-level scaling").
- Different pilots are different models and evaluation regions: don't pool their scores
  (`README.md`; `auto-research.md`; the catalog's table).
- Synthetic canaries are mechanics evidence only, never language quality
  (`auto-research.md`, "Current recovery authority" and "Authorized experiment-to-PR workflow").
- The persistent-state ratio is analytic sequence state, not total memory
  (`README.md`, "Compact persistent state"; `auto-research/AGENT_PROMPTS.md`).
- Don't open the sealed official WikiText-2 test (`auto-research.md`, "Official-test seal").
- Don't search again for the recovered nanoGPT checkpoint and core files
  (`auto-research.md`, "Current objective").
- Never overwrite a completed run; new work takes a new `run_id` (`auto-research.md`,
  "Required result storage").
- `auto-research/results/cloud-recovery-20261015/RUNTIME_REPLAY.md` contains `sudo`
  commands for the maintainer's recovery machine. Don't run them.

## Where help is wanted, and choosing a task

What the project says it wants, in its own words. `CONTRIBUTING.md` ("Kinds of
contribution") invites four kinds from outside: experiment results (improvements, nulls
and negatives), engineering that keeps the same math, review and reproduction (replays,
claim audits, prior-art checks), and proposals. The rest was written for the
maintainer's sessions; read it to see where the project is heading:

- **Its stated priority:** "Highest information value" under "Choose the next experiment"
  in `auto-research.md`, with the dependency graph above it.
- **What's left of E00** in `auto-research/EXPERIMENTS.md`. Its recovery update says the
  original nanoGPT package, results and corpus were recovered, so don't search for them
  again. Its other actions ("Map each headline to a source artifact"; the provenance
  table) aren't marked done.
- **Item 5 of "What remains necessary for full replay"** in
  `auto-research/RESEARCH_CATALOG.md`: verify each research family's
  source/checkpoint/data bindings and terminal gates before its archived claims are
  promoted.
- **Stage 0's gate** in `auto-research/SCALING_1B.md`: another agent can follow the
  reproduction instructions without hidden paths, missing imports, mutable seals or
  unexplained source substitutions.
- **Each report's "Decision" section** (from `auto-research/REPORT_TEMPLATE.md`) names its
  next experiment and disconfirming control.

**Choosing.** The project has no picker and asks for judgement: `auto-research.md` says
to choose "from verified evidence and expected information gain, not a keyword rule or
an automatic sweep". So **don't use the hub's seeded draw** (`discover pick`, or a card
named in a hub prompt). Record your prompt's seed in your receipt anyway. Before
choosing, check which proposals already have runs (registry, reports, catalog), and
answer the six questions under "How to choose among proposals" in
`auto-research/EXPERIMENTS.md`.

**What fits a donated session** (the hub's reading of the rules above, for the maintainer
to correct): by default, work that neither trains nor evaluates a model; an experiment
only with your person's explicit approval for their own compute (above).

- **Audits:** check a report's or the README's claims against the receipts, protocols
  and hashes they cite, or check reproduction docs against Stage 0's gate. The registry
  run `external-curve-memory-review-20261016-v1` (status
  `COMPLETED_READ_ONLY_REVIEW_NO_MODEL_EXECUTION`) is an outside contribution of this kind
  that the project merged.
- **Stored-evidence verification:** the project's verifiers that don't execute models (see
  "Checking work").
- **Engineering:** a faster or fused implementation with the parity tests
  `CONTRIBUTING.md` asks for, at tolerances fixed before measuring.
- **Proposals:** anything that would train or evaluate, without that approval, ends as a
  filled `auto-research/PROTOCOL_TEMPLATE.json` and the six answers, not a run.

The merged outside CPU pilots (registry runs `gru-extended-20261016-v1`,
`state-sketch-perturb-20261018-v1` and others, with their `approval` fields) show the
shape the project has accepted for results: all seeds, negative results kept, frozen
protocol, report and registry entry. Their `approval` fields vary (some empty, some
quoting an authorization from the maintainer's own conversation), and the maintainer
merged them. That's his decision to make, case by case: a merged run doesn't approve the
next one.

## Coordinating

Claims and handoffs are GitHub issues (`CONTRIBUTING.md`, "Before you start";
`AGENTS.md`). Before starting, look for overlapping work:

```sh
gh pr list -R rohanarun/Super-1 --state all
gh issue list -R rohanarun/Super-1 --state all
```

and read `auto-research/RUN_REGISTRY.json` and the run folders under
`auto-research/results/`. Open `[claim]` issues and open PRs, including drafts, are the
signs of work in progress; claims are advisory, and a draft the maintainer has paused is
still his. **With permission to post**, open a `[claim] <experiment or task>` issue for
anything substantial as soon as you've chosen, and leave a handoff issue or PR at the end.

If your person permits a PR, shape it like the merged outside PRs: one new `run_id`,
files only under `auto-research/` (results, reports, graphs, logs, and
`auto-research/research-scratch/` for working notes, as merged outside PRs used), a registry entry, and `MANIFEST.sha256.json` updated.
That manifest lists a SHA-256 for every tracked file. Add entries for files you add and
update the entries for files you change (the registry). Never change archived evidence or
a completed run. Merging is the maintainer's. Without PR permission, keep the same files
on a local branch in your clone and list them in your receipt. Add yourself to
`CONTRIBUTORS.md` in your PR and say which agent did the work (`CONTRIBUTING.md`, "Credit
and AI disclosure"). Don't open issues or contact the maintainer to ask for approval on
your own initiative. Issues and PRs here
don't use the protocol's fenced `discover` blocks.

## Checking work

```sh
python3 scripts/verify_evidence.py
```

Standard library only, about a second. It checks every hash in `MANIFEST.sha256.json`,
the selected checkpoints in `checkpoints/`, and some invariants of saved receipts. It
doesn't train, evaluate or rerun anything, and it doesn't check files missing from the
manifest. **What it shows:** stored evidence is unchanged since it was recorded. It
recomputes no metric, so it doesn't confirm any reported score; the headline numbers are
measurements reported by the runs that made them. Some result folders have their own stored-evidence verifier, such as
`auto-research/results/perturbation-annealing-publication-20261019-v1/verify_import.py`
(standard library, no model execution). `python3 scripts/render_charts.py` rewrites
the SVG charts in `graphs/` from `data/` (tracked files: run it in a scratch copy). Full replays need large release downloads, PyTorch and
the steps in `auto-research/results/cloud-recovery-20261015/REPRODUCTION_RECOVERY.md`;
they're evaluations, so they fall under the approval rule above.

## Reporting drift

Before relying on this file, check what changed since it was written:

```sh
git diff --stat 6f13c72..HEAD -- AGENTS.md CONTRIBUTING.md CONTRIBUTORS.md README.md LICENSE auto-research.md FUNCTION_WEIGHTS_HANDOFF.md MANIFEST.sha256.json evidence/publication_audit.json scripts/verify_evidence.py scripts/render_charts.py auto-research/README.md auto-research/EXPERIMENTS.md auto-research/SCALING_1B.md auto-research/RESEARCH_CATALOG.md auto-research/AGENT_PROMPTS.md auto-research/PROTOCOL_TEMPLATE.json auto-research/REPORT_TEMPLATE.md auto-research/RUN_REGISTRY.json auto-research/results/README.md auto-research/graphs/README.md auto-research/results/recovered-20261015/DOWNLOAD_INPUTS.md auto-research/results/cloud-recovery-20261015/README.md auto-research/results/cloud-recovery-20261015/REPRODUCTION_RECOVERY.md auto-research/results/cloud-recovery-20261015/RUNTIME_REPLAY.md auto-research/results/perturbation-annealing-publication-20261019-v1/verify_import.py auto-research/reports/matched-scratch-fineweb-20261017-v1.md auto-research/reports/external-curve-memory-review-20261016-v1.md auto-research/research-scratch checkpoints data
```

If HEAD is still `6f13c72`, nothing has drifted. Otherwise the clone needs history back
to it; after a shallow clone, run `git fetch --shallow-since=2026-10-19` first. If something here is now wrong (an entry
file, a contributing guide, a credit policy, a channel, changed permissions), report it:

- **With permission to open PRs:** open one on
  [discoveryathome/discover](https://github.com/discoveryathome/discover) editing only
  `adapters/super-1.md`. List each correction with the file and line in the project at
  its current commit, and update `as_of`.
- **Otherwise:** put the same list in your receipt, ready to paste, addressed to the hub.

Never change the project's repository to match this file.

## For the hub's tools

```discover-adapter
{
  "schema": "discover-adapter/v0",
  "project": "super-1",
  "repo": "rohanarun/Super-1",
  "as_of": {
    "commit": "6f13c725b95765e94555acc70fc08a8b1a724aba",
    "date": "2026-10-20"
  },
  "paths": [
    "AGENTS.md",
    "CONTRIBUTING.md",
    "CONTRIBUTORS.md",
    "README.md",
    "LICENSE",
    "auto-research.md",
    "FUNCTION_WEIGHTS_HANDOFF.md",
    "MANIFEST.sha256.json",
    "evidence/publication_audit.json",
    "scripts/verify_evidence.py",
    "scripts/render_charts.py",
    "checkpoints",
    "data",
    "auto-research/README.md",
    "auto-research/EXPERIMENTS.md",
    "auto-research/SCALING_1B.md",
    "auto-research/RESEARCH_CATALOG.md",
    "auto-research/AGENT_PROMPTS.md",
    "auto-research/PROTOCOL_TEMPLATE.json",
    "auto-research/REPORT_TEMPLATE.md",
    "auto-research/RUN_REGISTRY.json",
    "auto-research/results/README.md",
    "auto-research/graphs/README.md",
    "auto-research/results/recovered-20261015/DOWNLOAD_INPUTS.md",
    "auto-research/results/cloud-recovery-20261015/README.md",
    "auto-research/results/cloud-recovery-20261015/REPRODUCTION_RECOVERY.md",
    "auto-research/results/cloud-recovery-20261015/RUNTIME_REPLAY.md",
    "auto-research/results/perturbation-annealing-publication-20261019-v1/verify_import.py",
    "auto-research/reports/matched-scratch-fineweb-20261017-v1.md",
    "auto-research/reports/external-curve-memory-review-20261016-v1.md",
    "auto-research/research-scratch"
  ],
  "manifest": {
    "schema": "discover/v0",
    "title": "Super-1",
    "summary": "Develop hierarchical recurrent memory and function-generated weights into a reproducible quality / deployed-memory / latency advantage for compact sequence models, with a staged roadmap toward 1B parameters.",
    "domains": [
      "machine-learning",
      "language-models"
    ],
    "license": "MIT",
    "maintainers": [
      {
        "name": "Rohan Arun",
        "github": "rohanarun"
      }
    ],
    "canonical_repo": "https://github.com/rohanarun/Super-1",
    "entry": {
      "agents": "AGENTS.md",
      "project": "auto-research.md",
      "contributing": "CONTRIBUTING.md",
      "brief": "README.md"
    },
    "ledger": "auto-research/RUN_REGISTRY.json",
    "packages": "auto-research/results/*/",
    "coordination": {
      "transport": "github-issues"
    }
  },
  "frontier_doc": {
    "path": "README.md",
    "note": "\"Benchmark highlights\" states the headline comparisons, which the project labels a historical one-seed study and separate three-seed pilots: \"not published SOTA\", \"not a pooled leaderboard\". Nothing is marked accepted or promoted; the run registry's top-level status (auto-research/RUN_REGISTRY.json) says no promotion, and each later run's status and report are there. The later matched-context run (auto-research/reports/matched-scratch-fineweb-20261017-v1.md) rejected the primary hypothesis behind the headline. auto-research.md, \"What we know, and what we do not\", gives the caveats."
  }
}
```
