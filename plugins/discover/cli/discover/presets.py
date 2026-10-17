"""Permission presets for coding agents (Claude Code settings), per role.

For a maintainer, every public write becomes an explicit prompt (an `ask` rule), which an
automatic checker such as Claude Code's auto mode can't refuse after the person says yes.
For an unattended donor allowed to post, the post commands are pre-approved (narrow `allow`
rules); for a local-only donor, writes are denied. They are conveniences on top of the real
boundary, which is the credentials the agent runs with: a local-only session should run
without GitHub write access at all.

Rules match command prefixes, not repositories: an allowed `gh pr merge` is allowed for
any repo the account can write to. Use them in the folder you run sessions from.
"""

import json
from pathlib import Path

# Commands each playbook may ask to run publicly, in the space form Claude Code's docs use.
# They match only when the subcommand comes first: `gh pr merge 17 -R o/r`, not `gh -R o/r pr merge 17`.
_POST = ["Bash(git push *)", "Bash(gh pr create *)", "Bash(gh api graphql *)",
         "Bash(gh issue comment *)", "Bash(gh pr comment *)"]
_MAINTAIN = _POST + ["Bash(gh pr merge *)", "Bash(gh pr close *)", "Bash(gh pr edit *)",
                     "Bash(gh issue create *)", "Bash(gh issue close *)", "Bash(gh issue edit *)",
                     "Bash(gh repo edit *)", "Bash(gh label create *)"]
_WRITES = sorted(set(_MAINTAIN + ["Bash(gh repo create *)", "Bash(gh repo fork *)", "Bash(gh release create *)"]))

PRESETS = {
    # Unattended and allowed nothing public: deny writes (text match only; the real boundary
    # is running without GitHub write credentials).
    "donor-local": {
        "about": "A donated session with Permissions: local. Nothing public; GitHub writes are denied.",
        "allow": [], "ask": [], "deny": _WRITES,
    },
    # Unattended but allowed to post: narrow allow rules, so the donor's grant isn't refused
    # mid-session; merging and settings stay denied.
    "donor-post": {
        "about": "A donated session with Permissions: post. Claims, findings, handoffs and one focused PR.",
        "allow": _POST, "ask": [],
        "deny": ["Bash(gh pr merge *)", "Bash(gh pr close *)", "Bash(gh repo edit *)", "Bash(gh repo create *)"],
    },
    # The maintainer is present: ask rules always prompt them, and an automatic checker can't
    # refuse what they approve. (An allow rule would also skip protections like not merging
    # unreviewed PRs, which a maintainer preset shouldn't turn off.)
    "maintainer": {
        "about": "A maintainer's own sessions (setup, direct, triage): each public write asks you, and isn't refused after you say yes.",
        "allow": [], "ask": _MAINTAIN, "deny": [],
    },
}


def settings(name):
    p = PRESETS[name]
    perms = {k: p[k] for k in ("allow", "ask", "deny") if p[k]}
    return {"permissions": perms}


def merge_into(path, name):
    """Add a preset's rules to a settings file, keeping everything already there."""
    path = Path(path)
    current = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    perms = current.setdefault("permissions", {})
    added = []
    for key in ("allow", "ask", "deny"):
        rules = perms.setdefault(key, [])
        for rule in PRESETS[name][key]:
            if rule not in rules:
                rules.append(rule)
                added.append(f"{key}: {rule}")
        if not rules:
            del perms[key]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(current, indent=2) + "\n", encoding="utf-8")
    return added
