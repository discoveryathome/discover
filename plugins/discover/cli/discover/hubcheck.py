"""The hub's scheduled check (spec §12.6): what changed in listed projects since the hub last looked.

Each finding is one thing a hub maintainer or a hub-work session should act on: a
withdrawn consent record, an adapter whose paths changed, a stale assessment, an entry that
no longer validates. With --open-issues, each becomes one hub issue, updated in place and
closed when it's resolved.
"""

import json
import re
import subprocess
from datetime import date
from fnmatch import fnmatch
from pathlib import Path

from . import adapter as adaptermod
from . import schema
from .hub import consent_record, listing_state
from .project import Source
from .validate import catalogued, validate

ASSESSMENT = re.compile(r"^```discover-assessment[ \t]*\n(.*?)^```[ \t]*$", re.S | re.M)
STALE_DAYS = 30
SETTLE_DAYS = 7  # changes newer than this are expected churn on an active project
LABEL = "hub-check"
# Words in a project's summary, frontier and cards that tie its work to particular hardware.
HARDWARE = re.compile(r"\b(Apple Silicon|Apple M[1-9]|M[1-9] (?:Pro|Max|Ultra)|macOS only|CUDA|NVIDIA|ROCm|"
                      r"GPU|TPU|AVX-?512|AVX2|NEON|SVE|x86-64|AArch64|Windows only|Linux only)\b")
GRADED = ("orientation", "coordination", "verification", "review", "steering")


def parse_assessment(text):
    """(block, problems) from an assessment record's discover-assessment block."""
    found = ASSESSMENT.findall(text)
    if len(found) != 1:
        return None, [f"expected one ```discover-assessment block, found {len(found)}"]
    try:
        block = json.loads(found[0])
    except ValueError as e:
        return None, [f"discover-assessment block isn't JSON: {e}"]
    return block, schema.check("assessment.schema.json", block)


def hardware_hints(report):
    """Hardware the project's own text names, and whether anything declares it (spec §4):
    (terms, declared)."""
    m, f, cat = report.get("manifest") or {}, report.get("frontier") or {}, report.get("catalog") or {}
    cards = [c for t in cat.get("tracks", []) for c in t.get("tasks", [])]
    text = " ".join([m.get("summary", ""), f.get("statement", ""), f.get("scope", ""), " ".join(f.get("prerequisites", []))]
                    + [json.dumps([c.get("question"), c.get("methods"), c.get("first_step")]) for c in cards])
    terms = list(dict.fromkeys(x for x in HARDWARE.findall(text)))
    return terms, bool(m.get("requirements")) or any(c.get("requires") for c in cards)


def gh_api(path):
    out = subprocess.run(["gh", "api", path], capture_output=True, text=True, encoding="utf-8")
    if out.returncode != 0:
        raise RuntimeError(f"gh api {path}: {out.stderr.strip()}")
    return json.loads(out.stdout)


def touches(changed, paths):
    """The listed paths (files, folders or globs) that any changed file falls under."""
    hit = []
    for p in paths:
        q = p.rstrip("/")
        if any(c == q or c.startswith(q + "/") or fnmatch(c, p) or fnmatch(c, q + "/*") for c in changed):
            hit.append(p)
    return hit


def changed_since(repo, base, head, paths, gh, gone_only=False):
    """Listed paths changed between two commits, via GitHub's compare API (no clone).
    With gone_only, only paths that were deleted or renamed away."""
    if not base or not paths or head.startswith(base) or base.startswith(head):
        return []
    cmp = gh(f"repos/{repo}/compare/{base}...{head}")
    files = [f["filename"] for f in cmp.get("files", [])
             if not gone_only or f.get("status") in ("removed", "renamed")]
    hit = touches(files, paths)
    if len(cmp.get("files", [])) >= 300 and not hit:
        hit = ["(more than 300 files changed; compare them by hand)"]
    return hit


def missing_at(repo, head, paths, gh):
    """Listed paths that don't exist at a commit. Asks for each path directly, which stays exact
    however many files changed; a glob counts as present if its fixed prefix exists."""
    gone = []
    for p in paths:
        q = re.split(r"[*?\[]", p)[0].rstrip("/") or "."
        try:
            gh(f"repos/{repo}/contents/{q}?ref={head}")
        except RuntimeError:
            gone.append(p)
    return gone


def check(registry_dir, hub_repo, gh=gh_api, today=None):
    """Findings for every registry entry: [{slug, kind, severity, title, detail}]."""
    registry_dir = Path(registry_dir)
    root = registry_dir.resolve().parent.parent
    today = today or date.today()
    findings = []

    def add(slug, kind, severity, title, detail):
        findings.append({"slug": slug, "kind": kind, "severity": severity, "title": title, "detail": detail})

    for path in sorted(registry_dir.glob("*.json")):
        slug = path.stem
        entry = json.loads(path.read_text(encoding="utf-8"))
        repo = entry["repos"][0]["repo"]
        overlay, fadapter, block, aprobs = adaptermod.for_entry(entry, root)
        if aprobs:
            add(slug, "adapter-invalid", "error", "The adapter doesn't parse", "; ".join(aprobs))
        try:
            source = Source.from_entry(entry)
            report = validate(source, overlay, fadapter, catalogued(entry), (block or {}).get("frontier_doc"))
            if not report["conformant"]:
                add(slug, "not-conformant", "error", "The listing no longer validates", "; ".join(report["problems"]))
            listing = listing_state(entry, consent_record(source, report, hub_repo))
            if listing == "opted-out":
                add(slug, "opted-out", "error", "The project's consent record opts out of this hub",
                    "Remove the registry entry. The site already hides it.")
            if listing == "listed" and entry.get("stage") in (0, 1, 2) and not report.get("license"):
                add(slug, "no-license", "warning", "Listed with a launcher but the repo has no LICENSE file",
                    f"Stage {entry['stage']} requires a license (spec §3.3). Ask the maintainer to add one; "
                    f"otherwise the listing drops to catalogued 14 days after this notice.")
            terms, declared = hardware_hints(report)
            if terms and not declared:
                add(slug, "undeclared-hardware", "warning", "The project's work names particular hardware, but nothing declares it",
                    f"Its summary, frontier or cards mention {', '.join(terms[:6])}, and neither `requirements` in the "
                    f"manifest nor `requires` on any card says what a donor's machine needs (spec §4). Donors on other "
                    f"machines can draw work they can't run. Propose the declarations to the maintainer, or put them "
                    f"in the adapter.")
            head = gh(f"repos/{repo}/commits/HEAD")["sha"]
        except Exception as e:  # network, rate limits, a deleted repo: report, keep going
            add(slug, "check-failed", "warning", "The check couldn't read the project", f"{type(e).__name__}: {e}")
            continue

        if block and report.get("manifest_origin") == "adapter":
            # An adapter points to files rather than copying them, so only a path that moved or
            # vanished makes it wrong; edits to the files it points to are noted, not flagged.
            base, paths = block["as_of"]["commit"], block.get("paths", [])
            gone = missing_at(repo, head, paths, gh) if not head.startswith(base) else []
            if gone:
                add(slug, "adapter-drift", "warning", "Paths the adapter relies on moved or were deleted",
                    f"Gone since {base[:12]}: {', '.join(gone)}. Re-verify with the adapt playbook in update "
                    f"mode and move as_of forward.")
            else:
                edited = changed_since(repo, base, head, paths, gh)
                if edited:
                    add(slug, "adapter-edits", "info", "Files the adapter points to were edited",
                        f"Edited since {base[:12]}: {', '.join(edited)}. The adapter maps rather than copies, "
                        f"so it's probably still right; refresh as_of at the next update.")

        if not entry.get("assessment"):
            if listing == "listed":
                add(slug, "not-assessed", "info", "Listed but not yet assessed", "Run the assess playbook.")
            continue
        apath = root / entry["assessment"]
        if not apath.exists():
            add(slug, "assessment-missing", "error", "The entry's assessment file doesn't exist", entry["assessment"])
            continue
        ablock, problems = parse_assessment(apath.read_text(encoding="utf-8"))
        if ablock is None or problems:
            add(slug, "assessment-invalid", "error", "The assessment record's block is missing or invalid",
                "; ".join(problems))
            continue
        if "stage" in entry and entry["stage"] != ablock["stage"]:
            add(slug, "registry-mismatch", "error", "The registry's stage differs from the assessment",
                f"registry: {entry['stage']!r}; assessment: {ablock['stage']!r}")
        if entry.get("grades") and {k: entry["grades"].get(k) for k in GRADED} != ablock["grades"]:
            add(slug, "registry-mismatch", "error", "The registry's grades differ from the assessment",
                f"registry: {entry['grades']}; assessment: {ablock['grades']}")
        age = (today - date.fromisoformat(ablock["assessed_on"])).days
        stale = changed_since(repo, ablock["assessed_commit"], head, ablock.get("entry_paths", []), gh)
        if stale and age < SETTLE_DAYS:
            add(slug, "assessment-changes", "info", "The entry docs changed since the assessment",
                f"Changed since {ablock['assessed_commit'][:12]}: {', '.join(stale)}. Expected on an active "
                f"project; it becomes a re-assessment if still true after {SETTLE_DAYS} days.")
        elif stale:
            add(slug, "assessment-stale", "warning", "The entry docs changed since the assessment",
                f"Changed since {ablock['assessed_commit'][:12]}: {', '.join(stale)}. Re-assess (assess playbook, "
                f"re-assess mode).")
        elif age > STALE_DAYS:
            add(slug, "assessment-old", "info", f"Assessed {age} days ago",
                f"Probes rerun at least monthly (spec §3.4). Last assessed {ablock['assessed_on']}.")
    return findings


def format_report(findings):
    if not findings:
        return "Hub check: nothing to act on."
    lines = [f"Hub check: {len(findings)} finding(s)", ""]
    for f in findings:
        lines.append(f"- [{f['severity']}] {f['slug']}: {f['title']} ({f['kind']})")
        lines.append(f"  {f['detail']}")
    return "\n".join(lines)


def issue_title(f):
    return f"[{LABEL}] {f['slug']}: {f['kind']}"


def sync_issues(findings, hub_repo, run=subprocess.run, today=None):
    """One open issue per actionable finding: open new ones, update changed ones, close resolved ones."""
    today = (today or date.today()).isoformat()
    actionable = [f for f in findings if f["severity"] != "info"]
    run(["gh", "label", "create", LABEL, "-R", hub_repo, "--color", "FBCA04",
         "--description", "Opened by the scheduled hub check"], capture_output=True)
    out = run(["gh", "issue", "list", "-R", hub_repo, "--label", LABEL, "--state", "open", "--limit", "200",
               "--json", "number,title,body"], capture_output=True, text=True)
    existing = {i["title"]: i for i in json.loads(out.stdout or "[]")}
    done = []
    for f in actionable:
        title = issue_title(f)
        body = (f"**{f['title']}** ({f['severity']})\n\n{f['detail']}\n\n"
                f"Registry entry: `registry/projects/{f['slug']}.json`. Reported by the scheduled hub check "
                f"(spec §12.6) on {today}; it closes this issue when the finding is resolved.")
        if title in existing:
            if existing[title]["body"].split("Reported by")[0] != body.split("Reported by")[0]:
                run(["gh", "issue", "edit", str(existing[title]["number"]), "-R", hub_repo, "--body", body])
                done.append(("updated", title))
        else:
            run(["gh", "issue", "create", "-R", hub_repo, "--title", title, "--label", LABEL, "--body", body])
            done.append(("opened", title))
    current = {issue_title(f) for f in actionable}
    for title, issue in existing.items():
        if title not in current:
            run(["gh", "issue", "close", str(issue["number"]), "-R", hub_repo, "--comment",
                 f"Resolved: the hub check on {today} no longer reports this."])
            done.append(("closed", title))
    return done
