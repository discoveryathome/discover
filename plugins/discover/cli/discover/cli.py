"""discover: command-line tools for the Discovery@Home protocol."""

import argparse
import json
import re
import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path

from . import board as boardmod
from . import __version__, hub, init, pick, prompt, schema
from .project import Source, load_manifest
from .validate import format_report, normalize_catalog, validate

REPO_RE = re.compile(r"(?:https?://github\.com/)?([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+?)(?:\.git)?/?$")


def parse_repo(text):
    m = REPO_RE.match(text.strip())
    if not m:
        raise SystemExit(f"not a GitHub repo: {text!r} (use owner/name or a github.com URL)")
    return m.group(1)


def emit(obj, as_json, formatter):
    if as_json:
        print(json.dumps(obj, indent=2, ensure_ascii=False, default=str))
    else:
        print(formatter(obj))


def local_repo(path):
    """The canonical owner/name from a local checkout's discover.json."""
    manifest, _ = load_manifest(Source(local=path))
    if not manifest or "canonical_repo" not in manifest:
        raise SystemExit("no discover.json with canonical_repo here; pass --repo")
    return parse_repo(manifest["canonical_repo"])


def git_head(path="."):
    out = subprocess.run(["git", "-C", str(path), "rev-parse", "HEAD"], capture_output=True, text=True)
    return out.stdout.strip() if out.returncode == 0 else None


# --- commands ---------------------------------------------------------------

def cmd_validate(a):
    overlay = adapter = None
    if a.registry_entry:
        entry = json.loads(Path(a.registry_entry).read_text(encoding="utf-8"))
        overlay, adapter = entry.get("overlay"), entry.get("frontier_adapter")
        if not a.repo and not a.path_given:
            home = entry["repos"][0]
            a.repo, a.root = home["repo"], home.get("path", "")
    root = getattr(a, "root", "")
    source = Source(repo=parse_repo(a.repo), ref=a.ref, root=root) if a.repo else Source(local=a.path)
    r = validate(source, overlay, adapter)
    slim = {k: v for k, v in r.items() if k not in ("manifest", "frontier", "catalog")}
    emit(slim, a.json, lambda _: format_report(r))
    return 0 if r["conformant"] else 1


def cmd_init(a):
    repo = parse_repo(a.repo)
    r = init.scaffold(a.path, a.title, a.summary, [d.strip() for d in a.domains.split(",")],
                      a.maintainer, repo, a.github, a.minutes, a.profile)
    for c in r["created"]:
        print(f"created {c}")
    for s in r["skipped"]:
        print(f"skipped {s}")
    if r["agents_snippet"]:
        print("\nAdd this to AGENTS.md:\n\n" + r["agents_snippet"])
    print("\nNext: fill in the TODOs, then run `discover validate`.")
    return 0


def load_catalog(path):
    manifest, _ = load_manifest(Source(local=path))
    if not manifest or not manifest.get("catalog"):
        raise SystemExit("no discover.json with a catalog here")
    catalog = json.loads((Path(path) / manifest["catalog"]).read_text(encoding="utf-8"))
    return manifest, normalize_catalog(catalog)[0]


def live_board(repo, n):
    msgs, bad = boardmod.messages(boardmod.fetch_posts(repo, n))
    for b in bad:
        print(f"warning: malformed discover block at {b['url']}: {b['problems']}", file=sys.stderr)
    return boardmod.state(msgs)


def cmd_pick(a):
    manifest, catalog = load_catalog(a.path)
    b = None
    if a.live:
        try:
            b = live_board(a.repo or parse_repo(manifest["canonical_repo"]), a.discussions)
        except Exception as e:
            print(f"warning: live board unavailable ({e}); suggestions ignore claims", file=sys.stderr)
    r = pick.pick(catalog, a.seed, a.track, a.task, b, a.count)
    r["base"] = git_head(a.path)
    r["priority_revision"] = catalog.get("priority_revision")
    emit(r, a.json, pick.format_pick)
    return 0


def cmd_board(a):
    repo = parse_repo(a.repo) if a.repo else local_repo(a.path)
    s = live_board(repo, a.discussions)
    emit(s, a.json, boardmod.format_state)
    return 0


def cmd_post(a):
    repo = parse_repo(a.repo) if a.repo else local_repo(a.path)
    payload = {"v": 0, "kind": a.kind, "scope": a.scope, "base": a.base or git_head(a.path) or "unknown",
               "posted_at": boardmod.now().isoformat(timespec="seconds").replace("+00:00", "Z")}
    optional = {"task": a.task, "scope_key": a.scope_key, "scope_status": a.scope_status,
                "priority_revision": a.priority_revision, "replaces": a.replaces,
                "responds_to": a.responds_to, "evidence_level": a.evidence_level,
                "artifact": a.artifact, "reason": a.reason}
    payload.update({k: v for k, v in optional.items() if v is not None})
    if a.predecessor:
        payload["predecessors"] = a.predecessor
    if a.kind == "claim":
        until = boardmod.now() + timedelta(minutes=a.expires_in)
        payload["expires"] = until.isoformat(timespec="seconds").replace("+00:00", "Z")
    if a.kind == "handoff":
        req = {"question": a.question, "first_step": a.first_step}
        req.update({k: v for k, v in {"success_test": a.success_test, "track": a.track,
                                      "est_minutes": a.est_minutes}.items() if v is not None})
        payload["request"] = req
    problems = schema.check("message.schema.json", payload)
    if problems:
        raise SystemExit("message invalid:\n  " + "\n  ".join(problems))
    prose = Path(a.body_file).read_text(encoding="utf-8") if a.body_file else f"**{a.kind.upper()}:** {a.scope}"
    body = boardmod.render(payload, prose)
    if a.dry_run:
        print(body)
        return 0
    if not a.discussion:
        raise SystemExit("--discussion is required unless --dry-run")
    print(boardmod.post(repo, a.discussion, body, a.reply_to))
    return 0


def cmd_prompt(a):
    repo = parse_repo(a.repo)
    if a.action != "contribute":
        print(prompt.action_prompt(a.action, repo, a.minutes, a.permissions))
        return 0
    seed = a.seed or __import__("secrets").token_hex(16)
    print(prompt.donation_prompt(repo, a.minutes, a.focus, a.permissions, seed=seed))
    print("\nWith the discover plugin installed:\n  " + prompt.skill_command(repo, a.minutes, a.focus, a.permissions, seed))
    return 0


def cmd_hub(a):
    data = hub.build(a.registry, a.out, a.board)
    print(f"wrote {a.out}: {len(data['projects'])} projects, {len(data['problems'])} problems")
    return 1 if a.strict and data["problems"] else 0




def parse_issue_form(body):
    """GitHub issue forms render as '### Label\\n\\nvalue' sections."""
    out = {}
    for label, value in re.findall(r"^### (.+?)\s*\n(.*?)(?=^### |\Z)", body, re.S | re.M):
        value = value.strip()
        out[label.strip()] = "" if value == "_No response_" else value
    return out


def cmd_registry_add(a):
    fields = parse_issue_form(Path(a.body_file).read_text(encoding="utf-8")) if a.body_file else {}
    repo = parse_repo(a.repo or fields.get("Repository", ""))
    contact = (a.contact or fields.get("Maintainer GitHub handle", "")).lstrip("@") or None
    slug = re.sub(r"[^a-z0-9-]+", "-", repo.split("/")[1].lower()).strip("-")
    out = Path(a.out) / f"{slug}.json"
    if out.exists():
        raise SystemExit(f"{out} already exists")
    today = date.today().isoformat()
    # Submitting through the hub's form counts as consent to be listed (spec §11.4).
    entry = {"repos": [{"repo": repo}], "added_on": today,
             "consent": {"source": "application", "checked_on": today, "list": True, "push": []}}
    if contact:
        entry["contact"] = contact
    errs = schema.check("registry-entry.schema.json", entry)
    if errs:
        raise SystemExit("entry invalid: " + "; ".join(errs))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(entry, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"slug": slug, "path": str(out), "repo": repo}))
    return 0


def cmd_submit(a):
    from . import HUB_REPO
    repo = parse_repo(a.repo)
    body = (f"### Repository\n\nhttps://github.com/{repo}\n\n"
            f"### Maintainer GitHub handle\n\n{a.contact or '_No response_'}\n\n"
            f"### Notes\n\n{a.notes or '_No response_'}\n\n"
            "### Maintainer confirmation\n\n- [x] I maintain this project and will review contributions to it\n")
    args = ["gh", "issue", "create", "-R", a.hub, "--title", f"Add project: {repo}", "--body", body]
    if a.dry_run:
        print(body)
        return 0
    out = subprocess.run(args, capture_output=True, text=True)
    if out.returncode != 0:
        raise SystemExit(f"gh issue create failed: {out.stderr.strip()}")
    print(out.stdout.strip())
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(prog="discover", description=__doc__)
    p.add_argument("--version", action="version", version=f"discover {__version__}")
    sub = p.add_subparsers(dest="cmd", required=True)

    v = sub.add_parser("validate", help="check a project's files and which conventions it follows")
    v.add_argument("path", nargs="?", default=".")
    v.add_argument("--repo", help="validate a GitHub repo (owner/name) instead of a local path")
    v.add_argument("--ref", default="HEAD")
    v.add_argument("--registry-entry", help="apply a registry entry's overlay/adapter")
    v.add_argument("--json", action="store_true")
    v.set_defaults(func=cmd_validate)

    i = sub.add_parser("init", help="scaffold protocol files in a repo (never overwrites)")
    i.add_argument("path", nargs="?", default=".")
    i.add_argument("--title", required=True)
    i.add_argument("--summary", required=True)
    i.add_argument("--domains", required=True, help="comma-separated")
    i.add_argument("--maintainer", required=True)
    i.add_argument("--github")
    i.add_argument("--repo", required=True, help="canonical owner/name")
    i.add_argument("--minutes", type=int, default=60)
    i.add_argument("--profile", default="review-only",
                   choices=["formal-proof", "exact-certificate", "benchmark", "replication", "review-only"])
    i.set_defaults(func=cmd_init)

    k = sub.add_parser("pick", help="suggest tasks from the local catalogue")
    k.add_argument("path", nargs="?", default=".")
    k.add_argument("--seed")
    k.add_argument("--track")
    k.add_argument("--task")
    k.add_argument("--count", type=int, default=3)
    k.add_argument("--live", action="store_true", help="read claims/handoffs from Discussions via gh")
    k.add_argument("--repo", help="override canonical repo for --live")
    k.add_argument("--discussions", type=int, default=50)
    k.add_argument("--json", action="store_true")
    k.set_defaults(func=cmd_pick)

    b = sub.add_parser("board", help="live claims and open handoffs from Discussions")
    b.add_argument("path", nargs="?", default=".")
    b.add_argument("--repo")
    b.add_argument("--discussions", type=int, default=50)
    b.add_argument("--json", action="store_true")
    b.set_defaults(func=cmd_board)

    o = sub.add_parser("post", help="post a coordination message to a Discussion")
    o.add_argument("kind", choices=["claim", "finding", "handoff", "done", "released"])
    o.add_argument("--scope", required=True)
    o.add_argument("--path", default=".")
    o.add_argument("--repo")
    o.add_argument("--discussion", type=int)
    o.add_argument("--reply-to", help="URL of the comment to reply to")
    o.add_argument("--body-file", help="Markdown prose to precede the block")
    o.add_argument("--task")
    o.add_argument("--scope-key")
    o.add_argument("--scope-status", choices=["unchanged", "refined", "changed"])
    o.add_argument("--base")
    o.add_argument("--priority-revision", type=int)
    o.add_argument("--expires-in", type=int, default=120, help="claim lifetime in minutes")
    o.add_argument("--replaces")
    o.add_argument("--responds-to")
    o.add_argument("--evidence-level", choices=["local-only", "author-checked", "independently-checked"])
    o.add_argument("--artifact")
    o.add_argument("--predecessor", action="append")
    o.add_argument("--reason")
    o.add_argument("--question")
    o.add_argument("--first-step")
    o.add_argument("--success-test")
    o.add_argument("--track")
    o.add_argument("--est-minutes", type=int)
    o.add_argument("--dry-run", action="store_true")
    o.set_defaults(func=cmd_post)

    r = sub.add_parser("prompt", help="print a donation prompt for a project")
    r.add_argument("repo")
    r.add_argument("--minutes", type=int, default=60)
    r.add_argument("--focus", choices=list(prompt.FOCUS), default="project")
    r.add_argument("--permissions", choices=list(prompt.PERMISSIONS), default="post")
    r.add_argument("--action", choices=["contribute", *prompt.ACTIONS], default="contribute",
                   help="which playbook the prompt points to")
    r.add_argument("--seed", help="32 hex digits; default: fresh OS randomness")
    r.set_defaults(func=cmd_prompt)

    h = sub.add_parser("hub", help="build the explore page data from the registry")
    h.add_argument("--registry", default="registry/projects")
    h.add_argument("--out", default="site/data/projects.json")
    h.add_argument("--board", action="store_true", help="include live board snapshots (needs gh)")
    h.add_argument("--strict", action="store_true", help="exit nonzero on any problem")
    h.set_defaults(func=cmd_hub)

    g = sub.add_parser("registry-add", help="create a registry entry (from flags or an issue-form body)")
    g.add_argument("--repo")
    g.add_argument("--contact")
    g.add_argument("--body-file")
    g.add_argument("--out", default="registry/projects")
    g.set_defaults(func=cmd_registry_add)

    s = sub.add_parser("submit", help="request listing on the hub (opens an add-project issue)")
    s.add_argument("repo")
    s.add_argument("--contact", help="maintainer GitHub handle")
    s.add_argument("--notes")
    s.add_argument("--hub", default=__import__("discover").HUB_REPO)
    s.add_argument("--dry-run", action="store_true")
    s.set_defaults(func=cmd_submit)

    a = p.parse_args(argv)
    a.path_given = "path" in a and a.path != "."
    return a.func(a)
