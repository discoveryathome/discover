"""Seeded, saturation-aware task suggestions (spec/v0.md section 7)."""

import hashlib
import json
import re
import secrets


def digest(value):
    return hashlib.sha256(json.dumps(value, separators=(",", ":"), sort_keys=True).encode()).hexdigest()


def scope_key(task_id, method):
    # Seed and base commit are excluded on purpose: they don't change the question.
    return digest([task_id, method])[:32]


def card_weight(card_id, board):
    """Down-weight crowded cards; never to zero, since claims are advisory."""
    if not board:
        return 1.0
    live = board["live_by_task"].get(card_id, 0)
    done = board["recent_done_by_task"].get(card_id, 0)
    return 1.0 / (1 + live + 0.5 * done)


def pick(catalog, seed=None, track_id=None, task_id=None, board=None, count=3):
    seed = (seed or secrets.token_hex(16)).lower()
    if not re.fullmatch(r"[0-9a-f]{32}", seed):
        raise ValueError("seed must be exactly 32 hexadecimal digits")

    def draw(label):
        return int(digest([seed, label]), 16)

    tracks = catalog["tracks"]
    if task_id:
        hits = [(t, c) for t in tracks for c in t["tasks"] if c["id"] == task_id]
        if not hits:
            raise ValueError(f"no card {task_id!r}")
        track, cards = hits[0][0], [hits[0][1]]
    else:
        if track_id:
            matches = [t for t in tracks if t["id"] == track_id]
            if not matches:
                raise ValueError(f"no track {track_id!r}")
            track = matches[0]
        else:
            ticket = draw("track") % sum(t["weight"] for t in tracks)
            for track in tracks:
                ticket -= track["weight"]
                if ticket < 0:
                    break
        pool = list(track["tasks"])
        cards = []
        for i in range(min(count, len(pool))):
            weights = [max(1, round(1000 * card_weight(c["id"], board))) for c in pool]
            ticket = draw(f"card:{i}") % sum(weights)
            for j, w in enumerate(weights):
                ticket -= w
                if ticket < 0:
                    cards.append(pool.pop(j))
                    break

    suggestions = []
    for card in cards:
        method = card["methods"][draw(f"method:{card['id']}") % len(card["methods"])]
        s = {"task_id": card["id"], "question": card["question"], "method": method,
             "scope_key": scope_key(card["id"], method), "first_step": card.get("first_step"),
             "acceptance_gate": card.get("acceptance_gate")}
        if board:
            s["live_claims"] = board["live_by_task"].get(card["id"], 0)
            s["recent_done"] = board["recent_done_by_task"].get(card["id"], 0)
        suggestions.append(s)

    handoffs = []
    if board:
        handoffs = [{"url": h["_url"], "question": h["request"]["question"],
                     "first_step": h["request"]["first_step"], "track": h["request"].get("track")}
                    for h in board["open_handoffs"]
                    if h["request"].get("track") in (None, track["id"])]
    return {"seed": seed, "track": track["id"], "handoffs_first": handoffs,
            "suggestions": suggestions,
            "note": "Suggestions, not reservations. Prefer a matching open handoff. "
                    "Run an overlap check and write a task card before substantial work."}


def format_pick(r):
    lines = [f"seed {r['seed']}  track {r['track']}"]
    if r["handoffs_first"]:
        lines.append("Open handoffs on this track (prefer these):")
        for h in r["handoffs_first"]:
            lines += [f"  - {h['question']}", f"    first step: {h['first_step']}", f"    {h['url']}"]
    lines.append("Card suggestions:")
    for s in r["suggestions"]:
        crowd = ""
        if "live_claims" in s:
            crowd = f"  [live claims {s['live_claims']}, recent done {s['recent_done']}]"
        lines.append(f"  - {s['task_id']}{crowd}")
        lines.append(f"    question: {s['question']}")
        lines.append(f"    method: {s['method']}")
        if s.get("first_step"):
            lines.append(f"    first step: {' '.join(s['first_step']['command'])}  → expect {s['first_step']['expected']}")
        lines.append(f"    scope_key: {s['scope_key']}")
    lines.append(r["note"])
    return "\n".join(lines)
