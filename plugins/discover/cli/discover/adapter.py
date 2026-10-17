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
