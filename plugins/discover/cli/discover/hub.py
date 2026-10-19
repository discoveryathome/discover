"""Build the explore page's data file from the registry."""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from . import adapter as adaptermod
from . import board as boardmod
from . import review as reviewmod
from . import schema
from .project import Source
from . import HUB_REPO
from .prompt import templates
from .validate import catalogued, validate


def consent_record(source, report, hub):
    """This hub's line in the project's own consent record (spec §11.4), or None.

    Read from the repo only: the hub writes adapters, so they prove nothing.
    """
    hubs = None
    if report.get("manifest_origin") == "discover.json":
        hubs = (report.get("manifest") or {}).get("hubs")
    if hubs is None:
        try:
            hubs = (source.read_json(".github/discover-hubs.json") or {}).get("hubs")
        except Exception:
            hubs = None
    if not isinstance(hubs, list):
        return None
    mine = [h for h in hubs if isinstance(h, dict) and str(h.get("hub", "")).lower() == hub.lower()]
    anyhub = [h for h in hubs if isinstance(h, dict) and h.get("hub") == "*"]
    return (mine or anyhub or [None])[0]


def listing_state(entry, record):
    """listed (consented), nominated (catalogued, no launcher) or opted-out (not shown)."""
    if record is not None:
        return "listed" if record.get("list", True) else "opted-out"
    if (entry.get("consent") or {}).get("list"):
        return "listed"
    return "nominated"


def project_summary(slug, entry, report, board=None, listing="listed", site=None, measured=None):
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
        "listing": listing, "nomination": entry.get("nomination"), "intake": entry.get("intake"),
        "stage": entry.get("stage"), "assessment": entry.get("assessment"), "grades": entry.get("grades"),
        "projected": entry.get("projected"),
        "conformant": report["conformant"], "manifest_origin": report.get("manifest_origin"),
        "warnings": report["warnings"], "problems": report["problems"],
        "conventions": report["conventions"],
        "featured": entry.get("featured", False), "added_on": entry.get("added_on"),
        "links": {k: blob + v for k, v in (m.get("entry") or {}).items()},
        # Only link Discussions when the project says it coordinates there.
        "discussions": ({"all": f"https://github.com/{repo}/discussions",
                         **{k: f"https://github.com/{repo}/discussions/{n}" for k, n in threads.items()}}
                        if (m.get("coordination") or {}).get("transport") in (None, "github-discussions")
                        and m.get("coordination") else {}),
        "adapter_url": f"{site}{entry['adapter']}" if entry.get("adapter") and site else None,
        "picker": bool(m.get("picker")),
        "assessment_url": (f"https://github.com/{HUB_REPO}/blob/main/{entry['assessment']}"
                           if entry.get("assessment") else None),
        "session_minutes": (m.get("session") or {}).get("default_minutes", 60),
        "permissions": m.get("permissions", {}),
        "review": reviewmod.status(m.get("review"), measured),
        "requirements": m.get("requirements"),
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


def launchable(p):
    """Open to donated sessions: listed (not nominated), assessed at Stage 0 or above, its
    required files valid, and not paused by its maintainer. Review load never closes it."""
    return (p["listing"] == "listed" and p.get("stage") in (0, 1, 2) and p["conformant"]
            and not (p.get("review") or {}).get("paused"))


def agent_index(projects, site, hub_repo, generated_at):
    """agents.json: the hub's projects for an agent choosing one on a donor's behalf
    (schema agent-index.schema.json). Compact and stable; projects.json is the site's own."""
    from .pick import STAGE_WEIGHT, project_weight
    out = []
    for p in projects:
        if not launchable(p):
            continue
        perms = p.get("permissions") or {}
        handoffs = (p.get("board") or {}).get("open_handoffs", [])
        f = p.get("frontier") or {}
        item = {
            "slug": p["slug"], "repo": p["repo"], "url": p["url"], "title": p["title"], "summary": p["summary"],
            "domains": p["domains"], "stage": p["stage"], "self_assessed": p.get("self_assessed", False),
            "verification_profile": p.get("verification_profile"), "license": p.get("license"),
            "credit_policy": (p.get("credit") or {}).get("policy") if isinstance(p.get("credit"), dict) else p.get("credit"),
            # Stage 0 is local-only whatever the donor allows (spec §3.3); the manifest is a ceiling too.
            "sessions": {"local": True,
                         "post_messages": p["stage"] >= 1 and bool(perms.get("post_messages")),
                         "open_prs": p["stage"] >= 1 and bool(perms.get("open_prs"))},
            "session_minutes": p.get("session_minutes", 60),
            "requirements": p.get("requirements"),
            "frontier": ({"statement": f.get("statement"), "open_assumptions": [a.get("id") or a.get("statement")
                                                                                for a in f.get("open_assumptions", [])]}
                         if f else ({"doc": p["frontier_doc"]["url"]} if p.get("frontier_doc") else None)),
            "tracks": [{"id": t["id"], "weight": t["weight"], "useful_outcome": t.get("useful_outcome")}
                       for t in p.get("tracks", [])],
            "open_handoffs": handoffs, "open_handoffs_count": len(handoffs),
            "live_claims": (p.get("board") or {}).get("live_claims"),
            "review": {k: (p.get("review") or reviewmod.status(None))[k]
                       for k in ("state", "per_week", "awaiting", "headroom")},
            "own_picker": p.get("picker", False), "adapter_url": p.get("adapter_url"),
            "entry": p.get("links", {}), "page": f"{site}#/p/{p['slug']}" if site else None,
        }
        item["weight"] = project_weight(item)
        out.append(item)
    out.sort(key=lambda x: x["slug"])
    return {
        "schema": "discover-agents/v0", "generated_at": generated_at, "hub_repo": hub_repo, "site": site,
        "playbooks": {n: f"{site}v0/{n}.md" for n in ("explore", "contribute", "verify", "collaborate")} if site else {},
        "draw": {"stage_weight": {str(k): v for k, v in STAGE_WEIGHT.items()},
                 "rule": "weight = stage_weight[stage] (each project's `weight`). Keep the "
                         "projects whose domains meet the donor's interests (all, if none do), in slug order. "
                         "ticket = int(sha256(json([seed, \"project\"]))) mod total weight, with compact JSON; "
                         "the project is the one whose cumulative weight range holds the ticket. Round n > 1 of "
                         "one donation uses seed' = sha256(json([seed, \"round:n\"]))[:32]. explore.md has "
                         "a script."},
        "projects": out,
    }


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
        overlay, fadapter, ablock, aprobs = adaptermod.for_entry(entry, registry_dir.resolve().parent.parent)
        fdoc = (ablock or {}).get("frontier_doc")
        if aprobs:
            problems.append({"slug": slug, "errors": aprobs})
            print(f"skip {slug}: {aprobs}", file=log)
            continue
        try:
            report = validate(source, overlay, fadapter, catalogued(entry), fdoc)
        except Exception as e:  # network, JSON, etc. Keep building the rest.
            problems.append({"slug": slug, "errors": [f"{type(e).__name__}: {e}"]})
            print(f"skip {slug}: {e}", file=log)
            continue
        record = consent_record(source, report, HUB_REPO)
        listing = listing_state(entry, record)
        if listing == "opted-out":
            print(f"hide {slug}: its consent record opts out of {HUB_REPO}", file=log)
            continue
        board = None
        transport = ((report.get("manifest") or {}).get("coordination") or {}).get("transport")
        if with_board and listing == "listed" and transport in (None, "github-discussions"):
            try:
                msgs, _ = boardmod.messages(boardmod.fetch_posts(entry["repos"][0]["repo"]))
                board = boardmod.state(msgs)
            except Exception as e:
                print(f"{slug}: board unavailable ({e})", file=log)
        measured = None
        if with_board and listing == "listed":
            try:
                prs, total = reviewmod.fetch_open_prs(entry["repos"][0]["repo"])
                own = [x["github"] for x in (report.get("manifest") or {}).get("maintainers", []) if x.get("github")]
                measured = reviewmod.awaiting(prs, total=total, own=own)
            except Exception as e:
                print(f"{slug}: review queue unavailable ({e})", file=log)
        summary = project_summary(slug, entry, report, board, listing, site_url(registry_dir), measured)
        if entry.get("assessment"):
            from .hubcheck import parse_assessment
            apath = registry_dir.resolve().parent.parent / entry["assessment"]
            ablock = parse_assessment(apath.read_text(encoding="utf-8"))[0] if apath.exists() else None
            summary["self_assessed"] = bool((ablock or {}).get("self_assessed"))
            summary["verification_covers"] = (ablock or {}).get("verification_covers")
        if fdoc and report.get("manifest_origin") == "adapter":
            home = entry["repos"][0]
            summary["frontier_doc"] = {"url": f"https://github.com/{home['repo']}/blob/HEAD/{fdoc['path']}",
                                       "path": fdoc["path"], "note": fdoc.get("note")}
        projects.append(summary)
        print(f"ok {slug}: {listing}, {'conformant' if report['conformant'] else 'not conformant'}, "
              f"stage {entry.get('stage', 'not assessed')}", file=log)
    data = {"generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "hub_repo": HUB_REPO, "projects": projects, "problems": problems,
            "prompts": templates(site_url(registry_dir))}
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    index = agent_index(projects, site_url(registry_dir), HUB_REPO, data["generated_at"])
    (out_path.parent / "agents.json").write_text(json.dumps(index, indent=2, ensure_ascii=False) + "\n",
                                                encoding="utf-8")
    return data
