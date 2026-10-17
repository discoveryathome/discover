"""Check a project's files: the required ones (conformance) and which conventions it follows.

This is only the deterministic part of an assessment. The stage comes from a hub
assessment of the five properties (spec §3), never from this check.
"""

from . import schema
from .project import load_manifest


def normalize_catalog(catalog):
    """Accept the pre-v0 reference format (`schema_version: 1`) with a warning."""
    if catalog is not None and "schema" not in catalog and "schema_version" in catalog:
        catalog = {"schema": "discover-catalog/v0", **{k: v for k, v in catalog.items() if k != "schema_version"}}
        return catalog, ["catalog uses pre-v0 `schema_version`; treated as discover-catalog/v0"]
    return catalog, []


def normalize_frontier(raw, adapter=None):
    """Map a pre-v0 frontier record into v0 shape using a registry adapter.

    The adapter names which raw fields hold the v0 values, e.g.
    {"statement": "status", "metric": {"name": "kappa", "value": "kappa", "decimal": "decimal"}}.
    """
    if raw is None or raw.get("schema") == "discover-frontier/v0" or not adapter:
        return raw, []
    out = {"schema": "discover-frontier/v0"}
    for key, src in adapter.items():
        if key == "metric":
            m = {"name": src["name"], "value": str(raw.get(src["value"], ""))}
            if "decimal" in src and src["decimal"] in raw:
                m["decimal"] = str(raw[src["decimal"]])
            if "direction" in src:
                m["direction"] = src["direction"]
            out["metric"] = m
        elif key == "evidence_level":
            out[key] = src  # declared by the adapter, not read from the record
        elif isinstance(src, str) and src in raw:
            out[key] = raw[src]
    return out, ["frontier record is pre-v0; mapped through the registry adapter"]


def catalog_problems(catalog):
    probs = schema.check("catalog.schema.json", catalog)
    tracks = catalog.get("tracks", []) if isinstance(catalog, dict) else []
    total = sum(t.get("weight", 0) for t in tracks if isinstance(t.get("weight"), int))
    if tracks and total != 100:
        probs.append(f"$.tracks: weights sum to {total}, not 100")
    ids = [c.get("id") for t in tracks for c in t.get("tasks", [])]
    dupes = sorted({i for i in ids if ids.count(i) > 1})
    if dupes:
        probs.append(f"$.tracks: duplicate card ids {dupes}")
    tids = [t.get("id") for t in tracks]
    if len(tids) != len(set(tids)):
        probs.append("$.tracks: duplicate track ids")
    return probs


CONVENTIONS = {
    "catalog": "weighted task catalogue",
    "priority_log": "priority log",
    "coordination": "coordination channel",
    "reproduce": "frontier `reproduce` check",
    "ledger": "review ledger",
    "packages": "result packages",
}


def validate(source, overlay=None, adapter=None):
    """Return a report: `conformant`, `problems` (required files), `conventions` (name -> True,
    or a note on what's missing), warnings, and the loaded objects."""
    r = {"source": source.describe(), "conformant": False, "problems": [], "conventions": {}, "warnings": []}
    conv = r["conventions"]
    manifest, origin = load_manifest(source, overlay)
    r["manifest_origin"] = origin
    if manifest is None:
        r["problems"].append("discover.json not found (and no registry overlay)")
        return r
    if origin != "discover.json":
        r["warnings"].append("using registry overlay: the repo has no discover.json yet")
    r["manifest"] = manifest
    req = r["problems"]
    req += [f"discover.json {e}" for e in schema.check("manifest.schema.json", manifest)]
    entry = manifest.get("entry", {})
    for key in ("agents", "project"):
        path = entry.get(key)
        if path and source.exists(path) is False:
            req.append(f"entry.{key} file not found: {path}")
    frontier_path = manifest.get("frontier")
    raw = source.read_json(frontier_path) if frontier_path else None
    if frontier_path and raw is None:
        req.append(f"frontier record not found: {frontier_path}")
    frontier, warns = normalize_frontier(raw, adapter)
    r["warnings"] += warns
    if warns and frontier is not None and "updated_on" not in frontier:
        frontier["updated_on"] = source.last_modified(frontier_path) or "unknown"
    if frontier is not None:
        req += [f"frontier {e}" for e in schema.check("frontier.schema.json", frontier)]
        r["frontier"] = frontier

    cat_path = manifest.get("catalog")
    catalog = source.read_json(cat_path) if cat_path else None
    if not cat_path:
        conv["catalog"] = "manifest has no `catalog`"
    elif catalog is None:
        conv["catalog"] = f"not found: {cat_path}"
    else:
        catalog, warns = normalize_catalog(catalog)
        r["warnings"] += warns
        probs = catalog_problems(catalog)
        conv["catalog"] = "; ".join(probs) if probs else True
        r["catalog"] = catalog
    log = manifest.get("priority_log")
    conv["priority_log"] = ("manifest has no `priority_log`" if not log else
                            f"not found: {log}" if source.exists(log) is False else True)
    conv["coordination"] = True if "coordination" in manifest else "manifest has no `coordination` channel"
    conv["reproduce"] = True if frontier and frontier.get("reproduce") else "frontier record has no `reproduce` command"
    ledger = manifest.get("ledger")
    conv["ledger"] = ("manifest has no `ledger`" if not ledger else
                      f"not found: {ledger}" if source.exists(ledger) is False else True)
    pk = manifest.get("packages")
    if not pk:
        conv["packages"] = "manifest has no `packages` location"
    elif source.exists(pk) is False:
        conv["packages"] = f"none yet under {pk} (fine for a new project)"
    else:
        conv["packages"] = True

    r["conformant"] = not req
    return r


def format_report(r):
    if r["conformant"]:
        head = "conformant: the required files are present and valid"
    else:
        head = "not conformant: fix the problems below"
    lines = [f"{r['source']}: {head}"]
    lines += [f"  problem: {p}" for p in r["problems"]]
    lines += [f"  warning: {w}" for w in r["warnings"]]
    have = [CONVENTIONS[k] for k, v in r["conventions"].items() if v is True]
    if have:
        lines.append("  conventions followed: " + ", ".join(have))
    lines += [f"  convention not followed: {CONVENTIONS[k]}: {v}" for k, v in r["conventions"].items() if v is not True]
    lines.append("  Conventions are recommended, not required. The stage comes from a hub assessment of")
    lines.append("  the five properties (spec §3), not from this check.")
    return "\n".join(lines)
