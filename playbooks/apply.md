---
name: apply
description: Apply to list a research project on a Discovery@Home hub, or nominate one you don't maintain. Use when the user says "list my project", "apply to the hub", "add my repo to Discovery@Home", "nominate this repo", or pastes a Discovery@Home apply prompt. Arguments - repo (owner/name or URL), optional notes.
---

# Apply to list a project

Listing puts a project in the hub's gallery, where donors choose what to work on. The
repo doesn't need to change anything to apply: if it doesn't follow the protocol's files
yet, the hub maps where things live in it before listing. Applying counts as the
maintainer's consent to be listed by this hub (spec §11.4).

Someone who doesn't maintain a project can **nominate** it instead (spec §11.5). A
nominated project is catalogued with its assessment but no contribution launcher, so
no agents are sent to it, and the hub never contacts its maintainers about it. It
becomes a full listing only if they add a consent record to their repo.

{{TOOLS}}

## 1. Confirm the basics

- The repository is **public** on GitHub.
- The person applying **maintains it**, or applies with a maintainer's agreement. If
  they don't, it's a **nomination**: never present a nomination as an application.
- Optionally, a quick check: does `AGENTS.md` or the README tell a newcomer what the
  project is and how to contribute? If not, suggest the **setup** playbook
  ({{SITE}}v0/setup.md) first. It isn't required.
- For an application, ask for the **credit policy** (how contributors will be credited)
  if the repo doesn't state one. A listing needs it before donors get a contribution
  launcher.
- For a nomination, check the project hasn't opted out (`"list": false` in its
  `discover.json` or `.github/discover-hubs.json`). If it has, stop.

## 2. Submit

The application is an issue on the hub, `{{HUB_REPO}}`, titled
`Add project: OWNER/NAME` (or `Nominate project: OWNER/NAME`), with this body:

```markdown
### Repository

https://github.com/OWNER/NAME

### Your relationship to the project

I maintain it

### Your GitHub handle

HANDLE

### Proposal issue on the project

_No response_

### Notes

ANYTHING REVIEWERS SHOULD KNOW: THE CREDIT POLICY IF THE REPO DOESN'T STATE IT, OR FOR A
NOMINATION, THE EVALUATION SUMMARY AS IS AND (IF PROPOSED) AFTER SETUP

### Confirmation

- [x] What I've said about my relationship to the project is accurate
```

For a nomination, the relationship line is `I'm nominating it; I don't maintain it`,
and the proposal line is the URL of the proposal issue, if there is one.

- With the helper and `gh`: `discover submit OWNER/NAME --contact HANDLE --notes "..."`,
  adding `--nominate --proposal URL` for a nomination.
- With `gh` only: `gh issue create -R {{HUB_REPO}} --title "Add project: OWNER/NAME"
  --body-file application.md`.
- With neither, or if you aren't permitted to post: give the person the title and body
  ready to paste, and the form at
  https://github.com/{{HUB_REPO}}/issues/new?template=add-project.yml

Ask before submitting: it's a public post.

## 3. What happens next

Within a minute, the hub's automation comments on the issue and opens a registry PR. If
the repo doesn't validate yet, the PR is labelled `needs-adapter`, and someone on the
hub assesses the repo and writes the mapping before a hub maintainer merges it. The
project appears in the gallery after the next site build: a nomination in the
catalogue section, without a launcher. Tell the person to watch the issue for questions.
