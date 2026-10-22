# Pilot: rohanarun/quasi-rh-hillclimb (light)

Run 2026-10-21 by Claude in the hub maintainer's session (pilot playbook, light mode),
for intake, with the hub maintainer's approval to run the project's code. Frozen commit
`0d536c7`. Two sessions, each a fresh agent (Claude, general-purpose) given only the
donation prompt (`discover prompt rohanarun/quasi-rh-hillclimb --permissions local
--minutes 30`), plus where the checkout was and a Python with `numpy`, `scipy` and
`sympy`. Nothing was posted. The sessions **didn't get the hub's adapter**: the project
wasn't listed yet, so the prompt carried no adapter link.

## Fixed before any session ran

- **The check:** `python certify.py N h` for a final-section certificate; for anything
  else, the session's own exact script, rerun by the runner, and which hypotheses it
  rests on.
- **The strongest baseline:** the QuasiRiemannTracker's Lean-verified record,
  θ = 174963413/200000000 ≈ 0.874817065 (its PR #67). Repo-internal: 7/8 − 1/23600
  (certified and audited) and 7/8 − 1/23304 (final section only). Open PRs #1–#3:
  ≈ 0.87481, conditional on H1–H5.
- **What a better number mustn't break:** conditionality stated (the 7/8 theorem, and
  H1–H5 if used); audit margins recomputed for any point past ℓ = 1/6 + 1/5900; no
  re-certified old point; no floating-point search presented as evidence.

## Sessions

| | s1 | s2 |
|---|---|---|
| Fresh | yes | yes |
| Inherits | none (frozen commit) | s1's commit `54428ee` and its handoff |
| Minutes used (of 30) | about 6 | about 11 |
| Minutes to first checked result | about 6 | about 11 |
| Chose | Track B, direction 1 (a floor-bin witness), by the seed | s1's open Track B handoff |
| Claimed | A floor-bin saving alone buys nothing in the frozen architecture; with ideal row counts the ceiling is 84031/96156 ≈ 0.873903, and with every row count ideal it reproduces the README's 167/192, with an exact piecewise formula for σ₀(s) | A uniform adaptive row-count saving of u₂ ∈ [0.0068579, 0.0068589] (exact bracket) reaches s1's ceiling; the floor bin joins near u ≈ 0.00618 (floating point) |
| Runner's check | Reran `floorbin.py` (exact LPs, its own assertions pass, 167/192 reproduced) and `floorbin_check.py` (independent `linprog`, agrees to 6 decimals) | Reran `rowcount.py`: the exact bracket, the Bernstein certificate, and the binding rows all reproduce |
| Outcome | no-progress (a sound negative pricing result, not a frontier move) | no-progress (an exact threshold, building on s1) |
| Reframed | yes: priced a structural input instead of searching parameters | yes: extended the pricing |
| Compared with the strongest baseline | no: compared only with the repo's own table | no |

Both sessions stated conditionality, kept results as proposals, and didn't edit
`results.md`. Both reran `certify.py` first as a positive control. s2 caught its own
factor-of-108 error with its cross-check, and found that the audit (`audit/F`, line 13)
bounds δ by κ = 3/4 while the scripts check up to 5/6. That's conservative, so every
certificate still holds, but the idealized ceilings may be pessimistic; it left this as
the next handoff.

## Criteria

| Criterion | Rating | Evidence |
|---|---|---|
| `first_step` | good | `certify.py` ran as written in both sessions, in about a second |
| `time_to_result` | good | first checked result in about 6 minutes (s1) |
| `headroom` | fair | Track A is nearly exhausted (about 2·10⁻⁸, by the project's own account); real gains need structural lemmas, which a session can price but not prove |
| `strongest_baseline` | poor | neither session compared with the tracker's record, because the repo's docs don't mention it; the hub's adapter does, but the sessions didn't have it |
| `tracks_target` | fair | the sessions' numbers come from `whatif.py`'s simplified model; s2 found a mismatch between the model's δ range and the audited one. Useful for steering, but not the bound itself |
| `inheritance` | good | s2 took s1's handoff, extended it exactly, and left a precise next handoff |
| `check_cost` | good | exact rational certificate in about a second |
| `home_feasible` | good | CPU seconds, standard Python packages |
| `measurement` | good | exact arithmetic; nothing timing-dependent |
| `claims_risk` | fair | results next to the Riemann hypothesis attract attention; the repo states its conditions carefully, and listings and receipts must keep them |

## Verdict: fast-follow

Fresh sessions oriented quickly, ran the check as written, produced sound and exactly
checked Track B analysis, and the second built on the first: the cumulative behaviour
the hub most wants. But none moved a bound, and none could have: the frontier moves by
proving structural lemmas, by Lean proofs of the open PRs' hypotheses H1–H5, or through
the tracker, and the repo's docs don't point sessions at the strongest record.

**Bottleneck:** search, in proof space: the objective is right, and finding a provable
structural improvement is the hard part.

**Next:** have the README and `auto-research.md` state the tracker's record and how work
here becomes a tracker submission, then run a full pilot with the adapter. If fresh
sessions then target the strongest record and make progress on H1–H5 or a Track B lemma,
that supports `launch`.

```discover-pilot
{
  "schema": "discover-pilot/v0",
  "project": "quasi-rh-hillclimb",
  "repo": "rohanarun/quasi-rh-hillclimb",
  "commit": "0d536c793f5236904f0454fcc7d867354667183c",
  "piloted_on": "2026-10-21",
  "mode": "light",
  "runner": "claude (hub maintainer's session)",
  "self_piloted": false,
  "budget_minutes": 30,
  "sessions": [
    {"id": "s1", "model": "claude (general-purpose agent)", "fresh": true, "minutes": 6, "first_result_minutes": 6,
     "outcome": "no-progress", "beats_strongest": false, "measures_ok": null,
     "note": "Reframed (priced a structural input rather than searching parameters). Exact pricing of a floor-bin witness: alone it buys nothing; reproduces the README's 167/192 ceiling. Reproduced by the runner."},
    {"id": "s2", "model": "claude (general-purpose agent)", "fresh": true, "inherits": "s1", "minutes": 11, "first_result_minutes": 11,
     "outcome": "no-progress", "beats_strongest": false, "measures_ok": null,
     "note": "Reframed. Took s1's handoff: exact bracket for the row-count saving that reaches s1's ceiling; found the scripts' delta range (5/6) wider than the audit's (3/4). Reproduced by the runner."}
  ],
  "criteria": {
    "first_step": {"rating": "good", "evidence": "certify.py ran as written in both sessions, about 1 s"},
    "time_to_result": {"rating": "good", "evidence": "first checked result in about 6 minutes (s1)"},
    "headroom": {"rating": "fair", "evidence": "Track A nearly exhausted (about 2e-8); gains need structural lemmas"},
    "strongest_baseline": {"rating": "poor", "evidence": "neither session compared with the tracker's Lean-verified record; the repo's docs don't mention it"},
    "tracks_target": {"rating": "fair", "evidence": "results are in whatif.py's simplified model; s2 found its delta range wider than the audited one"},
    "inheritance": {"rating": "good", "evidence": "s2 extended s1's handoff exactly and left the next one"},
    "check_cost": {"rating": "good", "evidence": "exact rational certificate in about 1 s"},
    "home_feasible": {"rating": "good", "evidence": "CPU seconds, standard Python packages"},
    "measurement": {"rating": "good", "evidence": "exact arithmetic throughout"},
    "claims_risk": {"rating": "fair", "evidence": "RH-adjacent results attract attention; conditions must stay attached"}
  },
  "bottleneck": "search",
  "verdict": "fast-follow",
  "next": "README and auto-research.md state the tracker's record and how work here becomes a tracker submission; then a full pilot with the adapter."
}
```
