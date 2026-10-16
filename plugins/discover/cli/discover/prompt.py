"""Donation prompts. The explore page uses the same templates via site/data/prompts.json."""

FOCUS = {
    "project": "Choose useful work according to the repository's current priorities, preferring an open handoff on the drawn track.",
    "audit": "Prioritize independent verification and auditing of pending or accepted claims.",
    "explore": "Prioritize exploring a genuinely new approach, priced against a favorable best case first.",
}

PERMISSIONS = {
    "post": "You may post routine claims, findings and handoffs in the project's Discussions and open one focused PR without asking me again for each action.",
    "local": "Do not post publicly or open PRs; leave a local handoff note I can review and publish myself.",
}

TEMPLATE = (
    "Contribute one useful, independently reviewable result to {repo_url}. "
    "Read AGENTS.md and the project's entry doc from the current default branch first, and its discover.json if present. "
    "Use the repository's task-selection and overlap process unless I assign a specific task. "
    "Work for about {minutes} minutes, keeping the final quarter for verification and a concise handoff. "
    "{focus} "
    "Report the exact scope, evidence, what was not checked, and predecessor credit. "
    "{permissions} "
    "Do not merge, close others' PRs, or change the project's frontier record."
)

SKILL_COMMAND = "/discover:contribute {repo} --minutes {minutes} --focus {focus} --permissions {permissions}"


def donation_prompt(repo, minutes=60, focus="project", permissions="post"):
    return TEMPLATE.format(repo_url=f"https://github.com/{repo}", minutes=minutes,
                           focus=FOCUS[focus], permissions=PERMISSIONS[permissions])


def skill_command(repo, minutes=60, focus="project", permissions="post"):
    return SKILL_COMMAND.format(repo=repo, minutes=minutes, focus=focus, permissions=permissions)


def templates():
    """Everything the explore page needs to build the same prompts client-side."""
    return {"template": TEMPLATE, "focus": FOCUS, "permissions": PERMISSIONS, "skill_command": SKILL_COMMAND}
