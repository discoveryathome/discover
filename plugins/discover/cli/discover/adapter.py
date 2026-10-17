"""Adapters (spec §12.5): adapters/<project-id>.md in a hub repo.

Prose for donors' agents, plus one fenced ```discover-adapter JSON block that the hub's
tools read: where things live (`manifest`), how to read the results record
(`frontier_adapter`), and the commit it describes (`as_of`).
"""

import json
import re
from pathlib import Path

from . import schema

BLOCK = re.compile(r"^```discover-adapter[ \t]*\n(.*?)^```[ \t]*$", re.S | re.M)


def parse(text):
    """Return (block, problems) from an adapter file's text."""
    found = BLOCK.findall(text)
    if len(found) != 1:
        return None, [f"expected one ```discover-adapter block, found {len(found)}"]
    try:
        block = json.loads(found[0])
    except ValueError as e:
        return None, [f"discover-adapter block isn't JSON: {e}"]
    return block, schema.check("adapter.schema.json", block)


def hub_root(registry_entry_path):
    """registry/projects/<id>.json -> the hub repo's root."""
    return Path(registry_entry_path).resolve().parent.parent.parent


def for_entry(entry, root):
    """(overlay, frontier_adapter, block, problems) for a registry entry.

    Reads the adapter file when the entry names one; otherwise the deprecated inline fields.
    """
    if not entry.get("adapter"):
        return entry.get("overlay"), entry.get("frontier_adapter"), None, []
    path = Path(root) / entry["adapter"]
    if not path.exists():
        return None, None, None, [f"adapter not found: {entry['adapter']}"]
    block, problems = parse(path.read_text(encoding="utf-8"))
    if block is None:
        return None, None, None, problems
    return block.get("manifest"), block.get("frontier_adapter"), block, problems


def check(text, source_at, changed_since=None):
    """Check an adapter: its block, its paths at as_of, and the repo through its manifest.

    `source_at(commit)` returns a Source for the repo at that commit. `changed_since`, if
    given, returns the paths that changed between as_of and the repo's head.
    """
    from .validate import validate
    report = {"problems": [], "warnings": [], "missing_paths": [], "changed": None}
    block, problems = parse(text)
    report["problems"] += problems
    if block is None:
        return report
    commit = (block.get("as_of") or {}).get("commit")
    src = source_at(commit)
    for path in block.get("paths", []):
        if src.exists(path) is False:
            report["missing_paths"].append(path)
    report["problems"] += [f"path not found at as_of: {p}" for p in report["missing_paths"]]
    if block.get("manifest"):
        doc = block.get("frontier_doc")
        if doc and src.exists(doc.get("path", "")) is False:
            report["problems"].append(f"frontier_doc not found at as_of: {doc.get('path')}")
        r = validate(src, block["manifest"], block.get("frontier_adapter"), frontier_doc=doc)
        report["problems"] += [f"manifest: {p}" for p in r["problems"]]
        report["warnings"] += [w for w in r["warnings"] if "adapter: the repo has no discover.json" not in w]
        report["conventions"] = {k: v for k, v in r["conventions"].items()}
    else:
        report["warnings"].append("no manifest: the hub's tools can't validate or list the project")
    if changed_since:
        report["changed"] = changed_since(commit, block.get("paths", []))
    return report


def format_check(r):
    lines = ["adapter: " + ("ok" if not r["problems"] else f"{len(r['problems'])} problem(s)")]
    lines += [f"  problem: {p}" for p in r["problems"]]
    lines += [f"  warning: {w}" for w in r["warnings"]]
    for k, v in (r.get("conventions") or {}).items():
        lines.append(f"  {'has' if v is True else 'lacks'}: {k}" + ("" if v is True else f" ({v})"))
    if r["changed"]:
        lines.append("  changed since as_of: " + ", ".join(r["changed"]))
    elif r["changed"] == []:
        lines.append("  no listed path changed since as_of")
    return "\n".join(lines)
