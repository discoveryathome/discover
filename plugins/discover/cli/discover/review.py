"""Review capacity (spec §4 `review`, §12.2): what a maintainer declared, and what's waiting.

Shown on listings and in agents.json; never used to throttle a project. A project that
declares nothing has no limit. Only a maintainer's own `paused` closes the launcher.
"""

from datetime import datetime, timezone

from .board import gh_graphql, parse_time

# Authors GitHub reports with these associations are the project's own people. GitHub hides
# private org membership from tokens outside the org, so the manifest's maintainers count too.
MAINTAINER_ASSOC = {"OWNER", "MEMBER", "COLLABORATOR"}

OPEN_PRS = """
query($owner:String!, $name:String!, $after:String) {
  repository(owner:$owner, name:$name) {
    pullRequests(states:OPEN, first:100, after:$after, orderBy:{field:CREATED_AT, direction:DESC}) {
      totalCount pageInfo { hasNextPage endCursor }
      nodes { number url isDraft createdAt authorAssociation author { __typename login }
        reviews(first:20) { nodes { author { login } } }
        comments(first:20) { nodes { author { login } } } }
    }
  }
}"""


MAX_PAGES = 10


def fetch_open_prs(repo, gh=gh_graphql):
    """Open PRs, newest first (up to 1,000), plus the total count."""
    owner, name = repo.split("/")
    nodes, after = [], None
    for _ in range(MAX_PAGES):
        args = {"owner": owner, "name": name, **({"after": after} if after else {})}
        page = gh(OPEN_PRS, **args)["repository"]["pullRequests"]
        nodes += page["nodes"]
        if not page["pageInfo"]["hasNextPage"]:
            break
        after = page["pageInfo"]["endCursor"]
    return nodes, page["totalCount"]


def _bot(author):
    return not author or author.get("__typename") == "Bot" or (author.get("login") or "").endswith("[bot]")


def awaiting(prs, at=None, total=None, own=()):
    """Contributions waiting for a first response: open, non-draft PRs from outside the
    project with no review or comment from anyone but their author. `own` is the
    maintainers' GitHub logins."""
    at = at or datetime.now(timezone.utc)
    own = {o.lower() for o in own}
    waiting = []
    for pr in prs:
        author = pr.get("author") or {}
        if (pr.get("isDraft") or _bot(author) or pr.get("authorAssociation") in MAINTAINER_ASSOC
                or (author.get("login") or "").lower() in own):
            continue
        others = [n for k in ("reviews", "comments") for n in (pr.get(k) or {}).get("nodes", [])
                  if (n.get("author") or {}).get("login") not in (None, author.get("login"))
                  and not _bot(n.get("author"))]
        if not others:
            waiting.append(pr)
    oldest = min((parse_time(p["createdAt"]) for p in waiting), default=None)
    return {"awaiting": len(waiting), "oldest_days": round((at - oldest).total_seconds() / 86400, 1) if oldest else None,
            "urls": [p["url"] for p in waiting[:20]],
            # Fewer fetched than open: the count is a lower bound.
            "partial": total is not None and total > len(prs)}


def status(declared, measured=None):
    """The listing's review signal from the manifest's `review` block and a measurement.

    state: paused (the maintainer closed the launcher), surge (ready for any traffic),
    undeclared (no limit), room or full (a numeric capacity against what's waiting), or
    declared (numeric, not measured yet). Nothing here is enforced.
    """
    declared = declared or {}
    per_week = declared.get("per_week")
    out = {"per_week": per_week, "paused": bool(declared.get("paused")),
           "awaiting": None, "oldest_days": None, "headroom": None}
    if measured:
        out["awaiting"], out["oldest_days"] = measured["awaiting"], measured["oldest_days"]
        out["partial"] = measured.get("partial", False)
    if out["paused"]:
        out["state"] = "paused"
    elif per_week == "surge":
        out["state"] = "surge"
    elif not isinstance(per_week, int):
        out["state"] = "undeclared"
    elif out["awaiting"] is None:
        out["state"] = "declared"
    else:
        out["headroom"] = per_week - out["awaiting"]
        out["state"] = "room" if out["headroom"] > 0 else "full"
    return out
