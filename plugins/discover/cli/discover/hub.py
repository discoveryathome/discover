"""Build the explore page's data file from the registry."""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from . import adapter as adaptermod
from . import board as boardmod
from . import demo as demomod
from . import history as historymod
from . import visual as visualmod
from . import review as reviewmod
from . import schema
from .project import Source
from . import HUB_REPO
from .prompt import templates
from .validate import catalogued, normalize_frontier, validate

TABLE_SNAPSHOT_ROWS = 500


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


def project_summary(slug, entry, report, board=None, listing="listed", site=None, measured=None,
                    history=None, live=None):
    """`history` is {"from": "project" | "git", "points": [...]}; `live` says where a browser
    reads the frontier record and its table from the project at load time (spec §12.6)."""
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
        "bottleneck": m.get("bottleneck"),
        "frontier": None, "tracks": [], "board": None,
    }
    if f:
        out["frontier"] = {
            "statement": f.get("statement"), "status": f.get("status"),
            "metric": f.get("metric"), "evidence_level": f.get("evidence_level", []),
            "claim_kind": f.get("claim_kind", []), "external": f.get("external", []),
            "scope": f.get("scope"), "updated_on": f.get("updated_on"),
            "open_assumptions": [a for a in f.get("assumptions", []) if a.get("status", "open") != "closed"],
            "record_url": blob + m["frontier"] if m.get("frontier") else None,
        }
        if f.get("table") and report.get("table"):
            t = f["table"]
            out["frontier"]["table"] = {
                **report["table"], "url": blob + t["path"],
                **{k: t[k] for k in ("key", "value", "direction", "bound", "by", "source", "updated", "format") if t.get(k)},
                "rows_snapshot": report.get("table_rows", [])[:TABLE_SNAPSHOT_ROWS],
                "truncated": len(report.get("table_rows", [])) > TABLE_SNAPSHOT_ROWS,
            }
        if f.get("suite") and report.get("suite"):
            st = f["suite"]
            out["frontier"]["suite"] = {
                **report["suite"], "url": blob + st["path"], "held_out": st.get("instances"),
                **{k: st[k] for k in ("objective", "direction", "budget", "evaluate") if st.get(k)},
            }
        if report.get("measures"):
            out["frontier"]["measures"] = report["measures"]
        if f.get("formulation"):
            fm = f["formulation"]
            out["frontier"]["formulation"] = {**fm, **({"doc_url": blob + fm["doc"]} if fm.get("doc") else {})}
        if history and history.get("points"):
            out["frontier"]["history"] = history
        if live:
            out["frontier"]["live"] = live
    if cat:
        out["priority_revision"] = cat.get("priority_revision")
        out["assessed_on"] = cat.get("assessed_on")
        out["tracks"] = [{"id": t["id"], "weight": t["weight"], "useful_outcome": t.get("useful_outcome"),
                          **({"focus": t["focus"]} if t.get("focus") else {}),
                          "cards": [{"id": c["id"], "question": c["question"], "methods": c.get("methods", []),
                                     "claim_kind": c.get("claim_kind", []), "rows": "rows" in c,
                                     **({"contributes": c["contributes"]} if c.get("contributes") else {})}
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
            "bottleneck": (p.get("bottleneck") or {}).get("kind"),
            "frontier": ({"statement": f.get("statement"), "claim_kind": f.get("claim_kind", []),
                          **({"table": {k: f["table"][k] for k in ("rows", "open")}} if f.get("table") else {}),
                          **({"suite": {k: f["suite"][k] for k in ("current", "instances", "strongest_beaten", "has_mature")}}
                             if f.get("suite") else {}),
                          **({"measures": [{k: x[k] for k in ("name", "role", "status") if k in x}
                                           for x in f["measures"]]} if f.get("measures") else {}),
                          "open_assumptions": [a.get("id") or a.get("statement")
                                               for a in f.get("open_assumptions", [])]}
                         if f else ({"doc": p["frontier_doc"]["url"]} if p.get("frontier_doc") else None)),
            "tracks": [{"id": t["id"], "weight": t["weight"], "useful_outcome": t.get("useful_outcome"),
                        "focus": t.get("focus", []),
                        "contributes": sorted({c["contributes"] for c in t.get("cards", []) if c.get("contributes")})}
                       for t in p.get("tracks", [])],
            "open_handoffs": handoffs, "open_handoffs_count": len(handoffs),
            "live_claims": (p.get("board") or {}).get("live_claims"),
            "review": {k: (p.get("review") or reviewmod.status(None))[k]
                       for k in ("state", "per_week", "awaiting", "headroom", "mechanical")},
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


def copy_image(src, from_hub, source, hub_root, data_dir, name):
    """Copy an image into <data_dir>/visuals/<name>.bin after checking its size and that its
    bytes are the type its name says: (media type, path the site reads it from)."""
    media = visualmod.media_type(src)
    if from_hub:
        p = (Path(hub_root) / src).resolve()
        if Path(hub_root).resolve() not in p.parents or not p.is_file():
            raise ValueError(f"not a file in the hub: {src}")
        data = p.read_bytes()
        if len(data) > visualmod.MAX_BYTES:
            raise ValueError(f"{src} is larger than {visualmod.MAX_BYTES:,} bytes")
    else:
        data = source.read_bytes(src, visualmod.MAX_BYTES)
        if data is None:
            raise ValueError(f"image not found: {src}")
    if not visualmod.looks_like(data, media):
        raise ValueError(f"{src} isn't the {media} its name says")
    vdir = Path(data_dir) / "visuals"
    vdir.mkdir(parents=True, exist_ok=True)
    (vdir / f"{name}.bin").write_bytes(data)
    return media, f"{Path(data_dir).name}/visuals/{name}.bin"


def demos(slug, entry, report, adapter_block, source, hub_root, data_dir, log):
    """The project's demos for the site (spec §4, Demos): links, never hosted. Each says what
    it reads and whether that data predates the frontier; a thumbnail is copied like a
    hero image."""
    m = report.get("manifest")
    declared, origin = demomod.resolve(m, adapter_block)
    home = entry["repos"][0]
    blob = f"https://github.com/{home['repo']}/blob/{home.get('ref', 'HEAD')}/"
    out = []
    for i, d in enumerate(declared):
        probs = demomod.problems([d])
        if probs:
            print(f"{slug}: {'; '.join(probs)}; not listed", file=log)
            continue
        item = {"title": d["title"], "url": d["url"], "kind": d.get("kind"), "origin": origin,
                **{k: d[k] for k in ("note", "alt") if d.get(k)},
                "reads": [{"path": p, "url": blob + source._p(p)} for p in (d.get("reads") or [])[:demomod.MAX_READS]],
                "source_url": blob + source._p(d["source"]) if d.get("source") else None,
                **demomod.freshness(d, m, report.get("frontier"), source)}
        if d.get("image"):
            try:
                media, snapshot = copy_image(d["image"], False, source, hub_root, data_dir, f"{slug}-demo-{i}")
                item["image"] = {"type": media, "snapshot": snapshot}
            except Exception as e:
                print(f"{slug}: demo {d['title']!r} thumbnail unavailable ({e})", file=log)
        out.append(item)
    return out


def hero(slug, entry, report, adapter_block, source, hub_root, data_dir, title, log):
    """The project's declared visual for the site (spec §4, Visual), or None for the hub's
    default. An image is copied to <data_dir>/visuals/<slug>.bin, where the browser reads it
    as bytes and shows it as an <img>, so an SVG never runs as a page on the hub's origin."""
    vis, origin = visualmod.resolve(report.get("manifest"), adapter_block)
    if not vis:
        return None
    probs = visualmod.problems(vis, report)
    if probs:
        print(f"{slug}: {'; '.join(probs)}; using the default", file=log)
        return None
    render = vis["render"]
    out = {"render": render, "kind": vis.get("kind") or ("illustration" if render == "image" else "derived"),
           "origin": origin, **{k: vis[k] for k in ("alt", "caption", "baseline") if vis.get(k)}}
    if render != "image":
        return out
    src, from_hub = vis["src"], vis.get("from") == "hub"
    try:
        media, snapshot = copy_image(src, from_hub, source, hub_root, data_dir, slug)
    except Exception as e:
        print(f"{slug}: visual unavailable ({e}); using the default", file=log)
        return None
    home = entry["repos"][0]
    out.update({"type": media, "snapshot": snapshot,
                "live_url": None if from_hub else source.raw_url(src),
                "url": (f"https://github.com/{HUB_REPO}/blob/main/{src}" if from_hub else
                        f"https://github.com/{home['repo']}/blob/{home.get('ref', 'HEAD')}/{source._p(src)}")})
    if vis.get("prompt"):
        out["prompt"] = visualmod.fill(vis["prompt"], title, report.get("frontier"))
    return out


def build(registry_dir, out_path, with_board=False, log=sys.stderr, with_history=False):
    registry_dir = Path(registry_dir)
    out_path = Path(out_path)
    # Images are rewritten each build; a project that drops its visual or demo drops its copy.
    for old in (out_path.parent / "visuals").glob("*.bin"):
        old.unlink()
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
                bots = (((report.get("manifest") or {}).get("review") or {}).get("mechanical") or {}).get("bots", [])
                measured = reviewmod.awaiting(prs, total=total, own=own, verdict_bots=bots)
            except Exception as e:
                print(f"{slug}: review queue unavailable ({e})", file=log)
        frontier_path = (report.get("manifest") or {}).get("frontier")
        hist, live = None, None
        if report.get("frontier") is not None and frontier_path:
            if report.get("history"):
                hist = {"from": "project", "points": historymod.points_from_file(report["history"])}
            elif with_history and (report["frontier"].get("metric") or {}).get("value"):
                norm = (lambda raw: normalize_frontier(raw, fadapter)[0]) if fadapter else None
                hist = {"from": "git", "points": historymod.from_git(source, frontier_path, norm)}
            tbl = report["frontier"].get("table") or {}
            live = {"url": source.raw_url(frontier_path),
                    # A record in another shape is mapped in the browser the same way.
                    "map": fadapter if fadapter and any("pre-v0" in w for w in report["warnings"]) else None,
                    "table_url": source.raw_url(tbl["path"]) if report.get("table") else None}
        summary = project_summary(slug, entry, report, board, listing, site_url(registry_dir), measured,
                                  hist, live)
        if not summary["bottleneck"] and isinstance((ablock or {}).get("bottleneck"), dict):
            summary["bottleneck"] = {**ablock["bottleneck"], "from": "adapter"}
        summary["visual"] = hero(slug, entry, report, ablock, source, registry_dir.resolve().parent.parent,
                                 out_path.parent, summary["title"], log)
        summary["demos"] = demos(slug, entry, report, ablock, source, registry_dir.resolve().parent.parent,
                                 out_path.parent, log)
        if entry.get("assessment"):
            from .hubcheck import parse_assessment
            apath = registry_dir.resolve().parent.parent / entry["assessment"]
            ablock = parse_assessment(apath.read_text(encoding="utf-8"))[0] if apath.exists() else None
            summary["self_assessed"] = bool((ablock or {}).get("self_assessed"))
            summary["verification_covers"] = (ablock or {}).get("verification_covers")
        if entry.get("pilot"):
            from .hubcheck import parse_pilot
            ppath = registry_dir.resolve().parent.parent / entry["pilot"]
            pblock, perrs = parse_pilot(ppath.read_text(encoding="utf-8")) if ppath.exists() else (None, ["missing"])
            if pblock and not perrs:
                summary["pilot"] = {
                    "verdict": pblock["verdict"], "on": pblock["piloted_on"], "mode": pblock["mode"],
                    "self_piloted": pblock.get("self_piloted", False), "bottleneck": pblock.get("bottleneck"),
                    "sessions": len(pblock["sessions"]),
                    "fresh": sum(1 for x in pblock["sessions"] if x["fresh"]),
                    "progress": sum(1 for x in pblock["sessions"] if x["outcome"] == "progress"),
                    "url": f"https://github.com/{HUB_REPO}/blob/main/{entry['pilot']}"}
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
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    index = agent_index(projects, site_url(registry_dir), HUB_REPO, data["generated_at"])
    (out_path.parent / "agents.json").write_text(json.dumps(index, indent=2, ensure_ascii=False) + "\n",
                                                encoding="utf-8")
    return data
