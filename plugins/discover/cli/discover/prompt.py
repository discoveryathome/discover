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
    "Seed: {seed}{drawn}.{adapter} "
    "If you can't fetch the playbook: read the repository's AGENTS.md and follow it; don't choose a task "
    "\"at random\" yourself, use the seed; keep the last quarter of the time for verification; and report "
    "the exact scope, evidence, what was not checked, and predecessor credit. "
    "Never merge, close others' PRs, or change the project's record of accepted results."
)

# Methods are sentences, so the drawn method is quoted, without its final period.
DRAWN = " (from it the hub drew track {track}, card {card}, method \u201c{method}\u201d)"

# Projects listed through an adapter (spec §12.5): the hub's map of the repo's own conventions.
ADAPTER = " The hub's adapter for this project maps its conventions: {adapter_url}. Read it after the playbook."

# Other actions, one line each.
ACTIONS = {
    "verify": "Fetch {site}v0/verify.md (for example with curl) and follow it to independently verify a result in {repo_url}. Budget: about {minutes} minutes. {permissions}{adapter}",
    "collaborate": "Fetch {site}v0/collaborate.md (for example with curl) and follow it: I want to work with you on {repo_url}. Brief me on its current state first. Ask before any public action.{adapter}",
    "setup": "Fetch {site}v0/setup.md (for example with curl) and follow it to help me make my repository agent-ready for Discovery@Home. Ask before pushing, opening PRs or changing settings.",
    "apply": "Fetch {site}v0/apply.md (for example with curl) and follow it to apply to list my project {repo_url} on the Discovery@Home hub. Ask before posting anything.",
    "direct": "Fetch {site}v0/direct.md (for example with curl) and follow it to review priorities for my project {repo_url}. Propose one revision; ask before merging or posting.",
    "adapt": "Fetch {site}v0/adapt.md (for example with curl) and follow it in local mode to write the hub's adapter for {repo_url}. Read-only toward that project: never post to it or contact its maintainers.",
    "pilot": "Fetch {site}v0/pilot.md (for example with curl) and follow it to pilot {repo_url}: run fresh donated sessions against it and judge whether their results hold up. Ask before running the project's code. Never post to the project or contact its maintainers.",
    "intake": "Fetch {site}v0/intake.md (for example with curl) and follow it to review the hub application or nomination for {repo_url}. Recommend; don't merge. Never post to that project or contact its maintainers.",
    "assess": "Fetch {site}v0/assess.md (for example with curl) and follow it to assess {repo_url} for the hub. Read-only toward that project: never post to it or contact its maintainers.",
}

# The hub's periodic curation sweep (playbooks/curate.md): no repository, the whole registry.
CURATE = (
    "Fetch {site}v0/curate.md (for example with curl) and follow it to run the hub's curation sweep. "
    "Propose fixes as hub PRs; don't merge, change settings, or contact any project."
)


def curate_prompt(site=None):
    from . import SITE
    return CURATE.format(site=site or SITE)


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

# Starting a new project from a problem (playbooks/start.md). The problem is the person's own
# text, quoted; the playbook checks its claims before building on them.
START = (
    "Fetch {site}v0/start.md (for example with curl) and follow it to start a new research project "
    "on the problem below, set up for Discovery@Home from the start.{mode} Ask before creating "
    "repositories, pushing, posting or changing settings.\n\nProblem:\n<<<\n{problem}\n>>>"
)
START_LOCAL = " Mode: local (build it on disk only)."

# Donating to wherever it's useful (playbooks/explore.md): the agent draws the project from
# the hub's agents.json with the seed, then follows contribute.md there.
EXPLORE = (
    "Fetch {site}v0/explore.md (for example with curl) and follow it to donate about {minutes} minutes "
    "of research to a Discovery@Home project drawn from the hub.{interests} {permissions} Seed: {seed}. "
    "Never merge, close others' PRs, or change a project's record of accepted results."
)
EXPLORE_INTERESTS = " Interests: {interests}."

# One-time setup of a donor's folder (playbooks/prepare.md): the helper and a sandboxed preset.
PREPARE = (
    "Fetch {site}v0/prepare.md (for example with curl) and follow it to set up the folder you're "
    "running in for Discovery@Home donations, once: download the discover helper and write the "
    "{preset} permission preset. Ask before writing any settings, and don't start a donation."
)
PRESETS = ("donor", "donor-local", "donor-post")

SKILL_COMMAND = "/discover:contribute {repo} --minutes {minutes} --focus {focus} --permissions {permissions} --seed {seed}"


def donation_prompt(repo, minutes=60, focus="project", permissions="post", seed=None, site=None, drawn=None,
                    adapter_url=None):
    from . import SITE
    return TEMPLATE.format(site=site or SITE, repo_url=f"https://github.com/{repo}", minutes=minutes,
                           focus=FOCUS[focus], permissions=PERMISSIONS[permissions],
                           seed=seed or secrets.token_hex(16), drawn=DRAWN.format(**{**drawn, "method": drawn["method"].rstrip(". ")}) if drawn else "",
                           adapter=ADAPTER.format(adapter_url=adapter_url) if adapter_url else "")


def action_prompt(action, repo, minutes=60, permissions="local", site=None, adapter_url=None):
    from . import SITE
    return ACTIONS[action].format(site=site or SITE, repo_url=f"https://github.com/{repo}",
                                  minutes=minutes, permissions=PERMISSIONS[permissions],
                                  adapter=ADAPTER.format(adapter_url=adapter_url) if adapter_url else "")


def onboard_prompt(role, goal, repo, context=None, site=None):
    from . import SITE
    if goal not in GOALS[role]:
        raise ValueError(f"goal for a {role} must be one of {GOALS[role]}")
    return ONBOARD.format(site=site or SITE, role=role, goal=goal, repo_url=f"https://github.com/{repo}",
                          context=ONBOARD_CONTEXT.format(context=context) if context else "")


def start_prompt(problem, local=False, site=None):
    from . import SITE
    return START.format(site=site or SITE, problem=problem.strip(), mode=START_LOCAL if local else "")


def explore_prompt(minutes=240, permissions="local", interests=None, seed=None, site=None):
    from . import SITE
    return EXPLORE.format(site=site or SITE, minutes=minutes, permissions=PERMISSIONS[permissions],
                          seed=seed or secrets.token_hex(16),
                          interests=EXPLORE_INTERESTS.format(interests=interests) if interests else "")


def prepare_prompt(preset="donor", site=None):
    from . import SITE
    if preset not in PRESETS:
        raise ValueError(f"preset must be one of {PRESETS}")
    return PREPARE.format(site=site or SITE, preset=preset)


def skill_command(repo, minutes=60, focus="project", permissions="post", seed=None):
    return SKILL_COMMAND.format(repo=repo, minutes=minutes, focus=focus, permissions=permissions,
                                seed=seed or secrets.token_hex(16))


def templates(site=None):
    """Everything the explore page needs to build the same prompts client-side."""
    from . import SITE
    return {"site": site or SITE, "template": TEMPLATE, "drawn": DRAWN, "focus": FOCUS,
            "permissions": PERMISSIONS, "actions": ACTIONS, "skill_command": SKILL_COMMAND, "adapter": ADAPTER,
            "onboard": ONBOARD, "onboard_context": ONBOARD_CONTEXT, "goals": GOALS,
            "start": START, "start_local": START_LOCAL, "explore": EXPLORE, "explore_interests": EXPLORE_INTERESTS,
            "prepare": PREPARE}
