"""Build the explore page's data file from the registry."""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from . import board as boardmod
from . import schema
from .project import Source
from . import HUB_REPO
from .prompt import templates
from .validate import validate


def project_summary(slug, entry, report, board=None):
    m = report.get("manifest") or {}
    home = entry["repos"][0]
    repo = home["repo"]
    blob = f"https://github.com/{repo}/blob/{home.get('ref', 'HEAD')}/" + (home["path"].strip("/") + "/" if home.get("path") else "")
    f = report.get("frontier") or {}
    cat = report.get("catalog") or {}
    threads = (m.get("coordination") or {}).get("threads") or {}
    out = {
        "slug": slug, "repo": repo, "repos": entry["repos"], "url": f"https://github.com/{repo}",
        "credit": (m.get("credit") or entry.get("credit")),
        "title": m.get("title", repo), "summary": m.get("summary", ""),
        "domains": m.get("domains", []), "maintainers": m.get("maintainers", []),
        "license": m.get("license"), "verification_profile": m.get("verification_profile"),
        "stage": entry.get("stage"), "assessment": entry.get("assessment"),
        "conformant": report["conformant"], "manifest_origin": report.get("manifest_origin"),
        "warnings": report["warnings"], "problems": report["problems"],
        "conventions": report["conventions"],
        "featured": entry.get("featured", False), "added_on": entry.get("added_on"),
        "links": {k: blob + v for k, v in (m.get("entry") or {}).items()},
        "discussions": {"all": f"https://github.com/{repo}/discussions",
                        **{k: f"https://github.com/{repo}/discussions/{n}" for k, n in threads.items()}},
        "session_minutes": (m.get("session") or {}).get("default_minutes", 60),
        "permissions": m.get("permissions", {}),
        "frontier": None, "tracks": [], "board": None,
    }
    if f:
        out["frontier"] = {
            "statement": f.get("statement"), "status": f.get("status"),
            "metric": f.get("metric"), "evidence_level": f.get("evidence_level", []),
            "scope": f.get("scope"), "updated_on": f.get("updated_on"),
            "open_assumptions": [a for a in f.get("assumptions", []) if a.get("status", "open") != "closed"],
            "record_url": blob + m["frontier"] if m.get("frontier") else None,
        }
    if cat:
        out["priority_revision"] = cat.get("priority_revision")
        out["assessed_on"] = cat.get("assessed_on")
        out["tracks"] = [{"id": t["id"], "weight": t["weight"], "useful_outcome": t.get("useful_outcome"),
                          "cards": [{"id": c["id"], "question": c["question"], "methods": c.get("methods", [])}
                                    for c in t.get("tasks", [])]}
                         for t in cat.get("tracks", [])]
    if board:
        out["board"] = {
            "open_handoffs": [{"url": h["_url"], "question": h["request"]["question"],
                               "track": h["request"].get("track"), "est_minutes": h["request"].get("est_minutes")}
                              for h in board["open_handoffs"]],
            "live_claims": len(board["live_claims"]),
            "recent_done": sum(board["recent_done_by_task"].values()),
        }
    return out


def site_url(registry_dir):
    """The hub's website from hub.json next to the registry, else the configured default."""
    hub_json = Path(registry_dir).resolve().parent.parent / "hub.json"
    try:
        return json.loads(hub_json.read_text(encoding="utf-8"))["website"].rstrip("/") + "/"
    except (OSError, ValueError, KeyError):
        return None


def build(registry_dir, out_path, with_board=False, log=sys.stderr):
    registry_dir = Path(registry_dir)
    projects, problems = [], []
    for path in sorted(registry_dir.glob("*.json")):
        slug = path.stem
        entry = json.loads(path.read_text(encoding="utf-8"))
        errs = schema.check("registry-entry.schema.json", entry)
        if errs:
            problems.append({"slug": slug, "errors": errs})
            print(f"skip {slug}: {errs}", file=log)
            continue
        source = Source.from_entry(entry)
        try:
            report = validate(source, entry.get("overlay"), entry.get("frontier_adapter"))
        except Exception as e:  # network, JSON, etc. Keep building the rest.
            problems.append({"slug": slug, "errors": [f"{type(e).__name__}: {e}"]})
            print(f"skip {slug}: {e}", file=log)
            continue
        board = None
        transport = ((report.get("manifest") or {}).get("coordination") or {}).get("transport")
        if with_board and transport in (None, "github-discussions"):
            try:
                msgs, _ = boardmod.messages(boardmod.fetch_posts(entry["repos"][0]["repo"]))
                board = boardmod.state(msgs)
            except Exception as e:
                print(f"{slug}: board unavailable ({e})", file=log)
        projects.append(project_summary(slug, entry, report, board))
        print(f"ok {slug}: {'conformant' if report['conformant'] else 'not conformant'}, stage {entry.get('stage', 'not assessed')}", file=log)
    data = {"generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "hub_repo": HUB_REPO, "projects": projects, "problems": problems,
            "prompts": templates(site_url(registry_dir))}
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return data
