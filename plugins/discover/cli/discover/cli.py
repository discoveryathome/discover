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
from .validate import catalogued, format_report, normalize_catalog, validate

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
    if a.pilot:
        from .hubcheck import parse_pilot
        block, problems = parse_pilot(Path(a.pilot).read_text(encoding="utf-8"))
        emit({"valid": not problems, "problems": problems, "verdict": (block or {}).get("verdict")}, a.json,
             lambda r: "pilot record valid: verdict " + r["verdict"] if r["valid"]
             else "pilot record invalid:\n" + "\n".join(f"  {x}" for x in r["problems"]))
        return 0 if not problems else 1
    overlay = adapter = frontier_doc = None
    entry = {}
    if a.registry_entry:
        from . import adapter as adaptermod
        entry = json.loads(Path(a.registry_entry).read_text(encoding="utf-8"))
        overlay, adapter, block, problems = adaptermod.for_entry(entry, adaptermod.hub_root(a.registry_entry))
        if problems:
            raise SystemExit("adapter: " + "; ".join(problems))
        frontier_doc = (block or {}).get("frontier_doc")
        if not a.repo and not a.path_given:
            home = entry["repos"][0]
            a.repo, a.root = home["repo"], home.get("path", "")
    root = getattr(a, "root", "")
    source = Source(repo=parse_repo(a.repo), ref=a.ref, root=root) if a.repo else Source(local=a.path)
    r = validate(source, overlay, adapter, catalogued(entry), frontier_doc)
    slim = {k: v for k, v in r.items() if k not in ("manifest", "frontier", "catalog", "table_rows", "history")}
    emit(slim, a.json, lambda _: format_report(r))
    return 0 if r["conformant"] else 1


def cmd_signals(a):
    from datetime import date
    from . import signals
    data = json.loads(Path(a.data).read_text(encoding="utf-8"))
    r = signals.sweep(data, date.fromisoformat(a.today) if a.today else None)
    emit(r, a.json, signals.format_sweep)
    return 0


def cmd_screen(a):
    from . import screen
    findings = screen.screen(a.path)
    emit({"path": a.path, "findings": findings}, a.json, lambda _: screen.format_report(findings, a.path))
    return 2 if any(f["severity"] == "high" for f in findings) else 0


def cmd_init(a):
    repo = parse_repo(a.repo)
    r = init.scaffold(a.path, a.title, a.summary, [d.strip() for d in a.domains.split(",")],
                      a.maintainer, repo, a.github, a.minutes, a.profile, a.entry)
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


def load_table(path, manifest):
    """The frontier's record table (spec §5) and its rows, or (None, None)."""
    from . import table as tablemod
    source = Source(local=path)
    frontier = source.read_json(manifest["frontier"]) if manifest.get("frontier") else None
    tbl = (frontier or {}).get("table")
    if not tbl:
        return None, None
    rows, problem = tablemod.load(source, tbl)
    if problem:
        print(f"warning: {problem}", file=sys.stderr)
    return tbl, rows


def live_board(repo, n):
    msgs, bad = boardmod.messages(boardmod.fetch_posts(repo, n))
    for b in bad:
        print(f"warning: malformed discover block at {b['url']}: {b['problems']}", file=sys.stderr)
    return boardmod.state(msgs)


def cmd_pick(a):
    manifest, catalog = load_catalog(a.path)
    if manifest.get("picker") and not a.task:
        # The project's own picker is authoritative (spec §7); never name a card for it.
        seed = a.seed or __import__("secrets").token_hex(16)
        cmd = " ".join(t.replace("{seed}", seed) for t in manifest["picker"]["command"])
        print(f"This project uses its own picker. From the repo root, run:\n  {cmd}")
        return 0
    b = None
    if a.live:
        try:
            b = live_board(a.repo or parse_repo(manifest["canonical_repo"]), a.discussions)
        except Exception as e:
            print(f"warning: live board unavailable ({e}); suggestions ignore claims", file=sys.stderr)
    table, rows = load_table(a.path, manifest)
    r = pick.pick(catalog, a.seed, a.track, a.task, b, a.count, table=table, rows=rows)
    r["base"] = git_head(a.path)
    r["priority_revision"] = catalog.get("priority_revision")
    emit(r, a.json, pick.format_pick)
    return 0


def load_agent_index(where):
    """agents.json from a path or URL (default: the hub's site)."""
    from . import SITE
    where = where or f"{SITE}data/agents.json"
    if re.match(r"https?://", where):
        import urllib.request
        with urllib.request.urlopen(where, timeout=30) as r:
            return json.loads(r.read().decode("utf-8"))
    return json.loads(Path(where).read_text(encoding="utf-8"))


def cmd_choose(a):
    index = load_agent_index(a.data)
    interests = [i for i in (a.interests or "").split(",") if i.strip()]
    r = pick.choose_project(index["projects"], a.seed, interests, a.round)
    p = r["project"]
    # A Stage 0 project, or one whose manifest doesn't allow posting, gets a local session.
    perms = a.permissions if a.permissions == "local" or p["sessions"]["post_messages"] else "local"
    r["permissions"] = perms
    if a.action == "verify":
        r["prompt"] = prompt.action_prompt("verify", p["repo"], a.minutes, perms, adapter_url=p.get("adapter_url"))
    else:
        r["prompt"] = prompt.donation_prompt(p["repo"], a.minutes, a.focus, perms, seed=r["round_seed"],
                                             adapter_url=p.get("adapter_url"))

    def fmt(r):
        lines = [f"seed {r['seed']}  round {r['round']}", f"chosen: {p['slug']} ({p['repo']}), stage {p['stage']}",
                 f"  weight {r['weight']} of {r['total_weight']} across {', '.join(r['pool'])}",
                 f"  {p['title']}: {p['summary']}"]
        if r["note"]:
            lines.append(f"  {r['note']}")
        if perms != a.permissions:
            lines.append("  This project takes local sessions only for now, so the prompt says Permissions: local.")
        lines += ["", "Prompt for the session (it draws its task from the round's seed):", r["prompt"]]
        return "\n".join(lines)
    emit(r, a.json, fmt)
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
    if a.action == "start":
        text = Path(a.problem_file).read_text(encoding="utf-8") if a.problem_file else a.problem
        if not text:
            raise SystemExit("--action start needs --problem TEXT or --problem-file PATH")
        print(prompt.start_prompt(text, a.local))
        return 0
    if a.action == "explore":
        print(prompt.explore_prompt(a.minutes, a.permissions, a.interests, a.seed))
        return 0
    if a.action == "prepare":
        print(prompt.prepare_prompt(a.preset))
        return 0
    if a.action == "curate":
        print(prompt.curate_prompt())
        return 0
    if not a.repo:
        raise SystemExit("a repository (owner/name) is required for this action")
    repo = parse_repo(a.repo)
    if a.action == "onboard":
        try:
            print(prompt.onboard_prompt(a.role, a.goal or prompt.GOALS[a.role][-1], repo, a.context))
        except ValueError as e:
            raise SystemExit(str(e))
        return 0
    if a.action != "contribute":
        print(prompt.action_prompt(a.action, repo, a.minutes, a.permissions))
        return 0
    seed = a.seed or __import__("secrets").token_hex(16)
    print(prompt.donation_prompt(repo, a.minutes, a.focus, a.permissions, seed=seed))
    print("\nWith the discover plugin installed:\n  " + prompt.skill_command(repo, a.minutes, a.focus, a.permissions, seed))
    return 0


def cmd_hub(a):
    data = hub.build(a.registry, a.out, a.board, with_history=a.history)
    print(f"wrote {a.out}: {len(data['projects'])} projects, {len(data['problems'])} problems")
    return 1 if a.strict and data["problems"] else 0




def parse_issue_form(body):
    """GitHub issue forms render as '### Label\\n\\nvalue' sections."""
    out = {}
    for label, value in re.findall(r"^### (.+?)\s*\n(.*?)(?=^### |\Z)", body, re.S | re.M):
        value = value.strip()
        out[label.strip()] = "" if value == "_No response_" else value
    return out


NOMINATING = "nominat"  # matches the form's "I'm nominating it" option


def cmd_registry_add(a):
    fields = parse_issue_form(Path(a.body_file).read_text(encoding="utf-8")) if a.body_file else {}
    repo = parse_repo(a.repo or fields.get("Repository", ""))
    handle = (a.contact or fields.get("Your GitHub handle") or fields.get("Maintainer GitHub handle") or "").lstrip("@") or None
    nominated = a.nominate or NOMINATING in fields.get("Your relationship to the project", "").lower()
    proposal = a.proposal or fields.get("Proposal issue on the project") or None
    today = date.today().isoformat()
    clean = lambda t: re.sub(r"[^a-z0-9-]+", "-", t.lower()).strip("-")
    entries = {f.stem: json.loads(f.read_text(encoding="utf-8")) for f in sorted(Path(a.out).glob("*.json"))}
    same = [k for k, e in entries.items() if any(r.get("repo", "").lower() == repo.lower() for r in e.get("repos", []))]
    result = {"repo": repo, "nominated": bool(nominated), "branch": "registry/" + clean(repo.replace("/", "-"))}
    if same:
        # Already in the registry. A maintainer applying for a nominated project records consent
        # on the existing entry; anything else is a duplicate (spec §11.5).
        slug, entry = same[0], entries[same[0]]
        if nominated or (entry.get("consent") or {}).get("list"):
            print(json.dumps({**result, "slug": slug, "mode": "duplicate"}))
            return 0
        entry["consent"] = {"source": "application", "checked_on": today, "list": True, "push": []}
        if handle:
            entry["contact"] = handle
        if a.intake:
            entry["intake"] = a.intake
        mode = "consent"
    else:
        slug = clean(repo.split("/")[1])
        if slug in entries:  # same name, different owner
            slug = clean(repo.replace("/", "-"))
        entry, mode = None, "add"
    out = Path(a.out) / f"{slug}.json"
    if entry is not None:
        out.write_text(json.dumps(entry, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(json.dumps({**result, "slug": slug, "path": str(out), "mode": mode}))
        return 0
    entry = {"repos": [{"repo": repo}], "added_on": today}
    if a.intake:
        entry["intake"] = a.intake
    if nominated:
        # A nomination isn't consent: catalogued, no launcher, no contact (spec §11.5).
        if not handle:
            raise SystemExit("a nomination needs the nominator's GitHub handle")
        entry["nomination"] = {"by": handle, "on": today, **({"proposal": proposal} if proposal else {})}
    else:
        # A maintainer submitting through the hub's form consents to be listed (spec §11.4).
        entry["consent"] = {"source": "application", "checked_on": today, "list": True, "push": []}
        if handle:
            entry["contact"] = handle
    errs = schema.check("registry-entry.schema.json", entry)
    if errs:
        raise SystemExit("entry invalid: " + "; ".join(errs))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(entry, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({**result, "slug": slug, "path": str(out), "mode": mode}))
    return 0


def application_body(repo, handle, notes=None, nominate=False, proposal=None):
    """The hub's add-project issue form, filled in (.github/ISSUE_TEMPLATE/add-project.yml)."""
    rel = "I'm nominating it; I don't maintain it" if nominate else "I maintain it"
    none = "_No response_"
    return (f"### Repository\n\nhttps://github.com/{repo}\n\n"
            f"### Your relationship to the project\n\n{rel}\n\n"
            f"### Your GitHub handle\n\n{handle or none}\n\n"
            f"### Proposal issue on the project\n\n{proposal or none}\n\n"
            f"### Notes\n\n{notes or none}\n\n"
            "### Confirmation\n\n- [x] What I've said about my relationship to the project is accurate\n")


def cmd_submit(a):
    repo = parse_repo(a.repo)
    body = application_body(repo, a.contact, a.notes, a.nominate, a.proposal)
    title = f"{'Nominate' if a.nominate else 'Add'} project: {repo}"
    args = ["gh", "issue", "create", "-R", a.hub, "--title", title, "--body", body]
    if a.dry_run:
        print(title + "\n\n" + body)
        return 0
    out = subprocess.run(args, capture_output=True, text=True)
    if out.returncode != 0:
        raise SystemExit(f"gh issue create failed: {out.stderr.strip()}")
    print(out.stdout.strip())
    return 0


def cmd_adapter_check(a):
    import subprocess
    from . import adapter as adaptermod
    text = Path(a.file).read_text(encoding="utf-8")
    block, _ = adaptermod.parse(text)
    repo = a.repo or (block or {}).get("repo")
    if a.path:
        def at(commit):
            return GitSource(a.path, commit)

        def changed(commit, paths):
            out = subprocess.run(["git", "-C", a.path, "diff", "--name-only", f"{commit}..HEAD", "--", *paths],
                                 capture_output=True, text=True)
            return out.stdout.split() if out.returncode == 0 else None
    else:
        def at(commit):
            return Source(repo=parse_repo(repo), ref=commit or "HEAD")
        changed = None
    r = adaptermod.check(text, at, changed)
    emit(r, a.json, adaptermod.format_check)
    return 1 if r["problems"] else 0


def cmd_permissions(a):
    from . import presets
    if a.agent == "codex":
        work = a.work_dir
        if not a.write:
            print(f"# {presets.PRESETS[a.preset]['about']}\n# .codex/rules/discover.rules\n")
            print(presets.codex_rules(a.preset))
            print("# .codex/config.toml\n")
            print(presets.codex_config(a.preset, work))
            return 0
        written, skipped = presets.write_codex(a.write, a.preset, work)
        print("wrote " + ", ".join(written))
        if skipped:
            print(f"{skipped} exists, so it was left alone. The preset expects these settings in it:\n")
            print(presets.codex_config(a.preset, work))
        print(f"Codex reads a project's .codex/ only once you trust that folder (run codex there once and "
              f"accept). Check a command: codex execpolicy check --rules "
              f"{Path(a.write) / '.codex/rules/discover.rules'} -- gh pr merge 1")
        return 0
    if a.write:
        added = presets.merge_into(a.write, a.preset, a.work_dir, a.allow_domain)
        print(f"{a.write}: {len(added)} rule(s) added for {a.preset}" + "".join(f"\n  {r}" for r in added))
        if presets.PRESETS[a.preset]["sandbox"]:
            ok, advice = presets.sandbox_status()
            if not ok:
                print(f"\nWARNING: sessions here will NOT be sandboxed. {advice}\n"
                      f"Until then, the preset's other limits still apply (no GitHub writes beyond what it "
                      f"allows, credential files unreadable by the agent's file tools, repo hooks off), but "
                      f"the project's code runs with your normal permissions: prefer local reading, and "
                      f"don't run code from projects you don't trust.")
            f = Path(a.write).resolve()
            if f.parent.name == ".claude":
                folder = f.parent.parent
                print(f"\nDone. Start your agent in {folder} as usual (just `claude`); the preset applies there, "
                      f"and the repo's own hooks are off.")
                servers, keys = presets.repo_agent_config(folder)
                if keys:
                    print(f"Note: this repo ships .claude/settings.json with {', '.join(keys)}. Hooks are off, and "
                          f"your denies and sandbox switch win, but lists such as allowed hosts are merged with "
                          f"yours. Read it, or start with `claude --setting-sources user --settings {f}`, "
                          f"which ignores it.")
                if servers:
                    print(f"Turned off this repo's MCP servers ({', '.join(servers)}). New ones that arrive with "
                          f"a pull would start; rerun this command after pulling, or screen with "
                          f"`discover screen .`.")
            else:
                print(f"\nPass it when you start your agent: claude --settings {f} (unattended: claude -p "
                      f"--settings {f} \"...\"). Or write it to .claude/settings.local.json in the folder you "
                      f"start in, and just run `claude` there.")
        return 0
    print(f"# {presets.PRESETS[a.preset]['about']}")
    print(json.dumps(presets.settings(a.preset, a.work_dir, a.allow_domain), indent=2))
    return 0


def cmd_hub_check(a):
    from . import HUB_REPO, hubcheck
    findings = hubcheck.check(a.registry, HUB_REPO)
    emit({"hub": HUB_REPO, "findings": findings}, a.json, lambda _: hubcheck.format_report(findings))
    if a.open_issues:
        for action, title in hubcheck.sync_issues(findings, HUB_REPO):
            print(f"{action}: {title}", file=sys.stderr)
    return 1 if a.strict and any(f["severity"] == "error" for f in findings) else 0


class GitSource(Source):
    """A local clone read at a commit, without checking it out."""

    def __init__(self, path, commit):
        super().__init__(local=path)
        self.commit = commit or "HEAD"

    def describe(self):
        return f"{self.local}@{self.commit[:12]}"

    def read(self, path):
        import subprocess
        out = subprocess.run(["git", "-C", str(self.local), "show", f"{self.commit}:{self._p(path)}"],
                             capture_output=True)
        return out.stdout.decode("utf-8", "replace") if out.returncode == 0 else None

    def exists(self, path):
        import glob as globmod
        import subprocess
        p = self._p(path)
        if any(c in p for c in "*?["):
            out = subprocess.run(["git", "-C", str(self.local), "ls-tree", "-r", "-d", "--name-only", self.commit],
                                 capture_output=True, text=True)
            import fnmatch
            pat = p.rstrip("/")
            return any(fnmatch.fnmatch(d, pat) for d in out.stdout.split())
        out = subprocess.run(["git", "-C", str(self.local), "cat-file", "-e", f"{self.commit}:{p.rstrip('/')}"],
                             capture_output=True)
        return out.returncode == 0

    def last_modified(self, path):
        return None


def main(argv=None):
    # Windows consoles often can't encode characters like "→"; degrade them rather than crash.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(errors="replace")
    p = argparse.ArgumentParser(prog="discover", description=__doc__)
    p.add_argument("--version", action="version", version=f"discover {__version__}")
    sub = p.add_subparsers(dest="cmd", required=True)

    v = sub.add_parser("validate", help="check a project's files and which conventions it follows")
    v.add_argument("path", nargs="?", default=".")
    v.add_argument("--repo", help="validate a GitHub repo (owner/name) instead of a local path")
    v.add_argument("--ref", default="HEAD")
    v.add_argument("--registry-entry", help="apply a registry entry's overlay/adapter")
    v.add_argument("--pilot", help="check a pilot record's discover-pilot block instead (spec §3.6)")
    v.add_argument("--json", action="store_true")
    v.set_defaults(func=cmd_validate)

    sg = sub.add_parser("signals", help="hub curation: what to look at per project, from a hub build's projects.json")
    sg.add_argument("--data", default="site/data/projects.json", help="projects.json from `discover hub`")
    sg.add_argument("--today", help="YYYY-MM-DD, for reproducible output")
    sg.add_argument("--json", action="store_true")
    sg.set_defaults(func=cmd_signals)

    sc = sub.add_parser("screen", help="screen a cloned repo for signs that running it could harm you (static; never runs it)")
    sc.add_argument("path", nargs="?", default=".")
    sc.add_argument("--json", action="store_true")
    sc.set_defaults(func=cmd_screen)

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
                   choices=["formal-proof", "exact-certificate", "simulation", "benchmark", "observational",
                            "replication", "review-only"])
    i.add_argument("--entry", help="the project entry doc (default: an existing DISCOVERY.md or "
                                   "autoresearch.md, else a new DISCOVERY.md)")
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

    ch = sub.add_parser("choose", help="draw a project across the hub for a donation (seeded, reproducible)")
    ch.add_argument("--seed")
    ch.add_argument("--interests", help="comma-separated fields, matched against project domains")
    ch.add_argument("--round", type=int, default=1, help="the round of a long donation (each draws again)")
    ch.add_argument("--minutes", type=int, default=60)
    ch.add_argument("--focus", choices=list(prompt.FOCUS), default="project")
    ch.add_argument("--permissions", choices=list(prompt.PERMISSIONS), default="local")
    ch.add_argument("--action", choices=["contribute", "verify"], default="contribute")
    ch.add_argument("--data", help="agents.json path or URL (default: the hub's site)")
    ch.add_argument("--json", action="store_true")
    ch.set_defaults(func=cmd_choose)

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
    r.add_argument("repo", nargs="?")
    r.add_argument("--minutes", type=int, default=60)
    r.add_argument("--focus", choices=list(prompt.FOCUS), default="project")
    r.add_argument("--permissions", choices=list(prompt.PERMISSIONS), default="post")
    r.add_argument("--preset", choices=list(prompt.PRESETS), default="donor", help="with --action prepare")
    r.add_argument("--action", choices=["contribute", "explore", "onboard", "start", "prepare", "curate", *prompt.ACTIONS],
                   default="contribute",
                   help="which playbook the prompt points to")
    r.add_argument("--role", choices=list(prompt.GOALS), default="maintainer", help="onboard: who is asking")
    r.add_argument("--goal", help="onboard: default setup-and-submit / propose-and-nominate")
    r.add_argument("--context", help="onboard: a URL to start from, e.g. a proposal issue")
    r.add_argument("--problem", help="start: the problem, as text")
    r.add_argument("--problem-file", help="start: a file holding the problem")
    r.add_argument("--local", action="store_true", help="start: build on disk only")
    r.add_argument("--interests", help="explore: fields the donor cares about, in their words")
    r.add_argument("--seed", help="32 hex digits; default: fresh OS randomness")
    r.set_defaults(func=cmd_prompt)

    h = sub.add_parser("hub", help="build the explore page data from the registry")
    h.add_argument("--registry", default="registry/projects")
    h.add_argument("--out", default="site/data/projects.json")
    h.add_argument("--board", action="store_true", help="include live board snapshots (needs gh)")
    h.add_argument("--history", action="store_true",
                   help="derive each frontier's history from git where the project keeps no history file")
    h.add_argument("--strict", action="store_true", help="exit nonzero on any problem")
    h.set_defaults(func=cmd_hub)

    g = sub.add_parser("registry-add", help="create a registry entry (from flags or an issue-form body)")
    g.add_argument("--repo")
    g.add_argument("--contact")
    g.add_argument("--body-file")
    g.add_argument("--nominate", action="store_true", help="a nomination by a non-maintainer, not an application")
    g.add_argument("--proposal", help="URL of the setup proposal issue on the project")
    g.add_argument("--intake", help="URL of the hub issue this entry comes from")
    g.add_argument("--out", default="registry/projects")
    g.set_defaults(func=cmd_registry_add)

    s = sub.add_parser("submit", help="apply to list your project, or nominate one (opens an issue on the hub)")
    s.add_argument("repo")
    s.add_argument("--contact", help="your GitHub handle")
    s.add_argument("--notes")
    s.add_argument("--nominate", action="store_true", help="you don't maintain the project: nominate it")
    s.add_argument("--proposal", help="URL of a setup proposal issue you opened on the project")
    s.add_argument("--hub", default=__import__("discover").HUB_REPO)
    s.add_argument("--dry-run", action="store_true")
    s.set_defaults(func=cmd_submit)

    pm = sub.add_parser("permissions", help="print or write a coding-agent permission preset for a role")
    pm.add_argument("preset", choices=["donor-local", "donor-post", "donor", "maintainer"])
    pm.add_argument("--allow-domain", action="append", default=[], metavar="HOST",
                    help="donor presets: another host sandboxed commands may reach (repeatable)")
    pm.add_argument("--work-dir", metavar="PATH",
                    help="another folder sandboxed commands may write, besides the one the agent starts in")
    pm.add_argument("--agent", choices=["claude", "codex"], default="claude")
    pm.add_argument("--write", metavar="PATH",
                    help="claude: merge into a settings file, e.g. .claude/settings.local.json (keeps existing "
                         "rules); codex: the folder you run sessions from (writes .codex/rules/discover.rules, "
                         "and .codex/config.toml if there is none)")
    pm.set_defaults(func=cmd_permissions)

    hc = sub.add_parser("hub-check", help="the hub's scheduled check: consent, adapter drift, stale assessments")
    hc.add_argument("--registry", default="registry/projects")
    hc.add_argument("--open-issues", action="store_true", help="open, update and close one hub issue per finding")
    hc.add_argument("--strict", action="store_true", help="exit 1 if any finding is an error")
    hc.add_argument("--json", action="store_true")
    hc.set_defaults(func=cmd_hub_check)

    ac = sub.add_parser("adapter-check", help="check an adapter file against the repo it describes")
    ac.add_argument("file")
    ac.add_argument("--path", help="a local clone of the repo (reads it at the adapter's as_of commit)")
    ac.add_argument("--repo", help="owner/name, if not the adapter's own")
    ac.add_argument("--json", action="store_true")
    ac.set_defaults(func=cmd_adapter_check)

    a = p.parse_args(argv)
    a.path_given = "path" in a and a.path != "."
    return a.func(a)
