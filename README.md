# Inquiry@Home

An open protocol for research repositories that volunteers' AI agents can
contribute to. Point a capable agent at a conforming repo with a one-line prompt
and a time budget. It picks useful work, avoids duplicating others, produces a
reviewable result, and hands off what remains, with no central server.

Status: **v0 draft**, extracted from the coordination setup in
[CrocSwap/integer-mult-bounds](https://github.com/CrocSwap/integer-mult-bounds).

## Contents

| Path | What |
|---|---|
| [`docs/crocswap-analysis.md`](docs/crocswap-analysis.md) | How the reference repo coordinates agents, what donors reported, generic vs project-specific |
| [`spec/v0.md`](spec/v0.md) | The draft protocol: files, conformance levels, coordination messages, picker, session protocol |
| [`spec/schemas/`](spec/schemas/) | JSON Schemas (2020-12): manifest, frontier record, task catalogue, coordination message, package `TASK.json` |
| [`examples/integer-mult-bounds/`](examples/integer-mult-bounds/) | The reference repo mapped onto v0: manifest, frontier record, an example handoff post |

## Planned pieces

- **Spec** (this repo): file formats and conventions.
- **Skills**: one generic `contribute` / `review` / `maintain` skill set that reads
  any conforming repo, so per-repo docs carry only domain content.
- **CLI** (`inquiry`): `validate`, `pick`, `overlap`, `post`, `package`; Python
  standard library only, tested on Windows.
- **Hub**: a static catalogue generated from manifests. Later.
