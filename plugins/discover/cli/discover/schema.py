"""Minimal JSON Schema (2020-12 subset) checker, standard library only.

Supports the keywords the spec's schemas use: type, const, enum, required,
properties, additionalProperties (bool), items, minItems, uniqueItems, minimum,
pattern, allOf, if/then, and local $ref ("#/$defs/..."). Formats are not checked.
"""

import json
import pkgutil
import re

_TYPES = {
    "object": dict, "array": list, "string": str,
    "boolean": bool, "null": type(None),
}


def load(name):
    # The synced copy of spec/schemas (make sync). pkgutil also reads it from inside the .pyz.
    return json.loads(pkgutil.get_data(__package__, "schemas/" + name).decode("utf-8"))


def _is_type(value, name):
    if isinstance(name, list):  # a union, e.g. ["string", "null"]
        return any(_is_type(value, n) for n in name)
    if name == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if name == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    return isinstance(value, _TYPES[name])


def errors(schema, value, root=None, path="$"):
    """Return a list of 'path: message' strings; empty means valid."""
    root = root if root is not None else schema
    out = []
    if "$ref" in schema:
        ref = schema["$ref"]
        if not ref.startswith("#/"):
            raise ValueError(f"only local refs supported: {ref}")
        target = root
        for part in ref[2:].split("/"):
            target = target[part]
        return errors(target, value, root, path)
    if "type" in schema and not _is_type(value, schema["type"]):
        return [f"{path}: expected {schema['type']}"]
    if "const" in schema and value != schema["const"]:
        out.append(f"{path}: must equal {schema['const']!r}")
    if "enum" in schema and value not in schema["enum"]:
        out.append(f"{path}: must be one of {schema['enum']}")
    if isinstance(value, str) and "pattern" in schema and not re.search(schema["pattern"], value):
        out.append(f"{path}: does not match {schema['pattern']}")
    if _is_type(value, "number") and "minimum" in schema and value < schema["minimum"]:
        out.append(f"{path}: must be >= {schema['minimum']}")
    if isinstance(value, dict):
        for key in schema.get("required", []):
            if key not in value:
                out.append(f"{path}: missing required '{key}'")
        props = schema.get("properties", {})
        for key, sub in value.items():
            if key in props:
                out += errors(props[key], sub, root, f"{path}.{key}")
            elif schema.get("additionalProperties") is False:
                out.append(f"{path}: unexpected property '{key}'")
    if isinstance(value, list):
        if len(value) < schema.get("minItems", 0):
            out.append(f"{path}: needs at least {schema['minItems']} items")
        if schema.get("uniqueItems"):
            seen = [json.dumps(v, sort_keys=True) for v in value]
            if len(seen) != len(set(seen)):
                out.append(f"{path}: items must be unique")
        if "items" in schema:
            for i, item in enumerate(value):
                out += errors(schema["items"], item, root, f"{path}[{i}]")
    for sub in schema.get("allOf", []):
        if "if" in sub:
            if not errors(sub["if"], value, root, path) and "then" in sub:
                out += errors(sub["then"], value, root, path)
        else:
            out += errors(sub, value, root, path)
    return out


def check(schema_name, value):
    return errors(load(schema_name), value)
