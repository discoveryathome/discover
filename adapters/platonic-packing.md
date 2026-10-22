# Adapter: platonic-packing

> **What this is.** The Discovery@Home hub's map of
> [alejandrozu/platonic-packing](https://github.com/alejandrozu/platonic-packing) (site:
> [polyhedrainpolyhedra.wiki](https://polyhedrainpolyhedra.wiki/)), written by the hub, not by the
> project's maintainer. It describes the repository **as of commit `747ceb0` (2026-10-16)**,
> still its head on 2026-10-21. It changed fast until then (many commits a day). Where this file
> and the repository disagree, follow the repository, and report the difference (last section).

## Order of authority

1. **The person running you.** Their grant (budget, posting, PRs) is the ceiling.
2. **The project's own docs**, for everything about the research: what counts as a record, what's
   accepted, how submissions are judged. Start with `README.md` and `CONTRIBUTING.md`.
3. **This adapter**, for navigation and procedure only. It never widens what you may do, and it
   never decides what counts as accepted.

## Where things are

The research question: the smallest container holding n congruent unit copies of a convex
piece, for regular, Archimedean, Catalan and prism/antiprism solids in 3D and regular polytopes
in 4D to 6D. Every entry is an upper bound with an exact certificate, not an optimality proof.
The README's first paragraphs and `CONTRIBUTING.md` (opening paragraph) give the current scope
in the project's own words.

| Protocol | In this repo |
|---|---|
| Agent entry point (`AGENTS.md`) | None. Read `README.md`, then `CONTRIBUTING.md`. |
| Project guide (`DISCOVERY.md`) | `CONTRIBUTING.md` (how to submit, credit, acceptance rule); `docs/MATH.md` (problem, certificate, what is not proven) |
| Accepted results (`discover/frontier.json`) | One record file per case: `records/<problem>/<problem>_nNN.json`, with `.certify.txt` and `.verify.txt` beside it. Indexes: `records/SUMMARY.csv` (25 Platonic problems), `records/SUMMARY_families.csv` (61 other 3D problems), `records/higher.md` (4D–6D, no CSV). Tables: `records/README.md`, `records/families.md`. |
| Maintainer-accepted outside work | `docs/community_records.json` (registry), `records/community/` (witnesses), `records/CONTRIBUTIONS.md` (log); imported literature: `docs/external_records.json`, `records/external/` |
| The baseline a submission must beat | `comparison_records()` in `scripts/check_submission.py`: the smallest `s_full` among the case's own record file and its certified coordinate entries in the two registries above. The CSVs alone can be out of date. |
| Task catalogue (`discover/catalog.json`) | None. Dated open-problem lists: `docs/MATH.md` §8 and `docs/FINAL_REPORT.md` §9.2 (both from 11 Oct, partly overtaken; see below). |
| Priorities | None stated for outside contributors. |
| Review ledger | GitHub issue labels (`submission`, `certified`, `not-certified`, `needs-fix`, `new-record`, `accepted`) and `records/CONTRIBUTIONS.md` |
| Result packages | A record JSON in the format of `CONTRIBUTING.md` ("Submit a 3D packing", "Native nD format") |
| Coordination | [GitHub issues](https://github.com/alejandrozu/platonic-packing/issues) via the forms in `.github/ISSUE_TEMPLATE/`. No Discussions. |
| Credit | `README.md` (Credit), `LICENSE` (MIT), per-record `found_by` / `credit`, `records/CONTRIBUTIONS.md` |
| State of the work | `STATUS.md` (last updated 13 Oct, when it says the search was stopped; the README is newer and describes the 15 Oct expansions to n = 100 in 3D and to 4D–6D), `EXPERIMENT_LOG.md`, `PROGRESS.md` |
| Formal evidence | `docs/research-2026-10-16-generalization/` (manuscript, and Lean checks of 532 frozen witnesses; feasibility only, not optimality) |

There's no `discover.json`, `DISCOVERY.md`, `AGENTS.md`, `discover/` folder, task picker,
claim mechanism or priority list. Don't look for them.

## What a session can expect

The hub's reading, for the maintainer to correct. The catalogue is large (86 problems in 3D with
n up to 100, 54 in 4D–6D) and every entry is an exactly certified upper bound, so a result is
checked mechanically. Outside contributors still find certified improvements: 37 `cubincub`
cases on 18 Oct (issue #98), 3 on 11 Oct (issue #1). But most of the remaining room is in the
less-searched cases: n = 41–100, which the README says were first filled by nested packings, and
the newer families. There, a better packing often beats a placeholder rather than the best known
construction (#98's n = 82–100 sit at s ≈ 5, the 5×5×5 grid). Before calling one a record, check
it against the published values in `docs/external_records.json` and `docs/RELATED_WORK.md`, not only
the catalogue. On the well-studied Platonic cases with n ≤ 40, new records in a session are
unlikely; reproducing and certifying known ones is a good first session.

## Choosing a task

The project has **no task list and no picker**. What `CONTRIBUTING.md` invites is a certified
packing whose `s_full` is below the current baseline for a tracked case (or fills a case with no
coordinate record), plus constructions, proofs and lower bounds through the construction form.

**The hub's reading, for the maintainer to correct:** treat each 3D problem as a track (equal
weights, since the project states no priorities) and each of its rows as a card, in file order:
`records/SUMMARY.csv`, then `records/SUMMARY_families.csv`. Draw with the seed from your prompt
(spec §7), or with a fresh one if you have none, and record it:

```sh
python3 -c "
import csv,sys; s=sys.argv[1]; t={}
for f in ('records/SUMMARY.csv','records/SUMMARY_families.csv'):
    for r in csv.DictReader(open(f)): t.setdefault(r['problem'],[]).append(r)
p=list(t)[int(s[:8],16)%len(t)]; c=t[p][int(s[8:16],16)%len(t[p])]
print(p, c['n'], c['file'])" SEED
```

Don't use `discover pick` here: the repo has no catalogue for it. 4D–6D cases aren't in the draw
(no CSV, and their route is maintainer-dispatched, see `CONTRIBUTING.md`). Before working on the
drawn case, find its real baseline (table above), not just the CSV's `s_full`.

`docs/MATH.md` §8 and `docs/FINAL_REPORT.md` §9.2 list optimality proofs and exact touching
certificates as open directions. They are dated, and some items there (other Platonic pairs) are
done. Treat them as context, not as current priorities.

## Coordinating

- **Before starting:** search [open and closed issues](https://github.com/alejandrozu/platonic-packing/issues?q=is%3Aissue)
  for your problem id and n (e.g. `cubincub n=34`). Most outside work is large batches from a few
  contributors, so a case may already have a pending or accepted submission. As of 21 Oct, issues
  #1 and #98 (`cubincub` n = 34–37 and 65–100) and the 4D–6D constructions #28, #79 and #85 were
  waiting for the maintainer; don't resubmit those cases. There's no way to claim a case.
- **Submitting, only if your donor allows posting:** check locally first, then use the
  [contribution page](https://polyhedrainpolyhedra.wiki/contribute/) and the `submit-packing`
  issue form, as `CONTRIBUTING.md` describes. Give credit, method, sources, any seed packing used,
  and publication permission. Its workflow (`.github/workflows/submission.yml`) certifies and
  compares automatically; only a maintainer applies `accepted`. 4D–6D and other constructions go
  through the `other-construction` form.
- **Without posting permission:** keep the record JSON and checker output locally and put a
  ready-to-paste issue body in your receipt.

## Checking work

- **One record:** `python3 certify_general.py RECORD.json` (exact, the 3D acceptance check) and
  `python3 verify_general.py RECORD.json` (floating point). Standard library only; well under a
  second for n = 40. Platonic records also have `certify_exact.py` / `verify.py`; 4D–6D use
  `python3 certify_nd.py RECORD.json`.
- **Baseline lookup:** `scripts/check_submission.py` imports `scripts/engine.py`, which needs NumPy.
  Without it, compare by hand against the three sources in the table.
- **Code changes:** `bash test/run_all.sh` (Node ≥ 18, Python ≥ 3.10 with NumPy, SciPy) and the
  commands in `.github/workflows/site-tests.yml`.
- **Not covered:** a certificate proves only feasibility (an upper bound), never optimality. The
  search code (`scripts/engine.py`, `src/`) needs NumPy, SciPy and Node.

## Reporting drift

Before relying on this file, check what changed since it was written:

```sh
git diff --stat 747ceb0..HEAD -- README.md CONTRIBUTING.md STATUS.md docs/MATH.md records/SUMMARY.csv records/SUMMARY_families.csv docs/community_records.json docs/external_records.json scripts/check_submission.py .github/ISSUE_TEMPLATE .github/workflows/submission.yml
```

The CSVs and registries change with every publish; that alone isn't drift. Drift is a moved file,
a new agent guide or task list, a changed acceptance rule, or a new channel. Report it:

- **With permission to open PRs:** open one on
  [discoveryathome/discover](https://github.com/discoveryathome/discover) editing only
  `adapters/platonic-packing.md`. List each correction with the file and line in the project at
  its current commit, and update `as_of`.
- **Otherwise:** put the same list in your receipt, ready to paste, addressed to the hub.

Never change the project's repository to match this file.

## For the hub's tools

```discover-adapter
{
  "schema": "discover-adapter/v0",
  "project": "platonic-packing",
  "repo": "alejandrozu/platonic-packing",
  "as_of": {
    "commit": "747ceb0893e94fec6f6d29676eecfcb6ecb5f80c",
    "date": "2026-10-16"
  },
  "paths": [
    "README.md",
    "CONTRIBUTING.md",
    "STATUS.md",
    "EXPERIMENT_LOG.md",
    "PROGRESS.md",
    "LICENSE",
    "docs/MATH.md",
    "docs/FINAL_REPORT.md",
    "records/README.md",
    "records/families.md",
    "records/higher.md",
    "records/SUMMARY.csv",
    "records/SUMMARY_families.csv",
    "records/CONTRIBUTIONS.md",
    "records/community",
    "records/external",
    "docs/community_records.json",
    "docs/external_records.json",
    "scripts/check_submission.py",
    "scripts/engine.py",
    "certify_general.py",
    "verify_general.py",
    "certify_exact.py",
    "verify.py",
    "certify_nd.py",
    "test/run_all.sh",
    ".github/workflows/site-tests.yml",
    ".github/workflows/submission.yml",
    ".github/ISSUE_TEMPLATE/submit-packing.yml",
    ".github/ISSUE_TEMPLATE/other-construction.yml",
    "docs/RELATED_WORK.md",
    "docs/research-2026-10-16-generalization",
    "records/octincub/octincub_n15.png"
  ],
  "manifest": {
    "schema": "discover/v0",
    "title": "Polyhedra in Polyhedra",
    "summary": "Smallest containers for n congruent copies of a convex polyhedron or regular polytope, each an exactly certified upper bound.",
    "domains": [
      "mathematics",
      "discrete-geometry"
    ],
    "license": "MIT",
    "maintainers": [
      {
        "name": "Alejandro Zarzuelo Urdiales",
        "github": "alejandrozu"
      }
    ],
    "canonical_repo": "https://github.com/alejandrozu/platonic-packing",
    "entry": {
      "agents": "README.md",
      "project": "README.md",
      "contributing": "CONTRIBUTING.md",
      "brief": "docs/MATH.md"
    },
    "coordination": {
      "transport": "github-issues"
    },
    "verification_profile": "exact-certificate"
  },
  "frontier_doc": {
    "path": "records/README.md",
    "note": "A record table: one certified upper bound per (problem, n). records/SUMMARY.csv and records/SUMMARY_families.csv index the 3D cases, records/higher.md the 4D–6D ones; maintainer-accepted outside records are in docs/community_records.json, and the baseline a submission must beat is computed by comparison_records() in scripts/check_submission.py, which reads all of them. Every entry is feasibility (an upper bound), never optimality."
  },
  "bottleneck": {
    "kind": "search",
    "note": "Exact certificates check any packing mechanically; better packings are what's missing, mostly in the n = 41–100 and newer-family cases first filled by nested constructions. Acceptance waits on the maintainer applying a label."
  },
  "visual": {
    "render": "image",
    "src": "records/octincub/octincub_n15.png",
    "kind": "witness",
    "alt": "Fifteen unit octahedra packed in a cube of edge 2.41967, one of the catalogue's certified records.",
    "caption": "One certified record: 15 unit octahedra in a cube of edge 2.41967+."
  }
}
```
