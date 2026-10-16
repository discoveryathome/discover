"""Coordination messages on GitHub Discussions: parse, summarize and post.

A protocol post is ordinary Markdown ending with a fenced ```inquiry JSON block
(spec/v0.md section 6). Posts without a block are ignored, so prose-only
conventions keep working alongside this.
"""

import json
import re
import subprocess
from datetime import datetime, timedelta, timezone

from . import schema

FENCE = re.compile(r"```inquiry[ \t]*\r?\n(.*?)```", re.S)


def now():
    return datetime.now(timezone.utc)


def parse_time(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def extract(body):
    """Return (payload, problems) for the last inquiry block in a post, or (None, [])."""
    blocks = FENCE.findall(body or "")
    if not blocks:
        return None, []
    try:
        payload = json.loads(blocks[-1])
    except json.JSONDecodeError as e:
        return None, [f"invalid JSON in inquiry block: {e}"]
    return payload, schema.check("message.schema.json", payload)


def render(payload, prose=""):
    """A post body: human prose followed by the machine-readable block."""
    block = json.dumps(payload, indent=2, ensure_ascii=False)
    return f"{prose.rstrip()}\n\n```inquiry\n{block}\n```\n".lstrip()


# --- GitHub transport -------------------------------------------------------

def gh_graphql(query, **variables):
    args = ["gh", "api", "graphql", "-f", f"query={query}"]
    for k, v in variables.items():
        args += ["-F" if isinstance(v, int) else "-f", f"{k}={v}"]
    out = subprocess.run(args, capture_output=True, text=True, encoding="utf-8")
    if out.returncode != 0:
        raise RuntimeError(f"gh api graphql failed: {out.stderr.strip()}")
    data = json.loads(out.stdout)
    if data.get("errors"):
        raise RuntimeError(f"GraphQL errors: {data['errors']}")
    return data["data"]


RECENT = """
query($owner:String!, $name:String!, $n:Int!) {
  repository(owner:$owner, name:$name) {
    discussions(first:$n, orderBy:{field:UPDATED_AT, direction:DESC}) {
      nodes { number title url updatedAt body createdAt author { login }
        comments(last:100) { nodes { id url body createdAt author { login }
          replies(last:50) { nodes { id url body createdAt author { login } } } } } }
    }
  }
}"""


def fetch_posts(repo, discussions=50):
    """Most recently updated discussions with comments and replies, flattened."""
    owner, name = repo.split("/")
    data = gh_graphql(RECENT, owner=owner, name=name, n=discussions)
    posts = []

    def add(node, number, title):
        posts.append({"url": node["url"], "body": node["body"], "created_at": node["createdAt"],
                      "author": (node.get("author") or {}).get("login"),
                      "discussion": number, "title": title})

    for d in data["repository"]["discussions"]["nodes"]:
        add(d, d["number"], d["title"])
        for c in d["comments"]["nodes"]:
            add(c, d["number"], d["title"])
            for r in c["replies"]["nodes"]:
                add(r, d["number"], d["title"])
    return posts


def discussion_id(repo, number):
    owner, name = repo.split("/")
    q = "query($owner:String!,$name:String!,$n:Int!){repository(owner:$owner,name:$name){discussion(number:$n){id}}}"
    return gh_graphql(q, owner=owner, name=name, n=number)["repository"]["discussion"]["id"]


def comment_id(url):
    """Resolve a discussion comment URL (…#discussioncomment-N) to its node id."""
    q = "query($url:URI!){resource(url:$url){... on DiscussionComment{id}}}"
    node = gh_graphql(q, url=url)["resource"]
    if not node or "id" not in node:
        raise RuntimeError(f"not a discussion comment URL: {url}")
    return node["id"]


def post(repo, discussion, body, reply_to=None):
    """Add a comment (or a reply to a comment URL); return the new comment's URL."""
    m = ("mutation($d:ID!,$b:String!,$r:ID){addDiscussionComment(input:"
         "{discussionId:$d,body:$b,replyToId:$r}){comment{url}}}")
    variables = {"d": discussion_id(repo, discussion), "b": body}
    if reply_to:
        variables["r"] = comment_id(reply_to)
    return gh_graphql(m, **variables)["addDiscussionComment"]["comment"]["url"]


# --- Board state ------------------------------------------------------------

def messages(posts):
    """Valid protocol messages, oldest first, plus a list of malformed posts."""
    good, bad = [], []
    for p in posts:
        payload, problems = extract(p["body"])
        if payload is None and not problems:
            continue
        if problems:
            bad.append({"url": p["url"], "problems": problems})
            continue
        good.append({**payload, "_url": p["url"], "_author": p["author"], "_created": p["created_at"]})
    good.sort(key=lambda m: m["_created"])
    return good, bad


def state(msgs, at=None, recent_days=7):
    """Live claims, open handoffs and recent done counts per task."""
    at = at or now()
    ended, taken, done_handoffs = set(), set(), set()
    for m in msgs:
        if m["kind"] in ("done", "released") and m.get("replaces"):
            ended.add(m["replaces"])
        if m.get("responds_to"):
            (done_handoffs if m["kind"] == "done" else taken).add(m["responds_to"])
    # A later done/released by the same author on the same task also ends a claim.
    for i, m in enumerate(msgs):
        if m["kind"] != "claim":
            continue
        for later in msgs[i + 1:]:
            if (later["kind"] in ("done", "released") and later["_author"] == m["_author"]
                    and later.get("task") == m.get("task") and later.get("scope") == m.get("scope")):
                ended.add(m["_url"])
    live = [m for m in msgs if m["kind"] == "claim" and m["_url"] not in ended
            and parse_time(m["expires"]) > at]
    live_handoff_claims = {m.get("responds_to") for m in live}
    handoffs = [m for m in msgs if m["kind"] == "handoff" and m["_url"] not in done_handoffs
                and m["_url"] not in live_handoff_claims]
    cutoff = at - timedelta(days=recent_days)
    recent_done = {}
    for m in msgs:
        if m["kind"] == "done" and m.get("task") and parse_time(m["_created"]) > cutoff:
            recent_done[m["task"]] = recent_done.get(m["task"], 0) + 1
    live_by_task = {}
    for m in live:
        if m.get("task"):
            live_by_task[m["task"]] = live_by_task.get(m["task"], 0) + 1
    return {"live_claims": live, "open_handoffs": handoffs,
            "live_by_task": live_by_task, "recent_done_by_task": recent_done}


def format_state(s):
    lines = [f"Open handoffs ({len(s['open_handoffs'])}):"]
    for h in s["open_handoffs"]:
        req = h.get("request", {})
        lines.append(f"  - [{req.get('track', '?')}] {req.get('question', h['scope'])}")
        lines.append(f"    {h['_url']}")
    lines.append(f"Live claims ({len(s['live_claims'])}):")
    for c in s["live_claims"]:
        lines.append(f"  - {c.get('task', '-')}: {c['scope']} (until {c['expires']}, {c['_author']})")
    if s["recent_done_by_task"]:
        lines.append("Recent done by task: " + ", ".join(f"{k}={v}" for k, v in sorted(s["recent_done_by_task"].items())))
    return "\n".join(lines)
