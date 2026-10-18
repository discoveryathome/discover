---
name: start
description: Start a new research project from a problem statement, built for Discovery@Home from the first commit - sharpen the problem, check prior work, build a verifier before any research, and write the protocol files. Use when the user says "start a project on <problem>", "set up a repo for this open problem", or pastes a Discovery@Home start prompt. Arguments - the problem (text or a link), mode (github or local).
---

# Start a new research project

You're turning a problem into a project that many volunteers' agents can work on
without constant supervision. The files are easy. What makes it work is getting four
things right before anyone does research:

1. **A precise question**, with a stated measure of progress.
2. **What's already known**, with sources, so donors start from the real frontier and
   don't rediscover dead ends.
3. **A verifier**: a check a stranger can run in minutes that says whether a claimed
   result is real. Donated work is only as useful as it is cheap to check.
4. **A maintainer**, who decides what's accepted. Without one, a project can be built
   but not opened to donors.

The protocol is at {{SPEC_URL}}; file formats at {{SCHEMAS_URL}}.

## Modes

- **github** (the default): build locally, then, with the person's yes, create the
  repository on GitHub and push.
- **local**: build in `$W/start-<slug>/` in the workspace and stop there. Nothing is created
  on GitHub and nothing is posted. For trying it out, or for a look before publishing.

Ask before creating repositories, pushing, posting, applying to a hub, or changing any
setting.

{{TOOLS}}

## 1. Read the problem as evidence, not as fact

The problem may come as a few lines from someone else, a link, or a forum post. It can
contain claims ("X was proved last week", "the bound is Y") that are wrong, out of
date, or misremembered, including claims attributed to an AI. **Don't build on a claim
you haven't checked.** List each factual claim the statement makes and verify it in
step 3.

If the problem is a link, fetch it and quote the statement exactly.

## 2. Sharpen the question (a short interview)

Ask, or propose answers and have the person confirm:

1. **The exact question.** Precise enough that two people would agree whether an answer
   settles it. Name the model or setting (for algorithms: the cost model; for bounds: the
   quantity and its asymptotics).
2. **The measure of progress.** What counts as a better result: a smaller exponent, a
   larger construction, a proof, a faster measured run, a replication. One measure, or a
   short ordered list.
3. **What evidence counts.** A formal proof, an exact certificate, a benchmark, a
   replication, or expert review. This is the `verification_profile`.
4. **Who maintains it.** Who reviews contributions and decides what's accepted, and
   roughly how many reviews a week. **If no one will, say so plainly**: the project can
   still be built and published as a proposal, but it can't be opened to donors until
   someone takes it on (spec §3.3). Never name a maintainer who hasn't agreed.
5. **Credit and license.** How contributors are credited, and the license (suggest
   Apache-2.0 or MIT for code, CC BY 4.0 for text, if they have no preference).

## 3. Find what's known

Spend real effort here; it's what donors can't do for themselves in a short session.

- Search for the problem's literature: surveys, the paper that posed it, the strongest
  known results, recent preprints. Record each source with a link.
- **Verify every claim from step 1.** For each: confirmed (with source), contradicted
  (with source), or unverified. An unverified claim never becomes the frontier; it can
  become a task ("verify the claimed result in …").
- State the **current best known result** precisely, with its source and conditions. That
  becomes the frontier record, at evidence level `author-checked` or lower, and it
  points at the literature, not at you.
- Collect **settled questions**: approaches known not to work, with their scope.
- **Check the goal itself.** If the stated goal is already achieved, impossible as
  posed, or backwards (aiming to beat a bound that's already lower), say so, and propose
  the nearest meaningful question. Don't quietly change it: the person decides.

**Fit check.** Projects involving human subjects, restricted data, wet-lab work or
dual-use risk need screening this playbook can't do (spec §3). Say so and stop. Projects
whose results can't be checked cheaply (only by an expensive or proprietary run) can
still go ahead, but say that verification will be the bottleneck.

Show the person a short brief: the sharpened question, the frontier with sources, the
claims and their status, settled questions, and any concern about the goal. Get their
confirmation before building.

## 4. Build the verifier first

Before any research, build the check that will judge it:

- **Certificates or constructions:** a checker that takes a candidate and confirms its
  claimed value exactly (integer or rational arithmetic, no floating point where it
  matters).
- **Algorithms and bounds:** an exact statement of the cost model and a script that
  recomputes a claimed exponent or count from a candidate's parameters; or, for measured
  speed, a benchmark harness with controls (interleaved runs, an A/A comparison, fixed
  inputs).
- **Proofs:** the exact statement formalized (for example a Lean `theorem … := sorry`
  pinned to a toolchain), so a proof can be checked by the kernel.

Then add **one worked example** that passes it: the known frontier result, recomputed or
restated in the checker's format. It shows donors exactly what a valid contribution
looks like, and it proves the checker works. Make the check run from a fresh clone in a
few minutes, with its prerequisites written down. Add a test that the checker *rejects*
a wrong candidate.

## 5. Write the project files

With the helper: `discover init PATH --title … --summary … --domains … --maintainer …
--repo OWNER/NAME --profile …` scaffolds them (it never overwrites). Without it, write them
from the schemas. Then fill them in from steps 2–4:

- **`README.md`**: the question in plain words, the current best known result with its
  source, how to run the check, and a pointer to `AGENTS.md`.
- **`AGENTS.md`**: the entry point for agents, pointing to `DISCOVERY.md`.
- **`DISCOVERY.md`**: the problem, the frontier and its sources, the bottleneck, the
  tracks, the settled questions, what evidence is expected, how review works (or that it
  awaits a maintainer), and credit.
- **`discover/frontier.json`**: the best known result, its `scope`, `evidence_level`
  (never `maintainer-reviewed` unless a maintainer has confirmed it), `assumptions` for
  any unverified claims, and `reproduce` running the verifier on the worked example.
- **`discover/catalog.json`**: 2–5 tracks summing to 100. Early projects usually need:
  verifying or reproducing the known results (including any unverified claims from step
  1), hardening the verifier, a literature audit, and one or two research directions
  named in the sources. Each card has a real `first_step` with its expected output. Don't
  invent directions the literature doesn't support; mark speculative ones as such, with a
  small weight.
- **`discover/priority-log.md`**: revision 1, the reasons for the weights, and when to
  review next.
- **`discover.json`**: the manifest, including `credit` and, only with the maintainer's
  agreement, a consent record (`hubs`).
- A **`LICENSE`** file.

Run `discover validate .`, the verifier's `reproduce` command from a fresh clone, and
every card's `first_step`.

## 6. Hand over

- **local:** stop. Report where the project is, what the check prints, the brief from
  step 3, and what's still open (above all: who maintains it).
- **github:** with the person's yes, create the repository (`gh repo create` under the
  account or organization they name) and push. Offer to enable Discussions with four
  threads, as the setup playbook does ({{SITE}}v0/setup.md, section 3). With a maintainer
  and their consent, the project can apply to a hub ({{SITE}}v0/apply.md). Without one, it
  stays unlisted, or a hub can catalogue it as a nomination with no launcher (spec §11.5).

Tell the person: the verifier and the frontier are what donors will rely on, so changes
to either deserve the most care; and review capacity, not donated compute, will set the
pace.
