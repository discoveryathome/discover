"""Measures beyond the objective (spec §5, Measures).

Pilots found agents improve the number they're given faster than they improve what it
stands for: an alignment score that rose while agreement with reference alignments fell,
a treatment plan that beat its objective and failed dose limits, fewer constraints and
more prover work. So a frontier can declare, beside its objective:

- constraints: requirements the current result must meet; a failure makes it invalid.
- guards: measures that mustn't get worse than the baseline, beyond a tolerance.
- targets: the quantity the objective stands in for, reported next to it.

Each is a number with a baseline the hub compares, a column of the suite's results compared
instance by instance like the objective, or a status the project states. The burden is on
the claim: a measure counts as better only with the evidence the objective needs, but as
worse as soon as it loses on more instances than it wins.
"""

from . import suite as suitemod

ROLES = ("constraint", "guard", "target")
STATUSES = ("pass", "fail", "held", "regressed", "better", "same", "worse")
BAD = ("fail", "regressed", "worse")
# Domains where a better score is most often not a better result (spec §5, Measures).
CAREFUL_DOMAINS = ("medicine", "life-sciences")
TOL = 1e-9


def _num(s):
    return suitemod._num(s) if s is not None else None


def _against(m, suite):
    """The baseline a suite measure compares with: the declared one, else the strongest."""
    if m.get("against"):
        return m["against"]
    bs = suite.get("baselines") or []
    rank = lambda b: suitemod.STRENGTHS.index(b["strength"]) if b.get("strength") in suitemod.STRENGTHS else -1
    return max(bs, key=rank)["method"] if bs else None


def assess(m, rows=None, suite=None):
    """One measure's status and how it was reached: {status, how, ...comparison}."""
    role = m.get("role")
    direction = m.get("direction", "higher-is-better")
    if role != "constraint" and m.get("column") and rows is not None and suite:
        against = _against(m, suite)
        c = suitemod.compare(rows, suite, suite.get("current"), against, m["column"], direction)
        if c["instances"]:
            # The burden is on the claim: "better" needs the objective's evidence (a
            # significant sign test), but mostly losing is enough to show it went wrong.
            leaning_worse = c["losses"] > c["wins"] and (c["mean_gain"] or 0) < 0
            verdict = "better" if c["verdict"] == "beats" else "worse" if leaning_worse else "same"
            status = verdict if role == "target" else ("regressed" if verdict == "worse" else "held")
            return {"status": status, "how": "suite", "against": against,
                    **{k: c[k] for k in ("instances", "mean_gain", "wins", "ties", "losses", "p")}}
    v, b = _num(m.get("value")), _num(m.get("baseline"))
    if role != "constraint" and v is not None and b is not None:
        d = (v - b) if direction == "higher-is-better" else (b - v)
        if role == "target":
            status = "better" if d > TOL else "worse" if d < -TOL else "same"
        else:
            status = "regressed" if d < -(_num(m.get("tolerance")) or 0) - TOL else "held"
        return {"status": status, "how": "value"}
    if role == "constraint" and _num(m.get("value")) is not None and _num(m.get("limit")) is not None:
        v, lim = _num(m["value"]), _num(m["limit"])
        ok = v <= lim + TOL if direction == "lower-is-better" else v >= lim - TOL
        return {"status": "pass" if ok else "fail", "how": "value"}
    return {"status": m.get("status") or "unreported", "how": "stated" if m.get("status") else None}


def evaluate(measures, rows=None, suite=None):
    """Every declared measure with its status, for the page and the agent index."""
    keep = ("name", "role", "statement", "value", "baseline", "limit", "unit", "direction", "tolerance",
            "column", "source", "note")
    return [{**{k: m[k] for k in keep if m.get(k) is not None}, **assess(m, rows, suite)} for m in measures]


def warnings(measures, evaluated, domains, has_objective):
    """What a reader should know before trusting the objective."""
    out = []
    for m, e in zip(measures, evaluated):
        name = m.get("name")
        if e.get("how") == "suite" or e.get("how") == "value":
            if m.get("status") and m["status"] != e["status"]:
                out.append(f"measure {name!r}: stated {m['status']!r}, but the numbers say {e['status']!r}")
        if e["status"] == "fail":
            out.append(f"measure {name!r}: the current result fails this constraint, so it isn't a valid result")
        elif e["status"] == "regressed":
            out.append(f"measure {name!r}: the current result is worse than its baseline on this guard")
        elif e["status"] == "worse":
            out.append(f"measure {name!r}: the objective improved but this target got worse")
        elif e["status"] == "unreported":
            out.append(f"measure {name!r}: no value, baseline, limit or status, so its state is unknown")
        if m.get("column") and e.get("how") != "suite":
            out.append(f"measure {name!r}: column {m['column']!r} isn't in the suite's results for both methods")
    careful = sorted(set(domains or []) & set(CAREFUL_DOMAINS))
    if has_objective and careful and not any(m.get("role") in ("guard", "target") for m in measures):
        out.append(f"frontier: a {careful[0]} result declares no guard or target, so the page can't show "
                   "whether a better score is a better result (spec §5, Measures)")
    return out
