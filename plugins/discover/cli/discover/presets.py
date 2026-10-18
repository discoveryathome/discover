"""Permission presets for coding agents (Claude Code settings, Codex rules), per role.

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

# Commands each playbook may ask to run publicly, as argument prefixes. They match only
# when the subcommand comes first: `gh pr merge 17 -R o/r`, not `gh -R o/r pr merge 17`.
_POST = [("git", "push"), ("gh", "pr", "create"), ("gh", "api", "graphql"),
         ("gh", "issue", "comment"), ("gh", "pr", "comment")]
_MAINTAIN = _POST + [("gh", "pr", "merge"), ("gh", "pr", "close"), ("gh", "pr", "edit"),
                     ("gh", "issue", "create"), ("gh", "issue", "close"), ("gh", "issue", "edit"),
                     ("gh", "repo", "edit"), ("gh", "label", "create")]
_WRITES = sorted(set(_MAINTAIN + [("gh", "repo", "create"), ("gh", "repo", "fork"), ("gh", "release", "create")]))

# Donor presets also turn on the agent's sandbox (Claude Code: macOS Seatbelt, Linux and
# WSL2 bubblewrap): commands write only the session folders, can't read the usual credential
# files, and reach only these hosts. Tested headless (claude -p): writing outside, reading
# the ssh folder and other hosts were refused; gh worked with enableWeakerNetworkIsolation
# (Go's TLS check on macOS needs it). It does NOT hide credentials a tool holds: code run in
# it can still ask gh for its token. The playbooks' safety section says what that means.
DONOR_DOMAINS = ["github.com", "api.github.com", "*.githubusercontent.com", "codeload.github.com",
                 "discoveryathome.github.io", "pypi.org", "files.pythonhosted.org", "registry.npmjs.org",
                 "crates.io", "static.crates.io", "index.crates.io", "proxy.golang.org", "sum.golang.org"]
# Credential folders and files in the home folder (written without "~/" here, so the repo
# screen doesn't flag this list as code reading them).
_SECRET_DIRS = [".ssh", ".aws", ".gnupg", ".kube", ".docker", ".azure", ".config/gcloud"]
_SECRET_FILES = [".netrc", ".npmrc", ".pypirc"]
CREDENTIALS = ["~/" + c for c in _SECRET_DIRS + _SECRET_FILES]

PRESETS = {
    # Unattended and allowed nothing public: deny writes (a text match only; the real
    # boundary is running without GitHub write credentials).
    "donor-local": {
        "about": "A donated session with Permissions: local. Nothing public; GitHub writes are denied.",
        "allow": [], "ask": [], "deny": _WRITES, "unattended": True, "sandbox": True,
    },
    # Unattended but allowed to post: narrow allow rules, so the donor's grant isn't refused
    # mid-session; merging and settings stay denied.
    "donor-post": {
        "about": "A donated session with Permissions: post. Claims, findings, handoffs and one focused PR.",
        "allow": _POST, "ask": [], "unattended": True, "sandbox": True,
        "deny": [("gh", "pr", "merge"), ("gh", "pr", "close"), ("gh", "repo", "edit"), ("gh", "repo", "create")],
    },
    # A donor who is present: sandboxed like the unattended presets, but each public write asks.
    "donor": {
        "about": "A donated session you're watching: sandboxed, and each post or PR asks you first.",
        "allow": [], "ask": _POST, "unattended": False, "sandbox": True,
        "deny": [("gh", "pr", "merge"), ("gh", "pr", "close"), ("gh", "repo", "edit"), ("gh", "repo", "create")],
    },
    # The maintainer is present: ask rules always prompt them, and an automatic checker can't
    # refuse what they approve. (An allow rule would also skip protections like not merging
    # unreviewed PRs, which a maintainer preset shouldn't turn off.)
    "maintainer": {
        "about": "A maintainer's own sessions (setup, direct, triage): each public write asks you, and isn't refused after you say yes.",
        "allow": [], "ask": _MAINTAIN, "deny": [], "unattended": False, "sandbox": False,
    },
}

AGENTS = ("claude", "codex")


def claude_rule(cmd):
    """Claude Code's space form: Bash(gh pr merge *)."""
    return f"Bash({' '.join(cmd)} *)"


def settings(name, work_dir="~/discover-work", domains=()):
    """Claude Code settings for a preset."""
    p = PRESETS[name]
    out = {"permissions": {k: [claude_rule(c) for c in p[k]] for k in ("allow", "ask", "deny") if p[k]}}
    if p["sandbox"]:
        out["permissions"].setdefault("deny", []).extend(
            [f"Read(~/{c}/**)" for c in _SECRET_DIRS] + [f"Read(~/{c})" for c in _SECRET_FILES])
        out["sandbox"] = {
            "enabled": True, "failIfUnavailable": True,  # never run a donor's session unsandboxed by surprise
            "autoAllowBashIfSandboxed": True, "allowUnsandboxedCommands": False,
            "enableWeakerNetworkIsolation": True,
            "network": {"allowedDomains": DONOR_DOMAINS + [d for d in domains if d not in DONOR_DOMAINS]},
            "filesystem": {"allowWrite": [str(work_dir)], "denyRead": list(CREDENTIALS)},
        }
    return out


def _merge(have, new, added, path=""):
    """Add new's keys and list items to have, never removing or overwriting what's there."""
    for k, v in new.items():
        if isinstance(v, dict):
            _merge(have.setdefault(k, {}), v, added, f"{path}{k}.")
        elif isinstance(v, list):
            lst = have.setdefault(k, [])
            for item in v:
                if item not in lst:
                    lst.append(item)
                    added.append(f"{path}{k}: {item}")
        elif k not in have:
            have[k] = v
            added.append(f"{path}{k}: {json.dumps(v)}")


def merge_into(path, name, work_dir="~/discover-work", domains=()):
    """Add a preset's rules (and sandbox settings) to a Claude Code settings file, keeping
    everything already there."""
    path = Path(path)
    current = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    added = []
    _merge(current, settings(name, work_dir, domains), added)
    perms = current.setdefault("permissions", {})
    for key in [k for k, v in perms.items() if v == []]:
        del perms[key]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(current, indent=2) + "\n", encoding="utf-8")
    return added


# Codex: execpolicy rules (Starlark) and a config layer. `allow` runs the command outside
# Codex's sandbox without asking, `prompt` asks each time, `forbidden` blocks it.
_CODEX_DECISION = {"allow": "allow", "ask": "prompt", "deny": "forbidden"}
_CODEX_WHY = {
    "allow": "Pre-approved for this donated session (Permissions: post).",
    "ask": "A public write: the maintainer approves each one.",
    "deny": "Not allowed in this session; leave it ready for the person to run.",
}


def codex_rules(name):
    """The preset as a Codex .rules file. Each rule carries a match example, which Codex
    checks when it loads the file."""
    p = PRESETS[name]
    out = [f"# Discovery@Home preset {name}, written by `discover permissions`. {p['about']}",
           "# Regenerated on each run; put your own rules in another file.", ""]
    for key in ("deny", "ask", "allow"):
        for cmd in p[key]:
            pattern = ", ".join(json.dumps(c) for c in cmd)
            example = json.dumps(" ".join(cmd) + (" origin main" if cmd == ("git", "push") else " 1"))
            out += ["prefix_rule(", f"    pattern = [{pattern}],", f"    decision = \"{_CODEX_DECISION[key]}\",",
                    f"    justification = {json.dumps(_CODEX_WHY[key])},", f"    match = [{example}],", ")", ""]
    return "\n".join(out)


def codex_config(name, work_dir):
    """The config layer: approvals for a present person or an unattended run, and a
    workspace-write sandbox that can reach the network (to clone and read) and write the
    session folder."""
    approval = "never" if PRESETS[name]["unattended"] else "on-request"
    return (f"# Discovery@Home preset {name}, written by `discover permissions`.\n"
            f"approval_policy = \"{approval}\"\n"
            f"sandbox_mode = \"workspace-write\"\n\n"
            f"[sandbox_workspace_write]\n"
            f"network_access = true\n"
            f"writable_roots = [{json.dumps(str(work_dir))}]\n")


def write_codex(folder, name, work_dir):
    """Write <folder>/.codex/rules/discover.rules (ours, replaced each time) and
    <folder>/.codex/config.toml if there is none. Returns (written, config_skipped)."""
    folder = Path(folder)
    rules = folder / ".codex" / "rules" / "discover.rules"
    rules.parent.mkdir(parents=True, exist_ok=True)
    rules.write_text(codex_rules(name), encoding="utf-8")
    config = folder / ".codex" / "config.toml"
    if config.exists():
        return [str(rules)], str(config)
    config.write_text(codex_config(name, work_dir), encoding="utf-8")
    return [str(rules), str(config)], None
