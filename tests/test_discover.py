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
from discover.validate import format_report, validate  # noqa: E402

EXAMPLE = ROOT / "examples" / "integer-mult-bounds"


def iso(dt):
    return dt.isoformat(timespec="seconds").replace("+00:00", "Z")


class SchemaTests(unittest.TestCase):
    def test_plugin_copy_matches_spec(self):
        cmp = filecmp.dircmp(ROOT / "spec" / "schemas", ROOT / "plugins" / "discover" / "cli" / "discover" / "schemas")
        self.assertFalse(cmp.left_only or cmp.right_only or cmp.diff_files,
                         "plugin schemas out of sync with spec/schemas: run `make sync`")

    def test_examples_conform(self):
        self.assertEqual(schema.check("manifest.schema.json", json.loads((EXAMPLE / "discover.json").read_text())), [])
        self.assertEqual(schema.check("frontier.schema.json", json.loads((EXAMPLE / "frontier.json").read_text())), [])
        payload, problems = board.extract((EXAMPLE / "handoff-post.md").read_text())
        self.assertEqual(problems, [])
        self.assertEqual(payload["kind"], "handoff")

    def test_hub_description_conforms(self):
        self.assertEqual(schema.check("hub.schema.json", json.loads((ROOT / "hub.json").read_text())), [])

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
    def test_scaffold_is_conformant_and_never_overwrites(self):
        with tempfile.TemporaryDirectory() as d:
            r = init.scaffold(d, "T", "S", ["math"], "M", "o/r")
            self.assertIn("discover.json", r["created"])
            self.assertIn("AGENTS.md", r["created"])
            report = validate(Source(local=d))
            self.assertTrue(report["conformant"], report["problems"])
            self.assertIs(report["conventions"]["catalog"], True)
            self.assertIn("fine for a new project", report["conventions"]["packages"])
            self.assertIn("hub assessment", format_report(report))
            self.assertNotIn("Level", format_report(report))
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
            self.assertTrue(report["conformant"])
            self.assertIn("sum to 90", report["conventions"]["catalog"])


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
            self.assertEqual(entry["repos"][0]["repo"], "Some-Org/My.Repo")
            self.assertEqual(entry["consent"]["source"], "application")
            self.assertEqual(entry["contact"], "someone")

    def test_nomination_records_nominator_and_no_consent(self):
        from discover.cli import application_body
        body = application_body("Some-Org/Other", "fan", "looks good", nominate=True,
                                proposal="https://github.com/Some-Org/Other/issues/7")
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "body.md").write_text(body)
            self.assertEqual(main(["registry-add", "--body-file", str(Path(d) / "body.md"), "--out", d,
                                   "--intake", "https://github.com/h/h/issues/1"]), 0)
            entry = json.loads((Path(d) / "other.json").read_text())
            self.assertNotIn("consent", entry)
            self.assertEqual(entry["nomination"]["by"], "fan")
            self.assertEqual(entry["nomination"]["proposal"], "https://github.com/Some-Org/Other/issues/7")
            self.assertEqual(entry["intake"], "https://github.com/h/h/issues/1")
        maintainer = parse_issue_form(application_body("o/r", "me"))
        self.assertEqual(maintainer["Your relationship to the project"], "I maintain it")

    def test_duplicates_consent_and_name_collisions(self):
        from discover.cli import application_body
        def add(d, body):
            (Path(d) / "b.md").write_text(body)
            import io, contextlib
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                self.assertEqual(main(["registry-add", "--body-file", str(Path(d) / "b.md"), "--out", d]), 0)
            return json.loads(buf.getvalue())
        with tempfile.TemporaryDirectory() as d:
            first = add(d, application_body("Org/Proj", "fan", nominate=True))
            self.assertEqual((first["mode"], first["slug"], first["branch"]), ("add", "proj", "registry/org-proj"))
            self.assertEqual(add(d, application_body("org/proj", "fan2", nominate=True))["mode"], "duplicate")
            # The maintainer applies: consent is recorded on the existing entry.
            self.assertEqual(add(d, application_body("Org/Proj", "owner"))["mode"], "consent")
            entry = json.loads((Path(d) / "proj.json").read_text())
            self.assertEqual((entry["consent"]["source"], entry["contact"], entry["nomination"]["by"]),
                             ("application", "owner", "fan"))
            self.assertEqual(add(d, application_body("Org/Proj", "owner"))["mode"], "duplicate")
            # Same name, different owner: no overwrite.
            other = add(d, application_body("Else/Proj", "x"))
            self.assertEqual(other["slug"], "else-proj")
            self.assertEqual(json.loads((Path(d) / "proj.json").read_text())["repos"][0]["repo"], "Org/Proj")


class BuildTests(unittest.TestCase):
    """The published single-file CLI and rendered playbooks must match their sources."""

    def setUp(self):
        sys.path.insert(0, str(ROOT / "tools"))
        import build
        self.build = build
        self.info = json.loads((ROOT / "site" / "cli" / "latest.json").read_text())
        self.pyz = ROOT / "site" / "cli" / self.info["file"]

    def test_cli_file_matches_source_and_hash(self):
        self.assertEqual(self.build.read_members(self.pyz), self.build.cli_members(),
                         "site/cli is stale: run make sync")
        import hashlib
        self.assertEqual(hashlib.sha256(self.pyz.read_bytes()).hexdigest(), self.info["sha256"])
        self.assertTrue(self.info["file"].startswith("discover-" + self.info["sha256"][:12]))

    def test_playbooks_rendered(self):
        self.build.main(check=True)  # raises SystemExit if anything is stale

    def test_playbooks_carry_the_hash(self):
        text = (ROOT / "site" / "v0" / "contribute.md").read_text()
        self.assertIn(self.info["sha256"], text)
        self.assertNotIn("{{", text)

    def test_single_file_cli_runs(self):
        import subprocess
        out = subprocess.run([sys.executable, str(self.pyz), "--version"], capture_output=True, text=True)
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertTrue(out.stdout.startswith("discover "))
        # Commands that read packaged data (the schemas) must work from inside the zip too.
        with tempfile.TemporaryDirectory() as d:
            init.scaffold(d, "T", "S", ["math"], "M", "o/r")
            for args in (["validate", d], ["pick", d, "--seed", "0" * 32]):
                env = {**__import__("os").environ, "PYTHONIOENCODING": "cp1252"}  # a Windows console
                out = subprocess.run([sys.executable, "-I", str(self.pyz), *args], capture_output=True, text=True,
                                     encoding="utf-8", errors="replace", cwd=d, env=env)
                self.assertEqual(out.returncode, 0, out.stderr)


class SourceTests(unittest.TestCase):
    def test_project_in_subdirectory(self):
        with tempfile.TemporaryDirectory() as d:
            init.scaffold(Path(d) / "problems" / "p1", "T", "S", ["math"], "M", "o/r")
            src = Source(local=d, root="problems/p1")
            self.assertIsNotNone(src.read_json("discover.json"))
            self.assertTrue(src.exists("discover/catalog.json"))
            self.assertIsNone(Source(local=d).read("discover.json"))


class HubTests(unittest.TestCase):
    def test_summary_from_local_project(self):
        with tempfile.TemporaryDirectory() as d:
            init.scaffold(d, "T", "S", ["math"], "M", "o/r")
            report = validate(Source(local=d))
            s = hub.project_summary("t", {"repos": [{"repo": "o/r"}], "added_on": "2026-01-01"}, report)
            self.assertEqual(s["title"], "T")
            self.assertEqual(s["tracks"][0]["weight"], 100)
            self.assertEqual(s["frontier"]["evidence_level"], ["author-checked"])

    def test_listing_follows_the_consent_record(self):
        nominated = {"repos": [{"repo": "o/r"}], "added_on": "2026-01-01", "nomination": {"by": "x", "on": "2026-01-01"}}
        applied = {**nominated, "consent": {"source": "application", "list": True}}
        rep = lambda hubs: {"manifest_origin": "discover.json", "manifest": {"hubs": hubs}}
        none = Source(local=tempfile.gettempdir())
        rec = lambda hubs: hub.consent_record(none, rep(hubs), "Hub/Repo")
        self.assertEqual(hub.listing_state(nominated, rec(None)), "nominated")
        self.assertEqual(hub.listing_state(applied, rec(None)), "listed")
        # The maintainers adopt the proposal and name this hub: the nomination becomes a listing.
        self.assertEqual(hub.listing_state(nominated, rec([{"hub": "hub/repo", "list": True}])), "listed")
        self.assertEqual(hub.listing_state(applied, rec([{"hub": "*", "list": False}])), "opted-out")
        # A specific line beats the wildcard; an overlay written by the hub proves nothing.
        self.assertEqual(hub.listing_state(nominated, rec([{"hub": "*", "list": False}, {"hub": "Hub/Repo"}])), "listed")
        overlay = {"manifest_origin": "registry overlay", "manifest": {"hubs": [{"hub": "Hub/Repo", "list": True}]}}
        self.assertEqual(hub.listing_state(nominated, hub.consent_record(none, overlay, "Hub/Repo")), "nominated")

    def test_onboard_prompt(self):
        from discover import prompt
        text = prompt.onboard_prompt("contributor", "propose-and-nominate", "o/r", site="https://h/")
        self.assertTrue(text.startswith("Fetch https://h/v0/onboard.md"))
        self.assertIn("Role: contributor. Goal: propose-and-nominate. Project: https://github.com/o/r.", text)
        self.assertIn("Context: issue 3.", prompt.onboard_prompt("maintainer", "setup", "o/r", "issue 3", "https://h/"))
        with self.assertRaises(ValueError):
            prompt.onboard_prompt("contributor", "setup", "o/r")


if __name__ == "__main__":
    unittest.main()
