"""Record tables (spec §5): a frontier made of many independent cases, one row each.

Rows are read as text-valued dicts, whatever the file format, so keys, `where` filters
and command placeholders compare the same way for JSON and CSV.
"""

import csv
import io
import json
import re


def _text(v):
    return "" if v is None else v if isinstance(v, str) else json.dumps(v)


def parse(text, fmt):
    """Rows from the table file's text. fmt: json, jsonl or csv."""
    if fmt == "csv":
        rows = list(csv.DictReader(io.StringIO(text)))
    elif fmt == "jsonl":
        rows = [json.loads(line) for line in text.splitlines() if line.strip()]
    else:
        data = json.loads(text)
        rows = data.get("rows") if isinstance(data, dict) else data
        if not isinstance(rows, list):
            raise ValueError("a JSON table is an array of objects, or an object with a `rows` array")
    if not all(isinstance(r, dict) for r in rows):
        raise ValueError("every row must be an object")
    return [{k: _text(v) for k, v in r.items()} for r in rows]


def fmt_of(table):
    return table.get("format") or {"csv": "csv", "jsonl": "jsonl"}.get(table["path"].rsplit(".", 1)[-1].lower(), "json")


def load(source, table):
    """(rows, problem): rows from the project, or None and why not."""
    text = source.read(table["path"])
    if text is None:
        return None, f"frontier table not found: {table['path']}"
    try:
        return parse(text, fmt_of(table)), None
    except (ValueError, csv.Error) as e:
        return None, f"frontier table {table['path']}: {e}"


def key_of(row, table):
    return {k: row.get(k, "") for k in table["key"]}


def _num(s):
    try:
        return float(s)
    except ValueError:
        return None


def is_open(row, table):
    """Open while there's no proven bound, or the value doesn't meet it."""
    b = table.get("bound")
    if not b or not row.get(b, "").strip():
        return True
    v, bound = row.get(table["value"], "").strip(), row[b].strip()
    if v == bound:
        return False
    nv, nb = _num(v), _num(bound)
    return nv is None or nb is None or nv != nb


def problems(rows, table):
    """Missing columns and duplicate keys."""
    out = []
    cols = [table["value"], *table["key"]] + [table[c] for c in ("bound", "object", "by", "source", "updated") if table.get(c)]
    for c in dict.fromkeys(cols):
        missing = sum(1 for r in rows if c not in r)
        if missing:
            out.append(f"frontier table: {missing} row(s) lack column {c!r}")
    seen, dupes = set(), []
    for r in rows:
        k = json.dumps(key_of(r, table), sort_keys=True)
        if k in seen:
            dupes.append(k)
        seen.add(k)
    if dupes:
        out.append(f"frontier table: duplicate keys {dupes[:5]}")
    for name in re.findall(r"\{(\w+)\}", " ".join(table.get("check_row") or [])):
        if rows and name not in rows[0]:
            out.append(f"frontier table: check_row names a column the table lacks: {{{name}}}")
    return out


def summary(rows, table):
    return {"rows": len(rows), "open": sum(1 for r in rows if is_open(r, table))}


def check_command(table, row):
    """check_row with the row's values filled in, or None."""
    argv = table.get("check_row")
    if not argv:
        return None
    return [re.sub(r"\{(\w+)\}", lambda m: row.get(m.group(1), m.group(0)), a) for a in argv]


def eligible(rows, table, spec):
    """Rows a card with `rows: spec` may draw, in a stable order (by key)."""
    spec = spec or {}
    where = {k: _text(v) for k, v in (spec.get("where") or {}).items()}
    out = [r for r in rows
           if (not spec.get("open", True) or is_open(r, table))
           and all(r.get(k) == v for k, v in where.items())]
    return sorted(out, key=lambda r: json.dumps(key_of(r, table), sort_keys=True, separators=(",", ":")))
