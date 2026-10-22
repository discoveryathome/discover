# Project visuals

Hub-curated editorial covers for all 25 registry entries, reviewed 2026-10-22.
The site reads `catalog.json` separately from generated project data. Covers appear
on cards and detail pages; the original project/frontier visual remains under
“Project result visual”. No project claims or registry grades are changed.

## Sources and distinctions

Each catalogue entry records its source URL at a fixed Git commit, a credit,
accessible description, public-facing question and scope caption. These are
curated snapshots, not automatically updated claims about the latest frontier.

- **Project packings:** Polyhedra in Polyhedra (15 octahedra in a cube), and the
  circle-packing project's 100-circle certified layout. Files are copied unchanged.
- **Project figures:** antenna polar patterns, the 25-bar truss comparison, and
  asteroid-precovery image evidence. Files are copied unchanged, with all panels
  and labels retained. These represent simulations or a replication, as captioned.
- **Drawn from project data:** the seven-block Fano control and the LABS N=13
  reference sequence. Frozen inputs are in `sources/`; `tools/draw_gallery.py`
  draws the incidence matrix and computes the exact aperiodic autocorrelation.
  LABS sequence attribution: Packebusch and Mertens (2016), as recorded upstream.
- **Mathematical schematics:** original SVG explanatory drawings for the other
  mathematical/computational problems. These are explicitly illustrations, not
  frontier witnesses, benchmark plots or optimality claims. The tree uses toy DNA;
  the code example uses two toy words; the circuit shares an XOR expression;
  the zero-free half-plane uses the preprint's 7/8 reference, not today's bound.
  Super-1 shows a conceptual three-tier recurrent-memory hierarchy; tier spacing
  does not assert exact update intervals. Its earlier AI illustration is retained
  as an unused alternative (`super-1.jpg`), with its prompt in `prompts.json`.
- **AI illustrations:** cancer dependencies, quantum ground states and
  the hub. Generated with the built-in image-generation tool. Exact prompts are
  in `prompts.json` and the catalogue, and can be opened on each project page.
  JPEG delivery copies retain the complete composition; source PNGs were retained
  in the generation tool's output directory. These images are conceptual artwork.

Source license notices are retained in `licenses/`. In particular, the polyhedra
project credits Yohei Nakajima for the soft-to-rigid method and Alejandro Zarzuelo
for its generalization. Source figures retain their original attribution and rights.

## Asteroid image acknowledgements

The evidence figure is by the Asteroid precovery local pilot contributors. The
Digitized Sky Surveys were produced at the Space Telescope Science Institute under
U.S. Government grant NAG W-2166. The photographic material was obtained using the
Oschin Schmidt Telescope on Palomar Mountain. DSS/STScI/AURA and the original
photographic institutions retain their rights. The full original XE036 and XO036
plate headers are preserved in `sources/`, and the upstream data notices are in
`licenses/asteroid-precovery-DATA_LICENSES.md.txt`.

See the [DSS acknowledgements](https://archive.stsci.edu/dss/acknowledging.html).
The project also uses ESA Gaia data processed by DPAC, and NASA/JPL predictions;
the archive replication is not a newly discovered asteroid observation.

## Maintenance

Run `python3 tools/draw_gallery.py` to regenerate the explanatory SVGs. It requires
only the Python standard library and frozen local source files; it never fetches
or executes upstream code. Update the catalogue and attribution when changing an
asset. Keep each file below 1 MB. Use `contain` for evidence so it is never cropped,
and `cover` only for the conceptual art. Image loading is lazy on gallery cards.
A missing catalogue falls back to the original site visuals; failed images retain
the explanatory question. Run `make test` before proposing changes.

## Added 2026-10-22

- **Numerical computation:** the actual φ₁ function and an illustrative degree-four
  Taylor polynomial on [−4,4], plus their rescaled residual. Both are computed in
  `tools/draw_gallery.py`; neither curve asserts a project candidate or certified
  bound.
- **Genomic sequence indexing:** a toy sequence, four exact ACG matches and the
  corresponding ordered suffix interval. Letters encode bases; there is no prose
  inside the image. This explains exact substring search without implying any
  biological experiment or biological-effect prediction.
- **Pathfinding:** steps 0 and 25 of the 160-agent `room-32-32-4-s2-n160` archive
  plan. `sources/pathfinding-room-plan.json` preserves the source grid, goals,
  routes, metrics and source-artifact SHA-256 from the project's round-two playback.
  The generator checks the full plan for blocked cells, illegal moves, shared-cell
  collisions, edge swaps and final goals before drawing. Contains information from
  [Moving AI Lab benchmarks](https://movingai.com/benchmarks/), available under the
  [ODC Attribution License](https://opendatacommons.org/licenses/by/1-0/).
  Baseline solver: [LaCAM3, Keisuke Okumura](https://github.com/Kei18/lacam3).
  Benchmark reference: Sturtevant, “Benchmarks for Grid-Based Pathfinding,” 2012.
  Upstream notices are retained in `licenses/pathfinding-THIRD-PARTY.md.txt`.
