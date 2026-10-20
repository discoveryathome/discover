"""A project's hero visual (spec §4, Visual): its picture on the card and the page.

Declared in the manifest, or by the hub's adapter when the project declares none. The hub
draws `progress`, `bound-gap` and `records` itself from the frontier; an `image` is a file
the project (or the hub) keeps, copied into the site at build time and never inlined.
"""

import re

MAX_BYTES = 1_000_000
MEDIA = {"svg": "image/svg+xml", "png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg",
         "webp": "image/webp", "gif": "image/gif"}


def media_type(path):
    return MEDIA.get(str(path).rsplit(".", 1)[-1].lower())


def looks_like(data, media):
    """Whether the bytes are what the extension says, so a mislabelled file isn't served."""
    if media == "image/png":
        return data.startswith(b"\x89PNG\r\n\x1a\n")
    if media == "image/jpeg":
        return data.startswith(b"\xff\xd8\xff")
    if media == "image/gif":
        return data[:6] in (b"GIF87a", b"GIF89a")
    if media == "image/webp":
        return data[:4] == b"RIFF" and data[8:12] == b"WEBP"
    if media == "image/svg+xml":
        return b"<svg" in data[:4096]
    return False


def resolve(manifest, adapter_block):
    """(visual, origin): the manifest's declaration, else the adapter's, else (None, None)."""
    if isinstance((manifest or {}).get("visual"), dict):
        return manifest["visual"], "project"
    if isinstance((adapter_block or {}).get("visual"), dict):
        return adapter_block["visual"], "adapter"
    return None, None


def fill(template, title, frontier):
    """An image prompt with the frontier's current values in place of {title}, {statement},
    {metric} and {value}; unknown names are left as they are."""
    m = (frontier or {}).get("metric") or {}
    values = {"title": title or "", "statement": (frontier or {}).get("statement") or "",
              "metric": m.get("name") or "", "value": m.get("value") or ""}
    return re.sub(r"\{(\w+)\}", lambda x: str(values.get(x.group(1), x.group(0))), template)


def problems(visual, report):
    """Why a declared visual can't be drawn as declared (shown as warnings; the hub falls back)."""
    out, render = [], visual.get("render")
    f = report.get("frontier") or {}
    if render == "records" and not report.get("table"):
        out.append("visual: `records` needs a readable frontier table")
    if render in ("progress", "bound-gap") and not (f.get("metric") or {}).get("value"):
        out.append(f"visual: `{render}` needs a frontier metric")
    if render == "image" and not media_type(visual.get("src", "")):
        out.append(f"visual: {visual.get('src')!r} isn't SVG, PNG, JPEG, WebP or GIF")
    if visual.get("prompt") and render != "image":
        out.append("visual: `prompt` describes an image; it's ignored for drawn renders")
    return out
