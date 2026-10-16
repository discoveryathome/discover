import filecmp
import json
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "plugins" / "discover" / "cli"))

from discover import board, hub, init, pick, schema  # noqa: E402
from discover.cli import main, parse_issue_form  # noqa: E402
from discover.project import Source  # noqa: E402
from discover.validate import validate  # noqa: E402

EXAMPLE = ROOT / "examples" / "integer-mult-bounds"


def iso(dt):
    return dt.isoformat(timespec="seconds").replace("+00:00", "Z")


class SchemaTests(unittest.TestCase):
    def test_plugin_copy_matches_spec(self):
        cmp = filecmp.dircmp(ROOT / "spec" / "schemas", schema.SCHEMA_DIR)
        self.assertFalse(cmp.left_only or cmp.right_only or cmp.diff_files,
                         "plugin schemas out of sync with spec/schemas: run `make sync`")

    def test_examples_conform(self):
        self.assertEqual(schema.check("manifest.schema.json", json.loads((EXAMPLE / "discover.json").read_text())), [])
        self.assertEqual(schema.check("frontier.schema.json", json.loads((EXAMPLE / "frontier.json").read_text())), [])
        payload, problems = board.extract((EXAMPLE / "handoff-post.md").read_text())
        self.assertEqual(problems, [])
        self.assertEqual(payload["kind"], "handoff")

    def test_registry_entries_conform(self):
        for path in (ROOT / "registry" / "projects").glob("*.json"):
            with self.subTest(path.name):
                self.assertEqual(schema.check("registry-entry.schema.json", json.loads(path.read_text())), [])

    def test_conditional_requirements(self):
        base = {"v": 0, "scope": "s", "base": "abc", "posted_at": "2026-01-01T00:00:00Z"}
        self.assertIn("$: missing required 'expires'", schema.check("message.schema.json", {**base, "kind": "claim"}))
        self.assertIn("$: missing required 'artifact'", schema.check("message.schema.json", {**base, "kind": "done"}))
        self.assertEqual(schema.check("message.schema.json", {**base, "kind": "finding"}), [])


class InitValidateTests(unittest.TestCase):
    def test_scaffold_reaches_level_1_and_never_overwrites(self):
        with tempfile.TemporaryDirectory() as d:
            r = init.scaffold(d, "T", "S", ["math"], "M", "o/r")
            self.assertIn("discover.json", r["created"])
            self.assertIn("AGENTS.md", r["created"])
            report = validate(Source(local=d))
            self.assertEqual(report["level"], 1, report["missing"])
            self.assertTrue(any("packages" in m for m in report["missing"][2]))
            again = init.scaffold(d, "T2", "S", ["math"], "M", "o/r")
            self.assertEqual(again["created"], [])
            self.assertEqual(json.loads((Path(d) / "discover.json").read_text())["title"], "T")

    def test_bad_weights_are_reported(self):
        with tempfile.TemporaryDirectory() as d:
            init.scaffold(d, "T", "S", ["math"], "M", "o/r")
            cat_path = Path(d) / "discover" / "catalog.json"
            cat = json.loads(cat_path.read_text())
            cat["tracks"][0]["weight"] = 90
            cat_path.write_text(json.dumps(cat))
            report = validate(Source(local=d))
            self.assertEqual(report["level"], 0)
            self.assertTrue(any("sum to 90" in m for m in report["missing"][1]))


def catalog():
    card = lambda i: {"id": i, "question": f"q {i}", "starting_points": [], "methods": ["m1", "m2"],
                      "acceptance_gate": "g", "first_step": {"command": ["true"], "expected": ""},
                      "bottleneck_link": "b"}
    return {"schema": "discover-catalog/v0", "priority_revision": 1, "assessed_on": "2026-01-01",
            "tracks": [{"id": "a", "weight": 70, "tasks": [card("a1"), card("a2"), card("a3")]},
                       {"id": "b", "weight": 30, "tasks": [card("b1")]}]}


class PickTests(unittest.TestCase):
    seed = "0" * 31 + "1"

    def test_seed_reproduces(self):
        self.assertEqual(pick.pick(catalog(), self.seed), pick.pick(catalog(), self.seed))

    def test_scope_key_ignores_seed(self):
        a = pick.pick(catalog(), self.seed, task_id="a1")["suggestions"][0]
        b = pick.pick(catalog(), "f" * 32, task_id="a1")["suggestions"][0]
        if a["method"] == b["method"]:
            self.assertEqual(a["scope_key"], b["scope_key"])

    def test_track_weights_roughly_respected(self):
        hits = sum(pick.pick(catalog(), f"{i:032x}")["track"] == "a" for i in range(400))
        self.assertTrue(240 < hits < 320, hits)

    def test_crowded_card_is_drawn_less(self):
        crowded = {"live_by_task": {"a1": 5}, "recent_done_by_task": {}, "open_handoffs": []}
        first = lambda b: sum(pick.pick(catalog(), f"{i:032x}", track_id="a", board=b, count=1)
                              ["suggestions"][0]["task_id"] == "a1" for i in range(300))
        self.assertLess(first(crowded), first(None) / 2)

    def test_handoffs_listed_for_matching_track(self):
        h = {"_url": "u", "request": {"question": "q", "first_step": "f", "track": "b"}}
        b = {"live_by_task": {}, "recent_done_by_task": {}, "open_handoffs": [h]}
        self.assertEqual(len(pick.pick(catalog(), self.seed, track_id="b", board=b)["handoffs_first"]), 1)
        self.assertEqual(pick.pick(catalog(), self.seed, track_id="a", board=b)["handoffs_first"], [])


class BoardTests(unittest.TestCase):
    def post(self, url, author, minutes_ago, **payload):
        created = datetime.now(timezone.utc) - timedelta(minutes=minutes_ago)
        payload = {"v": 0, "scope": "s", "base": "abc", "posted_at": iso(created), **payload}
        return {"url": url, "author": author, "created_at": iso(created), "body": board.render(payload, "hi")}

    def test_claim_lifecycle_and_handoffs(self):
        future = iso(datetime.now(timezone.utc) + timedelta(hours=1))
        past = iso(datetime.now(timezone.utc) - timedelta(minutes=1))
        posts = [
            self.post("h1", "x", 60, kind="handoff", request={"question": "q", "first_step": "f"}),
            self.post("h2", "x", 59, kind="handoff", request={"question": "q2", "first_step": "f"}),
            self.post("c1", "alice", 50, kind="claim", task="t", expires=future, responds_to="h1"),
            self.post("c2", "bob", 40, kind="claim", task="t", expires=past),
            self.post("c3", "carol", 30, kind="claim", task="u", expires=future),
            self.post("d3", "carol", 10, kind="done", task="u", artifact="https://x"),
            {"url": "p", "author": "z", "created_at": iso(datetime.now(timezone.utc)), "body": "plain prose, no block"},
            {"url": "bad", "author": "z", "created_at": iso(datetime.now(timezone.utc)), "body": "```discover\n{nope\n```"},
        ]
        msgs, bad = board.messages(posts)
        self.assertEqual([b["url"] for b in bad], ["bad"])
        s = board.state(msgs)
        self.assertEqual([c["_url"] for c in s["live_claims"]], ["c1"])
        self.assertEqual([h["_url"] for h in s["open_handoffs"]], ["h2"])
        self.assertEqual(s["recent_done_by_task"], {"u": 1})


class RegistryTests(unittest.TestCase):
    def test_issue_form_to_entry(self):
        body = ("### Repository\n\nhttps://github.com/Some-Org/My.Repo\n\n"
                "### Maintainer GitHub handle\n\n@someone\n\n### Notes\n\n_No response_\n")
        self.assertEqual(parse_issue_form(body)["Notes"], "")
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "body.md").write_text(body)
            self.assertEqual(main(["registry-add", "--body-file", str(Path(d) / "body.md"), "--out", d]), 0)
            entry = json.loads((Path(d) / "my-repo.json").read_text())
            self.assertEqual(entry["repo"], "Some-Org/My.Repo")
            self.assertEqual(entry["contact"], "someone")


class HubTests(unittest.TestCase):
    def test_summary_from_local_project(self):
        with tempfile.TemporaryDirectory() as d:
            init.scaffold(d, "T", "S", ["math"], "M", "o/r")
            report = validate(Source(local=d))
            s = hub.project_summary("t", {"repo": "o/r", "added_on": "2026-01-01"}, report)
            self.assertEqual(s["title"], "T")
            self.assertEqual(s["tracks"][0]["weight"], 100)
            self.assertEqual(s["frontier"]["evidence_level"], ["author-checked"])


if __name__ == "__main__":
    unittest.main()
