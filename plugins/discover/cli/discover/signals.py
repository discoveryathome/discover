"""What a hub's curation sweep looks at, per project (the curate playbook).

Read from a hub build's projects.json, so it sees what donors see: the stage and the
pilot behind it, whether the frontier still moves, whether review keeps up, and what
the page flags. Each signal is a prompt for a person's judgment, never an action.
"""

from datetime import date

PLATEAU_DAYS = 90
PILOT_STALE_DAYS = 180
ASSESSMENT_STALE_DAYS = 45


def _days(since, today):
    try:
        return (today - date.fromisoformat(str(since)[:10])).days
    except ValueError:
        return None


def _assessed_on(path):
    """assessments/<id>/<YYYY-MM-DD>-<who>.md -> the date, or None."""
    name = str(path or "").rsplit("/", 1)[-1]
    return name[:10] if len(name) >= 10 and name[4] == "-" and name[7] == "-" else None


def for_project(p, today):
    """[{signal, detail}] for one project summary."""
    out = []
    add = lambda kind, detail: out.append({"signal": kind, "detail": detail})
    f = p.get("frontier") or {}
    if not p.get("conformant", True):
        add("not-conformant", "; ".join(p.get("problems") or []) or "required files missing or invalid")
    if p.get("listing") == "listed" and p.get("stage") is None:
        add("unassessed", "listed without an assessment")
    if p.get("self_assessed"):
        add("self-assessed", "the stage counts once an independent rerun agrees (spec §12.4)")
    age = _days(_assessed_on(p.get("assessment")), today) if p.get("assessment") else None
    if age is not None and age > ASSESSMENT_STALE_DAYS:
        add("assessment-old", f"assessed {age} days ago")
    pilot = p.get("pilot")
    if p.get("featured") and not pilot:
        add("featured-unpiloted", "featured without a pilot record (spec §3.6)")
    elif p.get("featured") and pilot and pilot.get("verdict") != "launch":
        add("featured-verdict", f"featured, but the pilot's verdict is {pilot.get('verdict')}")
    if pilot and (_days(pilot.get("on"), today) or 0) > PILOT_STALE_DAYS:
        add("pilot-old", f"piloted {pilot.get('on')}")
    points = (f.get("history") or {}).get("points") or []
    last = points[-1].get("date") if points else f.get("updated_on")
    still = _days(last, today) if last else None
    if f and still is not None and still > PLATEAU_DAYS:
        add("plateau", f"the frontier last changed {last}, {still} days ago")
    bad = [m["name"] for m in f.get("measures") or [] if m.get("status") in ("fail", "regressed", "worse")]
    if bad:
        add("measures", f"went the wrong way: {', '.join(bad)}")
    review = p.get("review") or {}
    if review.get("state") == "full":
        add("review-full", f"{review.get('awaiting')} awaiting a first response, capacity {review.get('per_week')}/week")
    elif review.get("state") == "paused":
        add("paused", "the maintainers closed the launcher")
    stale = [d["title"] for d in p.get("demos") or [] if d.get("stale")]
    if stale:
        add("demo-stale", f"data older than the frontier: {', '.join(stale)}")
    waited = _days(p.get("added_on"), today) if p.get("added_on") else None
    if p.get("listing") == "nominated" and waited is not None and waited > 90:
        add("nomination-old", f"nominated {p.get('added_on')}, no consent yet; never re-contact (spec §11.4)")
    return out


def sweep(data, today=None):
    today = today or date.today()
    rows = []
    for p in data.get("projects", []):
        rows.append({"slug": p["slug"], "listing": p.get("listing"), "stage": p.get("stage"),
                     "featured": p.get("featured", False), "verdict": (p.get("pilot") or {}).get("verdict"),
                     "bottleneck": (p.get("bottleneck") or {}).get("kind"), "signals": for_project(p, today)})
    skipped = [{"slug": x.get("slug"), "errors": x.get("errors")} for x in data.get("problems", [])]
    return {"generated_at": data.get("generated_at"), "projects": rows, "skipped": skipped}


def format_sweep(r):
    lines = [f"Hub signals from the build of {r['generated_at']}", ""]
    for p in r["projects"]:
        head = (f"{p['slug']}: {p['listing']}, stage {p['stage'] if p['stage'] is not None else 'none'}"
                f"{', featured' if p['featured'] else ''}"
                f"{', pilot ' + p['verdict'] if p['verdict'] else ''}"
                f"{', bottleneck ' + p['bottleneck'] if p['bottleneck'] else ''}")
        lines.append(head)
        lines += [f"  - {s['signal']}: {s['detail']}" for s in p["signals"]] or ["  (nothing to look at)"]
    for s in r["skipped"]:
        lines.append(f"{s['slug']}: skipped by the build: {'; '.join(s['errors'] or [])}")
    return "\n".join(lines)
