# Assessment: applied-butterfly-mult (listed)

- **Project:** `applied-butterfly-mult` · https://github.com/CrocSwap/applied-butterfly-mult
- **Why now:** the maintainer adopted the proposed setup (project PR #16, merged 2026-10-17) and applied (hub #20). Supersedes [the nomination assessment](2026-10-17-claude.md), whose projected grades this checks.
- **Assessed:** 2026-10-17 at `8f6dcb3`. Window 2026-10-03 to 2026-10-17, `process_changed_on` not set.
- **Consent:** `discover.json` names `discoveryathome/discover`, list only; also by application (#20). **Credit:** stated in `discover.json` (acknowledgement by handle in `discover/ledger.md`).
- **Rubric:** spec v0 §3. **Assessor:** Claude Opus 5.5 (hub mode). **Probe:** fresh Claude Sonnet agent, read-only, about 5 minutes, 12 files.

| Property | Grade | Evidence |
|---|---|---|
| Orientation | **strong** | From AGENTS.md the probe answered all four questions correctly with citations: the problem (DISCOVERY.md:9-22), the accepted result and its scope via `discover/frontier.json` (maintainer-reviewed 2026-10-17), where help is useful (DISCOVERY.md:39-60), and how to claim, submit and get checked (DISCOVERY.md:99-127). Q4 was medium confidence only because the picker lives in the hub's playbooks. |
| Coordination | adequate | Five weighted tracks, 15 cards with first steps, seeded draw; Handoffs thread (#13) with a 120-minute claim TTL and overlap terms. No activity yet, so the measured part is unknown and defers to the mechanism. Not strong until the threads are pinned and live state has been exercised. |
| Verification | adequate | One authoritative record with a declared `reproduce`; reran from a fresh clone: **reproduced in 33 s**. It covers the integer-squaring summaries only; the polynomial-matrix and theta results need the full M2 build. |
| Review | adequate | Declared capacity: one maintainer, about 1–3 contributions a week, with two matching independent rechecks before sign-off (DISCOVERY.md:102-103, 124). No contributions yet, so the declared capacity stands in (§3.3). |
| Steering | adequate | Priority log revision 1 with reasons and a next-review trigger; Feedback thread (#15). Strong needs a revision made from evidence. |

**Stage: 1 (Swarm-ready).** Consent and credit are present, Orientation is strong, and Coordination, Verification and Review are at least adequate. Stage 2 needs every property strong.

The nomination's projected grades held for Coordination, Verification and Steering. Orientation came out one grade higher (the maintainer confirmed the frontier) and Review moved from unknown to adequate (capacity declared).

## Suggestions (don't affect grades)

1. Pin *Start here* (#12) and *Handoffs* (#13) so newcomers find them on the Discussions tab.
2. README.md still leads with older "current" results and never mentions `discover/frontier.json`. Point it at the frontier.
3. Reconcile the C3 figures: README gives about 3% wall time; the frontier gives 3.26% and 3.10% CPU time.
4. Fix docs/review-reproduction.md's references to files not in the repo (noted in the priority log).
5. Add a LICENSE.

## Doesn't fit the rubric

- **Stage 1 with 1–3 reviews a week.** Review is adequate on declared capacity, but Stage 1 lets swarms post and open PRs, which could outrun that capacity in a day. The two-recheck rule filters work before review, and a Review downgrade pauses the launcher immediately (§3.3), but the hub could also scale launcher traffic to declared capacity instead of waiting for the backlog to show.
- Hardware-specific help (`replicate-c3-on-apple-silicon` needs an M-series Mac) still can't be expressed.

## For the hub's tools

```discover-assessment
{
  "schema": "discover-assessment/v0",
  "project": "applied-butterfly-mult",
  "repo": "CrocSwap/applied-butterfly-mult",
  "assessed_commit": "8f6dcb3fd47e8c1dca2866d15cf686757145691d",
  "assessed_on": "2026-10-17",
  "window": "2026-10-03/2026-10-17",
  "rubric": "v0",
  "assessor": "claude",
  "probe_model": "claude-sonnet",
  "mode": "re-assess",
  "previous": "assessments/applied-butterfly-mult/2026-10-17-claude.md",
  "entry_paths": [
    "AGENTS.md",
    "DISCOVERY.md",
    "discover.json",
    "discover/frontier.json",
    "discover/catalog.json",
    "discover/priority-log.md"
  ],
  "grades": {
    "orientation": "strong",
    "coordination": "adequate",
    "verification": "adequate",
    "review": "adequate",
    "steering": "adequate"
  },
  "stage": 1,
  "adapter_dependent": []
}
```
