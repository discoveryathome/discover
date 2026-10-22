"""Project demos (spec §4, Demos): pages a project builds and hosts to let readers explore
its results, a replay of decisions against hidden data, a dashboard, a browsable dataset.

The hub links to them and never serves them: a demo is the project's code, so it runs on
the project's origin, not the hub's. The hub says what a demo reads and whether that data
is older than the frontier, so a page that stopped updating isn't taken for the result.
"""

from . import visual as visualmod

KINDS = ("replay", "dashboard", "explorer")
MAX_DEMOS = 4
MAX_READS = 5


def resolve(manifest, adapter_block):
    """(demos, origin): the manifest's list, else the adapter's, else ([], None)."""
    if isinstance((manifest or {}).get("demos"), list):
        return manifest["demos"][:MAX_DEMOS], "project"
    if isinstance((adapter_block or {}).get("demos"), list):
        return adapter_block["demos"][:MAX_DEMOS], "adapter"
    return [], None


def problems(demos):
    """Why a demo can't be listed as declared (warnings; the hub drops that demo)."""
    out = []
    for i, d in enumerate(demos):
        name = d.get("title") or f"#{i + 1}"
        if not str(d.get("url", "")).startswith("https://"):
            out.append(f"demo {name!r}: url must be an https:// address")
        if d.get("image") and not visualmod.media_type(d["image"]):
            out.append(f"demo {name!r}: {d['image']!r} isn't SVG, PNG, JPEG, WebP or GIF")
    return out


def record_files(manifest, frontier):
    """The files the hub checks: the frontier record and its table or suite results."""
    f = frontier or {}
    return {p for p in ((manifest or {}).get("frontier"), (f.get("table") or {}).get("path"),
                        (f.get("suite") or {}).get("path")) if p}


def freshness(demo, manifest, frontier, source):
    """What the demo's data is, against the frontier: {reads_record, data_on, stale}.

    A demo that reads the frontier record (or its table or suite) shows the checked result
    as of its last deployment. One that reads other files is stale when every one of them
    was last changed before the frontier was updated."""
    reads = (demo.get("reads") or [])[:MAX_READS]
    if not reads:
        return {"reads_record": False, "data_on": None, "stale": False}
    if set(reads) & record_files(manifest, frontier):
        return {"reads_record": True, "data_on": None, "stale": False}
    dates = [d for d in (source.last_modified(p) for p in reads) if d]
    data_on = max(dates) if dates else None
    updated = (frontier or {}).get("updated_on")
    return {"reads_record": False, "data_on": data_on,
            "stale": bool(data_on and updated and data_on < updated)}
