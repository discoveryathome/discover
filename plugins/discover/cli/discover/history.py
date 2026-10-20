"""The frontier's history (spec §5): the project's own file, or derived from git.

A project can keep `frontier.history`, one entry per change. Without one, the hub reads the
git history of the frontier record and takes each version's metric, so any project with a
metric gets a history without doing anything.
"""

import json
import re
from fractions import Fraction

MAX_POINTS = 200


def number(value):
    """A float for charting from an exact value: integer, decimal, scientific or a/b. None if
    it isn't a number."""
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    s = str(value).strip().replace("_", "")
    m = re.fullmatch(r"(-?\d+)\s*/\s*(\d+)", s)
    try:
        return float(Fraction(int(m[1]), int(m[2]))) if m else float(s)
    except (ValueError, ZeroDivisionError):
        return None


def parse(text, path):
    """(entries, problems) from a history file: JSON Lines, or a JSON array (by extension)."""
    try:
        if path.lower().endswith(".jsonl"):
            entries = [json.loads(line) for line in text.splitlines() if line.strip()]
        else:
            entries = json.loads(text)
    except ValueError as e:
        return [], [f"frontier history {path}: {e}"]
    if not isinstance(entries, list):
        return [], [f"frontier history {path}: expected a list of entries"]
    problems = []
    for i, e in enumerate(entries):
        if not isinstance(e, dict) or "date" not in e or "value" not in e:
            problems.append(f"frontier history {path}: entry {i + 1} needs `date` and `value`")
        elif not re.fullmatch(r"\d{4}-\d{2}-\d{2}.*", str(e["date"])):
            problems.append(f"frontier history {path}: entry {i + 1} has date {e['date']!r}, not YYYY-MM-DD")
    return ([] if problems else entries), problems


def points_from_file(entries):
    """Entries in the site's shape, oldest first."""
    out = []
    for e in sorted(entries, key=lambda e: str(e["date"])):
        p = {"date": str(e["date"])[:10], "value": str(e["value"]), "number": number(e["value"])}
        for k in ("statement", "bound", "case", "by", "source", "note"):
            if e.get(k) not in (None, "", []):
                p[k] = e[k]
        out.append(p)
    return out[-MAX_POINTS:]


def from_git(source, path, normalize=None, limit=60):
    """Points from the frontier record's git history: each version's metric, oldest first,
    keeping only versions where the value changed. `normalize` maps a raw record to v0
    (the adapter's frontier mapping), so mapped records get a history too."""
    points, last = [], object()
    for sha, date in reversed(source.versions(path, limit)):
        text = source.read_at(sha, path)
        try:
            raw = json.loads(text) if text else None
        except ValueError:
            continue
        rec = normalize(raw) if normalize and raw is not None else raw
        metric = (rec or {}).get("metric") or {}
        value = metric.get("value")
        if value in (None, "") or value == last:
            continue
        last = value
        p = {"date": date, "value": str(value), "number": number(metric.get("decimal") or value), "source": sha}
        if rec.get("statement"):
            p["statement"] = rec["statement"]
        if rec.get("sources"):
            p["sources"] = rec["sources"]
        points.append(p)
    return points[-MAX_POINTS:]
