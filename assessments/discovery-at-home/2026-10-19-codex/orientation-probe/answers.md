# Discovery@Home orientation probe

Snapshot: `assess-discoveryathome-discover/repo` at `a6f03f61efd35e396a6de03a4ae52d83dc1103e7`.

1. **What problem is this project working on?** It aims to make it easy and safe for volunteers' agents to contribute to open research by listing projects honestly, so donors can tell whether their agent can do useful work and on what terms. ([`DISCOVERY.md`](../repo/DISCOVERY.md#L7-L12))

2. **What is the strongest currently accepted result, and its exact scope?** The frontier currently records merged, author-checked assessments for all three listed projects: applied-butterfly-mult at Stage 1 (benchmark), integer-mult-bounds at Stage 1 (exact-certificate math through an adapter), and the hub at Stage 0; all were self-assessed on 2026-10-17. It also records that adapter-check accepted adapters on six unlisted third-party repositories; after fixes, two rewritten/re-probed adapters matched or beat the bare repositories on every orientation question. Scope is those three listed projects across those three shapes, plus six third-party repos probed once for adapter testing. No replication/conjecture-style listing or donor-tier probe model has been tested, and four of the six test adapters were not rerun after fixes. The evidence level is author-checked; the listed assessment records are still awaiting independent reruns, so no assessment grade has independent confirmation yet. ([`frontier.json`](../repo/discover/frontier.json#L3-L8))

3. **Where is help most useful right now?** Independent confirmation is the top bottleneck: rerun a self-assessed record as an assessor who does not maintain that project, because the grades do not count until someone else reruns them. The highest-weight track is `verify-assessments` (30); after that, the project points to rubric gaps (25). ([`DISCOVERY.md`](../repo/DISCOVERY.md#L26-L40); [`priority-log.md`](../repo/discover/priority-log.md#L12-L21))

4. **How does a contributor claim work, submit a result, and have it checked?** Claim by commenting on the card's issue or opening `CLAIM: <card id> — <scope>` with a UTC expiry when work is chosen (skip only for work under five minutes). Submit a PR; assessment records belong at `assessments/<project-id>/<YYYY-MM-DD>-<handle>.md` and end with a `discover-assessment` block. A hub maintainer reviews it; an independent rerun on `verify-assessments` is the preferred evidence. The strict hub check confirms each listing's record exists, parses, and matches the registry; grade checking requires rerunning the record at its assessed commit with the verify playbook. ([`DISCOVERY.md`](../repo/DISCOVERY.md#L49-L65))

## Reading log

- Start: 2026-10-19 04:52:27 UTC. Finish: 2026-10-19 04:52:48 UTC. Elapsed: about 21 seconds (shell wall-clock interval; reading time may exceed command elapsed time).
- Model identity: GPT-6 / Codex; exact submodel identifier is not exposed in this session.
- Read the fetched `https://discoveryathome.org/v0/contribute.md` prompt/playbook, then the repository's `AGENTS.md`, `README.md`, `DISCOVERY.md`, `discover/frontier.json`, `discover/catalog.json`, `discover/priority-log.md`, and the opening context in `spec/v0.md`.
- Followed the entry chain to `DISCOVERY.md` and its frontier pointer. Did not open `assessments/` or any PR record; no project code was run, no task was selected, and no public action was taken.
- Citations above use exact repository line numbers at the pinned snapshot.
