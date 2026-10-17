"""Copy-paste prompts. The explore page builds the same prompts client-side from templates()."""

import secrets

FOCUS = {
    "project": "Choose useful work according to the repository's current priorities, preferring an open handoff on the drawn track.",
    "audit": "Prioritize independent verification and auditing of pending or accepted claims.",
    "explore": "Prioritize exploring a genuinely new approach, priced against a favorable best case first.",
}

PERMISSIONS = {
    "post": "Permissions: post. You may post routine claims, findings and handoffs in the project's coordination channel and open one focused PR without asking me again for each action.",
    "local": "Permissions: local. Do not post publicly or open PRs; leave everything ready for me to review and publish myself.",
}

# Every action starts from one short prompt that points at a hosted playbook (spec §1).
TEMPLATE = (
    "Fetch {site}v0/contribute.md (for example with curl) and follow it to contribute to {repo_url}. "
    "Budget: about {minutes} minutes. {focus} {permissions} "
    "Seed: {seed}{drawn}. "
    "If you can't fetch the playbook: read the repository's AGENTS.md and follow it; don't choose a task "
    "\"at random\" yourself, use the seed; keep the last quarter of the time for verification; and report "
    "the exact scope, evidence, what was not checked, and predecessor credit. "
    "Never merge, close others' PRs, or change the project's record of accepted results."
)

# Methods are sentences, so the drawn method is quoted, without its final period.
DRAWN = " (from it the hub drew track {track}, card {card}, method \u201c{method}\u201d)"

# Other actions, one line each.
ACTIONS = {
    "verify": "Fetch {site}v0/verify.md (for example with curl) and follow it to independently verify a result in {repo_url}. Budget: about {minutes} minutes. {permissions}",
    "collaborate": "Fetch {site}v0/collaborate.md (for example with curl) and follow it: I want to work with you on {repo_url}. Brief me on its current state first. Ask before any public action.",
    "setup": "Fetch {site}v0/setup.md (for example with curl) and follow it to help me make my repository agent-ready for Discovery@Home. Ask before pushing, opening PRs or changing settings.",
    "apply": "Fetch {site}v0/apply.md (for example with curl) and follow it to apply to list my project {repo_url} on the Discovery@Home hub. Ask before posting anything.",
    "direct": "Fetch {site}v0/direct.md (for example with curl) and follow it to review priorities for my project {repo_url}. Propose one revision; ask before merging or posting.",
    "assess": "Fetch {site}v0/assess.md (for example with curl) and follow it to assess {repo_url} for the hub. Read-only toward that project: never post to it or contact its maintainers.",
}

# Onboarding a project: one prompt, two words swapped (spec §11.5). The page and the CLI
# fill in role and goal; onboard.md routes to setup, apply and assess.
ONBOARD = (
    "Fetch {site}v0/onboard.md (for example with curl) and follow it. "
    "Role: {role}. Goal: {goal}. Project: {repo_url}.{context} "
    "Ask before posting anything, pushing, opening issues or PRs, or changing settings."
)
ONBOARD_CONTEXT = " Context: {context}."
GOALS = {
    "maintainer": ["evaluate", "setup", "submit", "setup-and-submit"],
    "contributor": ["evaluate", "nominate", "propose", "propose-and-nominate"],
}

SKILL_COMMAND = "/discover:contribute {repo} --minutes {minutes} --focus {focus} --permissions {permissions} --seed {seed}"


def donation_prompt(repo, minutes=60, focus="project", permissions="post", seed=None, site=None, drawn=None):
    from . import SITE
    return TEMPLATE.format(site=site or SITE, repo_url=f"https://github.com/{repo}", minutes=minutes,
                           focus=FOCUS[focus], permissions=PERMISSIONS[permissions],
                           seed=seed or secrets.token_hex(16), drawn=DRAWN.format(**{**drawn, "method": drawn["method"].rstrip(". ")}) if drawn else "")


def action_prompt(action, repo, minutes=60, permissions="local", site=None):
    from . import SITE
    return ACTIONS[action].format(site=site or SITE, repo_url=f"https://github.com/{repo}",
                                  minutes=minutes, permissions=PERMISSIONS[permissions])


def onboard_prompt(role, goal, repo, context=None, site=None):
    from . import SITE
    if goal not in GOALS[role]:
        raise ValueError(f"goal for a {role} must be one of {GOALS[role]}")
    return ONBOARD.format(site=site or SITE, role=role, goal=goal, repo_url=f"https://github.com/{repo}",
                          context=ONBOARD_CONTEXT.format(context=context) if context else "")


def skill_command(repo, minutes=60, focus="project", permissions="post", seed=None):
    return SKILL_COMMAND.format(repo=repo, minutes=minutes, focus=focus, permissions=permissions,
                                seed=seed or secrets.token_hex(16))


def templates(site=None):
    """Everything the explore page needs to build the same prompts client-side."""
    from . import SITE
    return {"site": site or SITE, "template": TEMPLATE, "drawn": DRAWN, "focus": FOCUS,
            "permissions": PERMISSIONS, "actions": ACTIONS, "skill_command": SKILL_COMMAND,
            "onboard": ONBOARD, "onboard_context": ONBOARD_CONTEXT, "goals": GOALS}
