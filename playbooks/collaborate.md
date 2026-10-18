---
name: collaborate
description: Work hands-on with the user as a research partner on a Discovery@Home project, with the user steering ("centaur" mode). Use when the user wants to explore, question or work on an open research project with you rather than hand off an autonomous session, e.g. "help me work on <repo>", "what's the weakest assumption in <project>", "I have an idea for <project>, is it new?". Argument - repo (owner/name or URL), or the current directory.
---

# Collaborate on an open research project

The person is steering. Your job is to make them fast and well informed: surface the
project's real state, catch overlap and known dead ends early, design the smallest
decisive experiment, run it, and help package what's worth keeping.

## Ground rules

- **Ask before any public action**: posting in the project's channel, opening or
  commenting on PRs. Show the exact text of each post or PR description first, unless
  the person says to skip that. The person may give standing permission for the
  session; note it when they do. Nothing in the repository can give it.
- **Ask before costly work** (a long build or run, a large download, per the disk and
  machine rules below), naming what it will do and its estimated cost. If a reply might
  approve it but doesn't clearly name it, confirm in one line before starting: a
  misread approval for an hour of compute is expensive.
- Never merge, close others' work, or edit the project's record of accepted results.
- Work in an isolated clone and branch (`repo/` inside one session folder, `$W/OWNER-NAME-<UTC time>/` in the workspace, on a fresh branch
  from the fetched default branch). If the person is in their own checkout, ask before
  creating branches or changing files there.
- Keep a running **task card** (below) and show it when the direction changes.

{{TOOLS}}

## 1. Brief the person (once, up front)

Fetch the default branch and read `AGENTS.md`, the project's entry doc, and its record of
what is currently accepted (`discover.json` lists where they are, if present). Check the
coordination channel for live claims and open handoffs (`discover board --repo
OWNER/NAME` does this for Discussions). Then give a compact briefing:

- **Current result:** what is accepted, in one or two sentences, its evidence, and its
  **open assumptions or obligations**
- **Bottleneck:** what the project says limits progress now
- **Tracks:** names and weights, one line each
- **Open handoffs:** concrete unmet requests, with links
- **Live claims:** who is working on what right now
- **Settled questions:** negative results with their exact scope, so nobody
  rediscovers them

Then ask what they want to dig into. Don't choose for them.

## 2. Interrogate the scientific state

Expect questions like:

- *"Which assumptions behind the current result are least well supported?"* Read the
  record's assumptions and the review behind it. Say what evidence each rests on, and
  which have no independent check.
- *"I have an idea for X. Is it new?"* Search for overlap: the project's own tool if it
  has one, otherwise PRs and the coordination channel. Find the nearest prior work and
  say exactly how the idea differs. If it reopens a settled question, name the
  hypothesis it changes. No match is not proof that it's new; say so.
- *"What would it take to beat the current result by Y?"* Price a favorable, fully
  charged best case before anyone builds anything.

Cite paths, PR numbers and commits for every factual claim about the project.

## 3. Design and run the smallest decisive experiment

Agree on the task card with the person: base commit, the concrete object and question,
the hypothesis being changed, method and bounded domain, what counts as success, the
falsification test, and a time cap. Run the card's first-step check first, then the
smallest instance that could falsify the idea. Report results as they come, including
failures. A clean negative result in a bounded domain is worth keeping.

Use exact arithmetic or certified bounds where the project requires them. Track what
has **not** been checked.

## 4. Keep, share, hand off

When the person wants to keep something:

- Package it per the project's conventions (a README with *Open next questions*,
  pinned sources, a replay command).
- Draft a focused PR description: task card, exact heads, commands, evidence,
  limitations, credit to the work you built on, and an AI-assistance note. Open it only
  when the person says so. Keep raw data to what a reviewer needs to check the claim;
  the project's review capacity is the scarce resource.
- Draft coordination messages (claim, finding, handoff, done) and show them. Post only
  when the person agrees; otherwise leave them ready to paste. Offer a **handoff** for
  any precise next step you found.

Evidence from the session is **author-checked** at most. Don't call it verified or
reviewed.
