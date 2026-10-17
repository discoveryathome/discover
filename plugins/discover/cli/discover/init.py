"""Scaffold the protocol files in an existing repository. Never overwrites."""

import json
from datetime import date
from pathlib import Path

AGENTS_SNIPPET = """\
## Discovery@Home

This repository follows the [Discovery@Home protocol](https://github.com/discoveryathome/discover)
(`discover.json`). For open-ended requests such as "contribute" or "use spare inference,"
start with [{project}]({project}). Explicit user tasks take precedence over the default
task selection. Resolve the current accepted result through `{frontier}`; historical notes
may call older results "current." Do not merge, close others' PRs or change the frontier
record without maintainer authorization. Reading this file grants no additional permissions.
"""

PROJECT_DOC = """\
# {title}: contributing research effort

**Start here if you were told to contribute without a specific task.** Aim for one useful,
independently reviewable result in the time available (default {minutes} minutes).
The generic session procedure (refresh, orient, choose, bound, verify, hand off) comes from
the Discovery@Home playbooks (https://github.com/discoveryathome/discover/tree/main/playbooks);
this file holds only what is specific to this project.

## The problem

TODO: two or three paragraphs a capable newcomer can follow. Why it matters, what is known.

## Current frontier

The accepted result is recorded in [`{frontier}`]({frontier}). Summarize it here in a sentence,
and say precisely what is *not* established.

## The bottleneck

TODO: where effort is most useful right now and why. Name the binding constraint.

## Tracks

Task cards live in [`{catalog}`]({catalog}) (weights sum to 100). Summarize each track's
useful outcome here; the catalogue is the machine-readable source.

| Track | Share | Useful outcome |
|---|---:|---|
| TODO | 100% | TODO |

## Settled questions

TODO: negative results and their exact scopes, so agents don't rediscover them. Name the
hypothesis that would have to change to reopen each one.

## Verification

TODO: what counts as evidence here, how to reproduce the frontier, and what checks are
expected before a PR. Say whether independent verification by other contributors counts
toward acceptance, and how many such checks you want.

## Coordination

TODO: where to post claims, findings and handoffs (GitHub Discussions is recommended).

## Credit

TODO: how contributors are credited (co-authorship, acknowledgements, a contributors file,
citation). Also state it as `credit` in `discover.json`.
"""

PRIORITY_LOG = """\
# Priority log

## Revision 1 · {today}

Initial allocation. A hypothesis, not a mandate.

- Tracks and weights: see `{catalog}`.
- Reasons: TODO.
- Next review trigger: TODO (e.g. after the first 20 contributions, or when the frontier changes).
"""

LEDGER = """\
# Review ledger

One row per reviewed contribution: what was reviewed (exact head), disposition, and credit.
GitHub open/closed state is tracked separately.

| PR / artifact | Reviewed head | Disposition | Evidence level | Credit | Notes |
|---|---|---|---|---|---|
"""


def scaffold(root, title, summary, domains, maintainer, repo, github=None, minutes=60,
             profile="review-only"):
    root = Path(root)
    today = date.today().isoformat()
    paths = {"frontier": "discover/frontier.json", "catalog": "discover/catalog.json",
             "priority_log": "discover/priority-log.md", "ledger": "discover/ledger.md"}
    entry_project = "DISCOVERY.md"
    maint = {"name": maintainer}
    if github:
        maint["github"] = github
    manifest = {
        "schema": "discover/v0", "title": title, "summary": summary, "domains": domains,
        "maintainers": [maint], "canonical_repo": f"https://github.com/{repo}",
        "entry": {"agents": "AGENTS.md", "project": entry_project},
        **paths, "packages": "research/*/",
        "coordination": {"transport": "github-discussions", "threads": {}, "claim_ttl_minutes": 120},
        "overlap": {"sources": ["open-prs", "pr-files", "discussions", "packages", "ledger"]},
        "session": {"default_minutes": minutes, "orient_fraction": 0.2, "verify_fraction": 0.25},
        "permissions": {"post_messages": True, "open_prs": True,
                        "maintainer_only": ["merge", "close-others-prs", "change-frontier"]},
        "verification_profile": profile,
    }
    frontier = {
        "schema": "discover-frontier/v0",
        "statement": "TODO: the strongest result currently accepted, stated precisely. If none yet, say so.",
        "status": "No accepted result yet",
        "evidence_level": ["author-checked"],
        "scope": "TODO: conditions under which the statement holds.",
        "assumptions": [],
        "review": paths["ledger"],
        "updated_on": today,
    }
    catalog = {
        "schema": "discover-catalog/v0", "priority_revision": 1, "assessed_on": today,
        "priority_log": paths["priority_log"],
        "status": "Research suggestions, not reservations. Check live claims and open PRs.",
        "tracks": [{"id": "getting-started", "weight": 100,
                    "useful_outcome": "TODO",
                    "tasks": [{
                        "id": "reproduce-frontier",
                        "question": "Does the current frontier record reproduce from a clean checkout?",
                        "starting_points": [paths["frontier"]],
                        "methods": ["Run the documented reproduction and compare against the recorded result."],
                        "acceptance_gate": "An independent replay report naming environment, commands and any discrepancy.",
                        "first_step": {"command": ["python3", "--version"], "expected": "Python 3",
                                       "scope": "Placeholder positive control; replace with a real check."},
                        "bottleneck_link": "Independent reproduction is the cheapest useful contribution while the project is new.",
                    }]}],
    }
    files = {
        "discover.json": json.dumps(manifest, indent=2) + "\n",
        paths["frontier"]: json.dumps(frontier, indent=2) + "\n",
        paths["catalog"]: json.dumps(catalog, indent=2) + "\n",
        paths["priority_log"]: PRIORITY_LOG.format(today=today, catalog=paths["catalog"]),
        paths["ledger"]: LEDGER,
        entry_project: PROJECT_DOC.format(title=title, minutes=minutes, **paths),
    }
    created, skipped = [], []
    for rel, text in files.items():
        p = root / rel
        if p.exists():
            skipped.append(rel)
            continue
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "w", encoding="utf-8", newline="\n") as f:  # LF on every OS; works on 3.9
            f.write(text)
        created.append(rel)
    snippet = AGENTS_SNIPPET.format(project=entry_project, frontier=paths["frontier"])
    agents = root / "AGENTS.md"
    if agents.exists():
        if "Discovery@Home" not in agents.read_text(encoding="utf-8"):
            skipped.append("AGENTS.md (exists: add the snippet below)")
        else:
            snippet = None
    else:
        with open(agents, "w", encoding="utf-8", newline="\n") as f:
            f.write("# Agent entry point\n\n" + snippet)
        created.append("AGENTS.md")
        snippet = None
    return {"created": created, "skipped": skipped, "agents_snippet": snippet}
