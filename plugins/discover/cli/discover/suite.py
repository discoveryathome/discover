"""Evaluation suites (spec §5): a frontier that is a method, scored on held-out instances.

An algorithm race's result isn't one best object but a method that does better across a
distribution of problems. The suite's results file has one row per run: `method`,
`instance`, `value`, and optionally `seed`, `machine`, `draw`, `by` and `source`. The hub
compares the accepted method with each declared baseline, instance by instance, and says
how strong the strongest baseline it beats is.
"""

import math

from . import table as tablemod

STRENGTHS = ("starter", "published", "mature")
MACHINE_UNITS = ("seconds", "minutes", "hours", "milliseconds")
COLUMNS = ("method", "instance", "value")
TOL = 1e-9


def load(source, suite):
    """(rows, problem), rows as text-valued dicts, like a record table's."""
    return tablemod.load(source, suite)


def timed(suite):
    """A wall-clock budget: results depend on the machine, so runs pair only within one."""
    return ((suite.get("budget") or {}).get("unit") or "").lower() in MACHINE_UNITS


def problems(rows, suite):
    """Why the results can't be compared as declared (conformance problems)."""
    out = []
    for c in COLUMNS:
        missing = sum(1 for r in rows if c not in r)
        if missing:
            out.append(f"frontier suite: {missing} row(s) lack column {c!r}")
    methods = {r.get("method") for r in rows}
    if suite.get("current") not in methods:
        out.append(f"frontier suite: no results for the current method {suite.get('current')!r}")
    for b in suite.get("baselines", []):
        if b.get("method") not in methods:
            out.append(f"frontier suite: no results for baseline {b.get('method')!r}")
    bad = [r.get("value") for r in rows if _num(r.get("value", "")) is None]
    if bad:
        out.append(f"frontier suite: non-numeric values, e.g. {bad[0]!r}")
    return out


def warnings(rows, suite):
    out = []
    if timed(suite) and rows and "machine" not in rows[0]:
        out.append("frontier suite: the budget is wall-clock time but results have no `machine` column, "
                   "so a method and its baseline may have run on different machines")
    draw = (suite.get("instances") or {}).get("draw")
    if draw == "drawn" and rows and "draw" not in rows[0]:
        out.append("frontier suite: instances are `drawn`, but results have no `draw` column naming the draw")
    if not any(b.get("strength") == "mature" for b in suite.get("baselines", [])):
        out.append("frontier suite: no `mature` baseline; the page will say the method wasn't compared "
                   "with a mature solver")
    return out


def _num(s):
    try:
        x = float(str(s).strip())
    except ValueError:
        return None
    return x if math.isfinite(x) else None


def _means(rows, method, by_machine, column="value"):
    """{pair key: mean of `column` over seeds} for one method."""
    acc = {}
    for r in rows:
        if r.get("method") != method:
            continue
        v = _num(r.get(column, ""))
        if v is None:
            continue
        key = (r.get("instance"), r.get("machine", "") if by_machine else "")
        acc.setdefault(key, []).append(v)
    return {k: sum(vs) / len(vs) for k, vs in acc.items()}


def sign_test(wins, losses):
    """Two-sided exact sign test p-value, ties dropped."""
    n = wins + losses
    if n == 0:
        return 1.0
    k = min(wins, losses)
    tail = sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n
    return min(1.0, 2 * tail)


def compare(rows, suite, method, baseline, column="value", direction=None):
    """The method against one baseline on the instances both ran: relative gains (positive
    is better for the method), wins, ties, losses and a sign test. `column` and `direction`
    compare another measure than the objective (spec §5, Measures)."""
    by_machine = timed(suite)
    m, b = _means(rows, method, by_machine, column), _means(rows, baseline, by_machine, column)
    lower = (direction or suite.get("direction", "lower-is-better")) == "lower-is-better"
    gains, wins, ties, losses = [], 0, 0, 0
    for key in sorted(set(m) & set(b), key=str):
        diff = (b[key] - m[key]) if lower else (m[key] - b[key])
        scale = abs(b[key]) or abs(m[key]) or 1.0
        g = diff / scale
        if abs(g) <= TOL:
            ties += 1
            g = 0.0
        elif g > 0:
            wins += 1
        else:
            losses += 1
        gains.append(g)
    n = len(gains)
    p = sign_test(wins, losses)
    mean = sum(gains) / n if n else None
    verdict = ("beats" if n and mean > 0 and wins > losses and p < 0.05 else
               "loses" if n and mean < 0 and losses > wins and p < 0.05 else "inconclusive")
    return {"instances": n, "mean_gain": mean, "min_gain": min(gains) if gains else None,
            "max_gain": max(gains) if gains else None,
            "wins": wins, "ties": ties, "losses": losses, "p": p, "verdict": verdict}


def summary(rows, suite):
    """What the hub shows: each baseline's comparison and the strongest one beaten."""
    current = suite.get("current")
    comps = []
    for b in suite.get("baselines", []):
        c = compare(rows, suite, current, b["method"])
        comps.append({"method": b["method"], "strength": b.get("strength"),
                      **{k: b[k] for k in ("source", "version") if b.get(k)}, **c})
    beaten = [c["strength"] for c in comps if c["verdict"] == "beats" and c["strength"] in STRENGTHS]
    strongest = max(beaten, key=STRENGTHS.index) if beaten else None
    instances = {r.get("instance") for r in rows if r.get("method") == current}
    return {"current": current, "instances": len(instances), "runs": len(rows),
            "methods": sorted({r.get("method") for r in rows if r.get("method")}),
            "baselines": comps, "strongest_beaten": strongest,
            "has_mature": any(c["strength"] == "mature" for c in comps)}
