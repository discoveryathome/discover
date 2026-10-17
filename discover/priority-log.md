# Priority log

## Revision 2 — 2026-10-17: confirm what's recorded

**Base and sources:** main at 996c7e4; the records in `assessments/`; the hub check's
report; the onboarding, adapter and donation test series (ROADMAP.md, Done); issues #1–#6.

**What changed since revision 1.** Its trigger fired: a second-shape pilot landed.
applied-butterfly-mult (a benchmark project) is assessed twice, integer-mult-bounds and the
hub once each, all with records in the new format (#3, done). Six third-party
repositories were probed with and without adapters. The hub check flags stale listings.
But every record is self-assessed (spec §12.4): the hub's maintainers maintain all three
projects, so no stage counts until someone else reruns it.

| Track | Old | New | Why |
|---|---:|---:|---|
| `verify-assessments` | 20 | 30 | Now the bottleneck: independent reruns are what let any stage count. New card `independent-rerun`. |
| `rubric` | 15 | 25 | Real assessments produced concrete gaps; new card `rubric-gaps-from-testing`. |
| `assessment-tooling` | 25 | 20 | Record format done (card retired). Left: the probe runner, and `board-issues-transport`, since the hub's own board can't see its claims. |
| `second-pilot` | 25 | 15 | Benchmark shape done; replication and conjecture shapes remain. |
| `gallery` | 15 | 10 | Wait for an outside pilot to show what people need. |

**Limits.** One person maintains everything assessed so far, and every probe used one model
family. Thresholds are uncalibrated.

**Next experiment.** An independent rerun of one record, ideally applied-butterfly-mult's,
on a different account: does it reproduce the grades?

**Stop rule.** If two independent reruns disagree with the original on two or more
properties, pause new assessments and work on the rubric until reruns agree.

**Next review:** after the first independent rerun lands, when an outside project applies,
or in 30 days.

## Revision 1 — 2026-10-16: get evidence beyond one project

The rubric has been applied once, by hand, to one project of one shape. The biggest
risk is that it only fits that shape, so a second pilot of a different shape and the
tooling to make assessment repeatable get the most weight (25 each). Independent
reruns (20) test probe reliability, which every grade depends on. Rubric and gallery
work (15 each) should follow evidence rather than lead it.

Next review: after the first second-pilot assessment lands, or in 30 days.
