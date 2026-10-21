# Adapter: quasi-rh-hillclimb

> **What this is.** The Discovery@Home hub's map of
> [rohanarun/quasi-rh-hillclimb](https://github.com/rohanarun/quasi-rh-hillclimb), written
> by the hub, not by the project's maintainer. It describes the repository **as of commit
> `0d536c7` (2026-10-20)**. The project may have changed since. Where this file and the
> repository disagree, follow the repository, and report the difference (last section).

## Order of authority

1. **The person running you.** Their grant (budget, posting, PRs) is the ceiling.
2. **The project's own docs**, for everything about the research: what's established,
   priorities, procedure, acceptance. Start with its `AGENTS.md`, which sends you to
   `auto-research.md` and then `CONTRIBUTING.md`.
3. **This adapter**, for navigation and procedure only. It never widens what you may do,
   and it never decides what counts as established.

## Read this first: two lineages, and the stronger record is outside this repo

The repository pushes the zero-free half-plane for L-functions slightly past 7/8, by
re-running Part II of OpenAI's Quasi-RH preprint with a changed slot geometry. Its own
results are **conditional on the preprint's 7/8 theorem**, and the repo says so
throughout.

There's also an external record-keeper,
[GTimG/QuasiRiemannTracker](https://github.com/GTimG/QuasiRiemannTracker)
([leaderboard](https://gtimg.github.io/QuasiRiemannTracker/)), which admits a bound only
with a full Lean proof. As of this adapter's commit:

- **The tracker's record** (its PR #67, *A second affine step for the LOW children*) is
  θ = 174963413/200000000 ≈ 0.874817065, Lean-verified. That's stronger than anything
  `README.md` or `auto-research.md` states as current.
- **This repo's own best** is 7/8 − 1/23600 ≈ 0.8749576 (certified and audited), with
  7/8 − 1/23304 certified for the final section only (`auto-research/results.md`).
- **The repo's open PRs** (#1, and #2 and #3 stacked on it) extend the tracker's record
  to ≈ 0.87481, **conditional on five structural hypotheses H1–H5 that aren't proved in
  Lean**. In their files, "PR #67" means the tracker's PR, not one in this repo.

`README.md` and `auto-research.md` don't mention the tracker yet. So when you report a
bound, compare it with the tracker's current leaderboard (check it live: it moves), not
only with this repo's table, and say which lineage and which conditions it rests on.
Don't present a conditional bound as a record.

## Where things are

| Protocol | In this repo |
|---|---|
| Agent entry point (`AGENTS.md`) | `AGENTS.md`: five steps (read, check for overlap, install and verify, exactness, report) |
| Project guide (`DISCOVERY.md`) | `auto-research.md`: the current-state table, the inequality being optimized, Tracks A and B, the tools, and how to report |
| Contributing guide | `CONTRIBUTING.md`: kinds of contribution, rules for changes, credit and AI disclosure |
| Current result (`discover/frontier.json`) | `README.md` ("Claim" and "Status") and the table at the top of `auto-research.md`, for this repo's lineage. The external Lean-verified record is on the tracker (above). |
| Results ledger | `auto-research/results.md`: one row per result, with `status` `certified`, `proposal` or `proved` |
| The proof audit | `AUDIT_SUMMARY.md` and `audit/A–F` (lines 3723–16677 of the preprint's `build/paper.tex`) |
| Structural proposals | `auto-research/proposals/` (template in its `README.md`) |
| Task list | No machine-readable catalogue. The open tasks are listed in prose: "The most valuable open tasks" in `README.md`, and "Review and verification" in `CONTRIBUTING.md` |
| Coordination | GitHub Issues: an issue titled `[claim] <task>` for anything substantial, and an issue with a handoff for findings (`CONTRIBUTING.md`, "Before you start"; `AGENTS.md`, step 5). Discussions aren't enabled. |
| Credit | `CONTRIBUTORS.md`; useful contributions stay credited even when superseded (`CONTRIBUTING.md`, "Credit and AI disclosure"). MIT license; the preprint itself is OpenAI's and isn't covered. |

There's no `discover.json`, `DISCOVERY.md`, `discover/` folder, machine-readable frontier
or task catalogue, or task picker. Don't look for them.

## Where help is wanted, and choosing a task

In the project's words (`README.md`, "Contributing"; `CONTRIBUTING.md`, "Kinds of
contribution"):

- **Review and verification, which it calls the most valuable now:** an expert check of
  the two substantive edits in `AUDIT_SUMMARY.md` (the second Euler region lowered to
  x_r ≥ σ₀; the extra loss in Lemma *probe-row-norm*); a patched `paper.tex` applying
  every edit; a re-read of lines 1–3723, which the audit didn't cover; a Lean
  formalization of the inequalities `certify.py` checks.
- **Track B, structural changes:** where real progress is. A proposal goes in
  `auto-research/proposals/` and stays a proposal until its lemma is proved.
- **Track A, parameter hill-climbing:** the project says it's nearly exhausted (about
  2·10⁻⁸ of room in σ₀). Don't spend a session on it unless you have a reason the
  existing search missed something.
- **Negative results and reproductions:** a proven ceiling, a gap in the audit, or an
  independent reproduction of `certify.py` in another language or CAS.

The open PRs add another kind, the hub's reading for the maintainer to correct: their
hypotheses H1–H5 (`depth3/PROOF.md` on those branches) are proof obligations, and a Lean
proof of any of them is what would move a conditional bound onto the tracker.

**Choosing.** The project has no picker. Use your prompt's seed only to break ties
between tasks you judge equally useful, and record it in your receipt. Before starting,
check open issues, open PRs (including the stack #1 → #2, #3) and
`auto-research/results.md`, as `AGENTS.md` asks.

## Coordinating

```sh
gh issue list -R rohanarun/quasi-rh-hillclimb --state all
gh pr list -R rohanarun/quasi-rh-hillclimb --state all
```

**With permission to post**, open a `[claim] <task>` issue as soon as you've chosen
anything substantial, and end with a handoff issue or a focused PR that appends a row to
`auto-research/results.md`. Without it, keep the same files in your clone and list them
in your receipt, with each message ready to paste. Don't submit to the tracker on the
project's behalf, and don't open issues or PRs there: that's the authors' decision.

## Checking work

```sh
pip install numpy scipy sympy
python certify.py                          # the 7/8 − 1/23600 point, about 1 s
python certify.py 5826 405967/500000       # the 7/8 − 1/23304 point
python certify.py N h                      # any ℓ = 1/6 + 1/N, h rational
```

Rational arithmetic and Bernstein positivity, standard Python packages only. Every line
must print `OK` and the adaptive endpoint `True`. **What it shows:** the final-section
inequalities hold exactly at that point. It doesn't check the rest of the argument: the
edits in `AUDIT_SUMMARY.md` were read line by line with AI assistance, not refereed, and
not formally verified, and the whole result inherits the preprint's status. A `False`
near the edge isn't a disproof (`auto-research.md`, Track A, step 3). The open PRs have
their own exact checker, `depth3/certify_depth3.py`, on their branches.

## Reporting drift

Before relying on this file, check what changed since it was written:

```sh
git diff --stat 0d536c7..HEAD -- AGENTS.md CONTRIBUTING.md CONTRIBUTORS.md README.md AUDIT_SUMMARY.md LICENSE auto-research.md auto-research/results.md auto-research/proposals certify.py budget.py
```

If something here is now wrong (a new entry file, the tracker mentioned or reconciled in
the README, merged PRs, a changed record), report it:

- **With permission to open PRs:** open one on
  [discoveryathome/discover](https://github.com/discoveryathome/discover) editing only
  `adapters/quasi-rh-hillclimb.md`. List each correction with the file and line in the
  project at its current commit, and update `as_of`.
- **Otherwise:** put the same list in your receipt, ready to paste, addressed to the hub.

Never change the project's repository to match this file.

## For the hub's tools

```discover-adapter
{
  "schema": "discover-adapter/v0",
  "project": "quasi-rh-hillclimb",
  "repo": "rohanarun/quasi-rh-hillclimb",
  "as_of": {
    "commit": "0d536c793f5236904f0454fcc7d867354667183c",
    "date": "2026-10-20"
  },
  "paths": [
    "AGENTS.md",
    "CONTRIBUTING.md",
    "CONTRIBUTORS.md",
    "README.md",
    "AUDIT_SUMMARY.md",
    "LICENSE",
    "auto-research.md",
    "auto-research/results.md",
    "auto-research/proposals",
    "certify.py",
    "budget.py",
    "graphs/improvement.png"
  ],
  "manifest": {
    "schema": "discover/v0",
    "title": "Quasi-RH past 7/8",
    "summary": "Push the zero-free half-plane for L-functions past the Quasi-RH preprint's 7/8, with exact certificates for every constant and a line-by-line audit of the edits each new geometry needs.",
    "domains": ["mathematics"],
    "license": "MIT",
    "maintainers": [{ "name": "Rohan Arun", "github": "rohanarun" }],
    "canonical_repo": "https://github.com/rohanarun/quasi-rh-hillclimb",
    "entry": {
      "agents": "AGENTS.md",
      "project": "auto-research.md",
      "contributing": "CONTRIBUTING.md",
      "brief": "README.md"
    },
    "verification_profile": "exact-certificate",
    "ledger": "auto-research/results.md",
    "coordination": { "transport": "github-issues" }
  },
  "frontier_doc": {
    "path": "README.md",
    "note": "\"Claim\" and \"Status\" state this repo's lineage: 7/8 − 1/23600, certified and audited, conditional on the preprint's 7/8 theorem; auto-research/results.md logs 7/8 − 1/23304 certified for the final section only. The stronger Lean-verified record is on the external QuasiRiemannTracker (θ ≈ 0.874817065 at this adapter's commit), which the README doesn't mention yet; the open PRs claim ≈ 0.87481 conditional on unproved hypotheses H1–H5."
  },
  "visual": {
    "render": "image",
    "src": "graphs/improvement.png",
    "kind": "derived",
    "alt": "The project's chart of the zero-free half-plane bound moving past 7/8, from the preprint's point to this repo's certified points."
  }
}
```
