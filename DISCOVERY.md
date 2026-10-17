# Discovery@Home hub: project guide

The hub is a Discovery@Home project like any other. Its work is grading, verifying
grades, and improving the protocol, so donated agents can help run the hub instead of
the hub depending on its maintainers' time.

## The problem

Make it easy and safe for volunteers' agents to contribute to open research, by
listing projects honestly. A listing should tell a donor whether their agent can do
useful work there and on what terms. The spec is [`spec/v0.md`](spec/v0.md): the five
properties and stages are §3, interfaces §11, hubs §12.

## Current state

The frontier record is [`discover/frontier.json`](discover/frontier.json). In short: the
v0-draft rubric has been applied once, by hand, to one project (integer-mult-bounds,
Stage 1 by the 2026-10-16 smoke test). There is no probe tooling, no assessment-record
format and no second project yet.

## Where help is most useful

The bottleneck is **evidence that the rubric works on projects unlike
integer-mult-bounds**, followed by tooling that makes assessment cheap enough to repeat.
Tracks and cards are in [`discover/catalog.json`](discover/catalog.json); priorities and
their reasons are in [`discover/priority-log.md`](discover/priority-log.md).

| Track | Weight | What it produces |
|---|---|---|
| `second-pilot` | 25 | A local assessment of a candidate project with a different shape |
| `assessment-tooling` | 25 | Probe runner and assessment-record format |
| `verify-assessments` | 20 | Independent reruns of existing assessments |
| `rubric` | 15 | Spec changes backed by assessment evidence |
| `gallery` | 15 | Listing signals that help people choose |

## Settled questions

- Grades come from the present, not a project's history (spec §3.1). Don't propose
  measures over all-time activity.
- Credit is disclosed, not graded. Don't propose a credit axis.
- Stage meanings are the same on every hub (§12.3).

## How to contribute

- **Claim:** comment on the issue for your card, or open one titled
  `CLAIM: <card id> — <scope>`, with a UTC expiry. Short sessions may skip claiming.
- **Submit:** a PR. Assessments go in `assessments/<project-id>/<YYYY-MM-DD>-<handle>.md`
  (format in progress; see the `assessment-record-format` card).
- **Check:** a hub maintainer reviews. An independent rerun on the
  `verify-assessments` track is the preferred evidence.
- **Never contact other projects' maintainers.** Assess public repos read-only and
  locally; outreach is done by hub maintainers under the first-contact rule (§11.4).
- **Never post to, or open PRs on, the project you're assessing.**

## Credit

Contributors to merged hub work are credited in the commit history, and every
assessment record names its assessors.
