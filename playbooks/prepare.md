---
name: prepare
description: Set up the folder the agent is running in for Discovery@Home donations, once - download the discover helper and write a sandboxed permission preset, so later sessions there are sandboxed and limited on GitHub without any launch flags. Use when the user says "set up this folder for donating", "sandbox my donation sessions", or pastes a Discovery@Home setup prompt. Arguments - preset (donor, donor-local or donor-post).
---

# Set up this folder for donating

The person wants later donated sessions in this folder to run safely without thinking
about it: commands sandboxed, credential files unreadable, the repo's own hooks off, and
GitHub writes limited to what they chose. Your job is a one-time setup that takes a
couple of minutes: the helper and a permission preset in this folder. You change nothing
outside it, and you don't start a donation in this session.

{{TOOLS}}

## 0. Which folder

The folder you were started in, with three exceptions:

- **The home folder:** propose `~/discover-work` instead (or another folder they name).
  Create it, set it up, and tell them to start their agent from there from now on.
- **A clone of a project they keep for contributing:** set it up in place. The preset
  goes in `.claude/settings.local.json`; check git ignores it (`git check-ignore
  .claude/settings.local.json`), and if not, add it to `.git/info/exclude`. Never commit
  it.
- **A checkout of a project they maintain:** a donor preset is the wrong one there. Say
  so and offer the maintainer preset instead (`discover permissions maintainer`).

## 1. Which preset

Take it from the prompt; otherwise ask once, recommending the first:

- **`donor`**: for sessions they watch. Sandboxed; each post or PR asks them first.
- **`donor-local`**: for unattended sessions that do nothing public.
- **`donor-post`**: for unattended sessions allowed to post coordination messages and
  open one focused PR.

You know which agent you are. Claude Code writes `.claude/settings.local.json`; Codex
writes `.codex/` in this folder.

## 2. Get the helper

Download the helper into this folder and check its hash, as in the helper section above.
The preset needs Python 3.9 or later; without it, say so, give them the install link
for their system (https://www.python.org/downloads/), and stop.

## 3. Write the preset (ask first)

Show the exact command and ask before running it:

```sh
python3 discover.pyz permissions PRESET --write .claude/settings.local.json   # Claude Code
python3 discover.pyz permissions PRESET --agent codex --write .               # Codex
```

It merges into an existing settings file and keeps what's there. Your own permission
checks may ask the person to approve a write under `.claude/`: that's expected. If they
refuse it anyway, don't work around it: give the person the command to run themselves
(in Claude Code, typing `! ` before it runs it in the session).

## 4. Report and hand over

Tell the person, in a few lines:

- What was written, from the command's output, and where.
- **Whether sessions here will be sandboxed.** If the command printed a warning (native
  Windows, or Linux without bubblewrap and socat), repeat it with its install steps
  word for word. Don't call the folder sandboxed if it isn't.
- **Next:** settings load when the agent starts, so they should exit and start it again
  in this folder (`claude`, nothing else). In Claude Code, `/sandbox` shows whether the
  sandbox is on. Codex: start `codex` here once and accept the trust prompt. Then paste
  a donation prompt from {{SITE}}#/contribute.
- In a kept clone: rerun the command after a pull that adds MCP servers (the command
  names any it turns off).
- To undo: delete `.claude/settings.local.json` (or the lines the command listed), or
  `.codex/` for Codex.

Don't start a donation in this same session: the preset isn't active until the agent
restarts.
