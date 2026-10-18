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


def machine():
    """This machine, as `requires` blocks describe one (spec §4)."""
    import os
    import platform
    arch = {"amd64": "x86_64", "aarch64": "arm64"}.get(platform.machine().lower(), platform.machine().lower())
    system = {"darwin": "macos"}.get(platform.system().lower(), platform.system().lower())
    ram = None
    try:
        ram = os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES") / 2**30
    except (ValueError, OSError, AttributeError):
        pass
    return {"arch": arch, "os": system, "ram_gb": ram}


def unmet(requires, here):
    """What a requires block asks for that this machine lacks. GPU and disk can't be checked
    reliably, so they're left to the agent (with the note)."""
    if not requires:
        return []
    out = []
    if requires.get("arch") and here["arch"] not in [a.lower() for a in requires["arch"]]:
        out.append(f"arch {'/'.join(requires['arch'])} (this is {here['arch']})")
    if requires.get("os") and here["os"] not in [o.lower() for o in requires["os"]]:
        out.append(f"os {'/'.join(requires['os'])} (this is {here['os']})")
    if requires.get("ram_gb") and here["ram_gb"] and here["ram_gb"] < requires["ram_gb"]:
        out.append(f"{requires['ram_gb']} GB RAM (this has {here['ram_gb']:.0f})")
    return out


def pick(catalog, seed=None, track_id=None, task_id=None, board=None, count=3, here=None):
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
        if card.get("requires"):
            # The draw doesn't depend on the machine, so it stays reproducible; a session
            # takes the next suggestion when this one can't be served here.
            s["requires"] = card["requires"]
            s["unmet_here"] = unmet(card["requires"], here or machine())
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
        if s.get("unmet_here"):
            lines.append(f"    CAN'T RUN HERE, needs {'; '.join(s['unmet_here'])}: take the next suggestion")
        elif s.get("requires"):
            lines.append(f"    requires: {json.dumps(s['requires'])}")
        lines.append(f"    question: {s['question']}")
        lines.append(f"    method: {s['method']}")
        if s.get("first_step"):
            lines.append(f"    first step: {' '.join(s['first_step']['command'])}  → expect {s['first_step']['expected']}")
        lines.append(f"    scope_key: {s['scope_key']}")
    lines.append(r["note"])
    return "\n".join(lines)


# --- Choosing a project across the hub (spec §12.2) ---------------------------------

STAGE_WEIGHT = {0: 1, 1: 3, 2: 6}


def project_weight(p):
    """By stage: a later stage can absorb more traffic. Deliberately not by open handoffs,
    which measure demand, not the review capacity to absorb it; declared review capacity
    (ROADMAP item 4) is the planned second factor."""
    return STAGE_WEIGHT[p["stage"]]


def round_seed(seed, n):
    """Round 1 uses the seed itself; later rounds of one long donation derive their own."""
    return seed if n == 1 else digest([seed, f"round:{n}"])[:32]


def choose_project(projects, seed=None, interests=None, round_no=1):
    """Draw one launchable project, weighted by project_weight, from those matching the
    donor's interests (or from all, if none match). Projects are taken in slug order and the
    ticket is draw("project") mod the total weight, over the round's seed."""
    seed = (seed or secrets.token_hex(16)).lower()
    if not re.fullmatch(r"[0-9a-f]{32}", seed):
        raise ValueError("seed must be exactly 32 hexadecimal digits")
    pool = sorted(projects, key=lambda p: p["slug"])
    if not pool:
        raise ValueError("no project is open to donated sessions")
    wanted = {i.strip().lower() for i in (interests or []) if i.strip()}
    matched = [p for p in pool if wanted & {d.lower() for d in p.get("domains", [])}] if wanted else pool
    note = None
    if wanted and not matched:
        matched, note = pool, "No project matches those interests, so the draw is over every open project."
    rseed = round_seed(seed, round_no)
    weights = [project_weight(p) for p in matched]
    ticket = int(digest([rseed, "project"]), 16) % sum(weights)
    for p, w in zip(matched, weights):
        ticket -= w
        if ticket < 0:
            break
    return {"seed": seed, "round": round_no, "round_seed": rseed, "project": p, "weight": w,
            "total_weight": sum(weights), "pool": [q["slug"] for q in matched], "note": note}
