# Adapter tests on six third-party repositories (2026-10-17)

Backs the frontier's adapter claim (`discover/frontier.json`). Reconstructed on 2026-10-19
from the session that ran the tests; the adapters and probe transcripts weren't committed,
so this record gives what's needed to rerun them, and says where evidence is thin.

**Self-run** (spec §12.4): the tests, the fixes and this record are all by agents working
for the hub's maintainer.

## Method

- **Tooling under test:** the `adapt` playbook and `discover adapter-check` at `e549cb8`.
- **Adapters:** one fresh agent per repository (Claude, the session's model, not recorded
  per run), given only the adapt prompt in local mode, read-only toward the project.
  Nothing was posted to the projects or listed on the hub.
- **Probes:** two fresh Claude Sonnet agents per repository, read-only on a local clone:
  one read the repository only, the other read the adapter first. Both answered the
  orientation questions (the problem; the strongest accepted result; where help is
  useful; how to claim, submit and check), each with a confidence level. The
  with-adapter probe also flagged adapter errors.
- **Rerun:** clone the repository at the commit below, run the adapt playbook in local
  mode (https://discoveryathome.org/v0/adapt.md), then run both probes with the same questions.

## Results

| Repository | Commit | `adapter-check` | Probe, with vs. without the adapter | Defects found |
|---|---|---|---|---|
| c0ldzy17/three-sum-lean | `2b63965` | ok (no frontier record) | Better: accepted result clearer (medium → high); where to help low → medium | Restated figures that go stale |
| rohanarun/Super-1 | `e791709` | ok (no frontier record) | About the same; the bare repo was already clear | Self-contradiction about where files live |
| shea256/fourier-transform-below-nlogn | `9749945` | ok | Round 1 **worse** on where to help (medium → low-medium). Round 2 after fixes: matched or beat the bare repo | Called the handoff file "not an invitation"; missed the repo's conflicting baselines |
| eumemic/exoplanets | `f1d17f0` | ok | Round 1 **worse** on where to help (low-medium → low). Round 2 after fixes: matched or beat the bare repo | Missed the README's conflicting counts |
| 1337isnot1337/erdos-99 | `d008926` | ok | Same confidence; slightly more precise on where help is needed | Stale counts; no pointer to where the result is stated |
| alejandrozu/platonic-packing | `747ceb0` | ok | **Worse** on where to help (low-medium → low): the seeded draw picked cases with no relation to usefulness | Restated counts; missed a submission file |

## Fixes that came out of it

- `bf92715`: adapters point to gaps in the project's own words, restate no fast-changing
  facts, always point to where the current result is stated, use a seeded draw only
  when the project invites work on any item, and get a self-consistency pass. The tool
  gained `frontier_doc` and `frontier_adapter.select`, and `adapter-check` fails an
  adapter with neither a frontier nor a `frontier_doc`.
- `222da63`: adapters note contradictions within the repository and which source is
  authoritative (from the round-2 probes).

## What this shows, and what it doesn't

- **Shown:** on all six repositories the playbook produced an adapter that
  `adapter-check` accepts, and the two adapters rewritten under the fixed playbook
  (fourier, exoplanets) matched or beat the bare repository on every question.
- **Not shown:**
  - that adapters never leave a donor less oriented. Three first-round adapters did,
    on where to help, and platonic-packing wasn't rerun after the fixes;
  - the other four adapters weren't regenerated under the fixed playbook;
  - round 2 compared against the round-1 bare-repo probes rather than fresh ones;
  - each probe ran once, with no repeats.
- **Planted error** (separate test, on a listed project): `1620daa` put a wrong
  handoffs thread into the integer-mult-bounds adapter. A donated session found it and
  opened hub PR #22, merged as `292d6d4`. `discover hub-check` didn't catch it: it checks
  an adapter's structure, not what its references say.

Rerunning the four unrerun adapters under the current playbook, with fresh bare-repo
probes and at least two runs each, is open work on the `assessment-tooling` track.
