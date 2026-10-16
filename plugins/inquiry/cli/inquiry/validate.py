"""Check a project against the v0 conformance levels."""

from . import schema
from .project import load_manifest


def normalize_catalog(catalog):
    """Accept the pre-v0 reference format (`schema_version: 1`) with a warning."""
    if catalog is not None and "schema" not in catalog and "schema_version" in catalog:
        catalog = {"schema": "inquiry-catalog/v0", **{k: v for k, v in catalog.items() if k != "schema_version"}}
        return catalog, ["catalog uses pre-v0 `schema_version`; treated as inquiry-catalog/v0"]
    return catalog, []


def normalize_frontier(raw, adapter=None):
    """Map a pre-v0 frontier record into v0 shape using a registry adapter.

    The adapter names which raw fields hold the v0 values, e.g.
    {"statement": "status", "metric": {"name": "kappa", "value": "kappa", "decimal": "decimal"}}.
    """
    if raw is None or raw.get("schema") == "inquiry-frontier/v0" or not adapter:
        return raw, []
    out = {"schema": "inquiry-frontier/v0"}
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


def validate(source, overlay=None, adapter=None):
    """Return a report dict: level (-1..2), errors/warnings per level, loaded objects."""
    r = {"source": source.describe(), "level": -1, "missing": {0: [], 1: [], 2: []}, "warnings": []}
    manifest, origin = load_manifest(source, overlay)
    r["manifest_origin"] = origin
    if manifest is None:
        r["missing"][0].append("inquiry.json not found (and no registry overlay)")
        return r
    if origin != "inquiry.json":
        r["warnings"].append("using registry overlay: the repo has no inquiry.json yet")
    r["manifest"] = manifest
    m0 = r["missing"][0]
    m0 += [f"inquiry.json {e}" for e in schema.check("manifest.schema.json", manifest)]
    entry = manifest.get("entry", {})
    for key in ("agents", "project"):
        path = entry.get(key)
        if path and source.exists(path) is False:
            m0.append(f"entry.{key} file not found: {path}")
    frontier_path = manifest.get("frontier")
    raw = source.read_json(frontier_path) if frontier_path else None
    if frontier_path and raw is None:
        m0.append(f"frontier record not found: {frontier_path}")
    frontier, warns = normalize_frontier(raw, adapter)
    r["warnings"] += warns
    if warns and frontier is not None and "updated_on" not in frontier:
        frontier["updated_on"] = source.last_modified(frontier_path) or "unknown"
    if frontier is not None:
        m0 += [f"frontier {e}" for e in schema.check("frontier.schema.json", frontier)]
        r["frontier"] = frontier

    m1 = r["missing"][1]
    cat_path = manifest.get("catalog")
    catalog = source.read_json(cat_path) if cat_path else None
    if not cat_path:
        m1.append("manifest has no `catalog`")
    elif catalog is None:
        m1.append(f"catalog not found: {cat_path}")
    else:
        catalog, warns = normalize_catalog(catalog)
        r["warnings"] += warns
        m1 += [f"catalog {e}" for e in catalog_problems(catalog)]
        r["catalog"] = catalog
    log = manifest.get("priority_log")
    if not log:
        m1.append("manifest has no `priority_log`")
    elif source.exists(log) is False:
        m1.append(f"priority log not found: {log}")
    if "coordination" not in manifest:
        m1.append("manifest has no `coordination` channel")

    m2 = r["missing"][2]
    if frontier is not None and not frontier.get("reproduce"):
        m2.append("frontier record has no `reproduce` command")
    if not manifest.get("packages"):
        m2.append("manifest has no `packages` location")
    elif source.exists(manifest["packages"]) is False:
        m2.append(f"no result packages match {manifest['packages']}")
    ledger = manifest.get("ledger")
    if not ledger:
        m2.append("manifest has no `ledger`")
    elif source.exists(ledger) is False:
        m2.append(f"review ledger not found: {ledger}")

    for level in (0, 1, 2):
        if r["missing"][level]:
            break
        r["level"] = level
    return r


LEVEL_NAMES = {-1: "not conformant", 0: "Level 0 · discoverable", 1: "Level 1 · agent-ready", 2: "Level 2 · verifiable"}


def format_report(r):
    lines = [f"{r['source']}: {LEVEL_NAMES[r['level']]}"]
    for w in r["warnings"]:
        lines.append(f"  warning: {w}")
    for level in (0, 1, 2):
        for item in r["missing"][level]:
            lines.append(f"  L{level} missing: {item}")
    return "\n".join(lines)
