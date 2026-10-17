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

    def test_frontier_optional_only_while_catalogued(self):
        from discover.validate import catalogued
        overlay = {"schema": "discover/v0", "title": "T", "summary": "S", "domains": ["m"], "maintainers": [{"name": "x"}],
                   "canonical_repo": "https://github.com/o/r", "entry": {"agents": "README.md", "project": "README.md"}}
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "README.md").write_text("x")
            nominated = {"nomination": {"by": "f", "on": "2026-01-01"}}
            self.assertTrue(validate(Source(local=d), overlay, None, catalogued(nominated))["conformant"])
            listed = {**nominated, "consent": {"list": True}}
            self.assertFalse(catalogued(listed))
            self.assertFalse(validate(Source(local=d), overlay, None, catalogued(listed))["conformant"])

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


class MultiBlockTests(unittest.TestCase):
    def test_a_post_can_carry_a_done_and_a_handoff(self):
        base = {"v": 0, "task": "t", "base": "abc1234", "posted_at": "2026-01-01T00:00:00Z"}
        claim = {**base, "kind": "claim", "scope": "s", "expires": "2099-01-01T00:00:00Z"}
        done = {**base, "kind": "done", "scope": "s", "artifact": "PR #1"}
        hand = {**base, "kind": "handoff", "scope": "next", "request": {"question": "q", "first_step": "f"}}
        posts = [{"url": "u1", "author": "a", "created_at": "2026-01-01T00:00:00Z", "body": board.render(claim)},
                 {"url": "u2", "author": "a", "created_at": "2026-01-01T00:10:00Z",
                  "body": board.render(done, "finished") + board.render(hand)}]
        msgs, bad = board.messages(posts)
        self.assertEqual(([m["kind"] for m in msgs], bad), (["claim", "done", "handoff"], []))
        s = board.state(msgs)
        self.assertEqual(s["live_claims"], [])
        self.assertEqual([h["_url"] for h in s["open_handoffs"]], ["u2"])


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


class AdapterTests(unittest.TestCase):
    def test_hub_adapters_parse_and_entries_point_at_them(self):
        from discover import adapter
        for path in sorted((ROOT / "adapters").glob("*.md")):
            block, problems = adapter.parse(path.read_text(encoding="utf-8"))
            self.assertEqual(problems, [], path.name)
            self.assertEqual(block["project"], path.stem)
            entry = json.loads((ROOT / "registry" / "projects" / f"{path.stem}.json").read_text())
            self.assertEqual(entry["adapter"], f"adapters/{path.stem}.md")
            self.assertNotIn("overlay", entry)
            overlay, _, _, problems = adapter.for_entry(entry, ROOT)
            self.assertEqual((problems, overlay["canonical_repo"]), ([], f"https://github.com/{block['repo']}"))

    def test_parse_rejects_missing_or_doubled_block(self):
        from discover import adapter
        self.assertIsNone(adapter.parse("# no block")[0])
        one = '```discover-adapter\n{"schema": "discover-adapter/v0", "project": "p", "repo": "o/r", "as_of": {"commit": "abcdef1", "date": "2026-01-01"}}\n```\n'
        self.assertEqual(adapter.parse(one)[1], [])
        self.assertIsNone(adapter.parse(one + one)[0])

    def test_adapter_check_reads_the_repo_at_as_of(self):
        import io, contextlib, subprocess
        with tempfile.TemporaryDirectory() as d:
            git = lambda *a: subprocess.run(["git", "-C", d, *a], capture_output=True, text=True, check=True).stdout.strip()
            git("init", "-q"); git("config", "user.email", "t@t"); git("config", "user.name", "t")
            (Path(d) / "README.md").write_text("x"); (Path(d) / "notes").mkdir(); (Path(d) / "notes" / "a.md").write_text("a")
            git("add", "-A"); git("commit", "-qm", "one")
            as_of = git("rev-parse", "HEAD")
            block = {"schema": "discover-adapter/v0", "project": "p", "repo": "o/p",
                     "as_of": {"commit": as_of, "date": "2026-01-01"}, "paths": ["README.md", "notes/a.md"],
                     "manifest": {"schema": "discover/v0", "title": "P", "summary": "S", "domains": ["m"],
                                  "maintainers": [{"name": "x"}], "canonical_repo": "https://github.com/o/p",
                                  "entry": {"agents": "README.md", "project": "README.md"}},
                     "frontier_doc": {"path": "notes/a.md", "note": "the latest result"}}
            f = Path(d) / "adapter.md"
            write = lambda b: f.write_text("# A\n\n```discover-adapter\n" + json.dumps(b) + "\n```\n")
            run = lambda: (lambda buf: (main(["adapter-check", str(f), "--path", d]), buf))(io.StringIO())
            write(block)
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                self.assertEqual(main(["adapter-check", str(f), "--path", d]), 0)
            self.assertIn("no listed path changed", buf.getvalue())
            (Path(d) / "notes" / "a.md").write_text("b"); git("commit", "-qam", "two")
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                self.assertEqual(main(["adapter-check", str(f), "--path", d]), 0)
            self.assertIn("changed since as_of: notes/a.md", buf.getvalue())
            write({**block, "paths": ["README.md", "missing.md"]})
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main(["adapter-check", str(f), "--path", d]), 1)
            # Without a machine-readable frontier, a listing needs to know where the result is stated.
            write({k: v for k, v in block.items() if k != "frontier_doc"})
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main(["adapter-check", str(f), "--path", d]), 1)

    def test_frontier_adapter_selects_a_registry_entry(self):
        from discover.validate import normalize_frontier
        raw = {"current": "b", "results": [{"id": "a", "claim": "old"}, {"id": "b", "claim": "new", "scope": "s"}]}
        out, _ = normalize_frontier(raw, {"select": {"list": "results", "key": "id", "current": "current"},
                                          "statement": "claim", "scope": "scope", "evidence_level": ["author-checked"]})
        self.assertEqual((out["statement"], out["scope"]), ("new", "s"))
        out, warns = normalize_frontier({**raw, "current": "z"}, {"select": {}, "statement": "claim"})
        self.assertIsNone(out)
        self.assertIn("no entry", warns[0])

    def test_prompts_link_the_adapter(self):
        from discover import prompt
        url = "https://h/adapters/p.md"
        self.assertIn(url, prompt.donation_prompt("o/r", seed="ab" * 16, site="https://h/", adapter_url=url))
        self.assertIn(url, prompt.action_prompt("verify", "o/r", site="https://h/", adapter_url=url))
        self.assertNotIn("adapter", prompt.donation_prompt("o/r", seed="ab" * 16, site="https://h/"))

    def test_pick_defers_to_the_projects_own_picker(self):
        import io, contextlib
        with tempfile.TemporaryDirectory() as d:
            init.scaffold(d, "T", "S", ["math"], "M", "o/r")
            m = json.loads((Path(d) / "discover.json").read_text())
            m["picker"] = {"command": ["python3", "pick.py", "--seed", "{seed}"]}
            (Path(d) / "discover.json").write_text(json.dumps(m))
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                self.assertEqual(main(["pick", d, "--seed", "c" * 32]), 0)
            self.assertIn("python3 pick.py --seed " + "c" * 32, buf.getvalue())


class HubCheckTests(unittest.TestCase):
    def test_hub_assessments_parse_and_match_the_registry(self):
        from discover import hubcheck
        for path in sorted((ROOT / "assessments").glob("*/*.md")):
            block, problems = hubcheck.parse_assessment(path.read_text(encoding="utf-8"))
            self.assertEqual(problems, [], path)
        for path in sorted((ROOT / "registry" / "projects").glob("*.json")):
            entry = json.loads(path.read_text())
            if entry.get("assessment"):
                block, _ = hubcheck.parse_assessment((ROOT / entry["assessment"]).read_text(encoding="utf-8"))
                self.assertEqual(entry.get("stage"), block["stage"], path.name)
                self.assertEqual(entry.get("grades"), block["grades"], path.name)

    def test_drift_staleness_and_mismatch(self):
        from datetime import date
        from discover import hubcheck
        with tempfile.TemporaryDirectory() as d:
            hub = Path(d) / "hub"
            proj = Path(d) / "proj"
            init.scaffold(proj, "T", "S", ["math"], "M", "o/p")
            (hub / "registry" / "projects").mkdir(parents=True)
            (hub / "assessments" / "p").mkdir(parents=True)
            grades = {"orientation": "strong", "coordination": "adequate", "verification": "adequate",
                      "review": "adequate", "steering": "adequate"}
            block = {"schema": "discover-assessment/v0", "project": "p", "repo": "o/p", "assessed_commit": "aaaaaaa",
                     "assessed_on": "2026-01-01", "rubric": "v0", "assessor": "t", "grades": grades, "stage": 1,
                     "entry_paths": ["AGENTS.md", "DISCOVERY.md"]}
            (hub / "assessments" / "p" / "a.md").write_text("# A\n\n```discover-assessment\n" + json.dumps(block) + "\n```\n")
            entry = {"repos": [{"repo": "o/p"}], "added_on": "2026-01-01", "assessment": "assessments/p/a.md",
                     "stage": 0, "grades": grades, "consent": {"source": "application", "list": True}}
            (hub / "registry" / "projects" / "p.json").write_text(json.dumps(entry))

            def gh(path):
                if path.endswith("/commits/HEAD"):
                    return {"sha": "bbbbbbbbbb"}
                if "/contents/" in path:
                    return {}
                return {"files": [{"filename": "DISCOVERY.md"}, {"filename": "results/x.csv"}]}
            real = hubcheck.Source.from_entry
            hubcheck.Source.from_entry = classmethod(lambda cls, e: cls(local=proj))
            try:
                found = hubcheck.check(hub / "registry" / "projects", "h/h", gh, date(2026, 1, 10))
                fresh = hubcheck.check(hub / "registry" / "projects", "h/h", gh, date(2026, 1, 3))
            finally:
                hubcheck.Source.from_entry = real
            kinds = {f["kind"] for f in found}
            self.assertEqual(kinds, {"registry-mismatch", "assessment-stale"}, found)
            self.assertIn("DISCOVERY.md", [f for f in found if f["kind"] == "assessment-stale"][0]["detail"])
            # Within a week, changes on an active project are only noted.
            self.assertEqual({f["kind"] for f in fresh}, {"registry-mismatch", "assessment-changes"})

    def test_adapter_drift_only_when_paths_go(self):
        from discover import hubcheck
        edited = {"files": [{"filename": "docs/p.md", "status": "modified"}]}
        moved = {"files": [{"filename": "docs/p.md", "status": "renamed"}]}
        self.assertEqual(hubcheck.changed_since("o/r", "a1", "b2", ["docs/p.md"], lambda p: edited, gone_only=True), [])
        self.assertEqual(hubcheck.changed_since("o/r", "a1", "b2", ["docs/p.md"], lambda p: moved, gone_only=True), ["docs/p.md"])

        def gh(path):
            if "docs/gone.md" in path:
                raise RuntimeError("404")
            return {}
        self.assertEqual(hubcheck.missing_at("o/r", "b2", ["docs/p.md", "docs/gone.md", "research/*/"], gh), ["docs/gone.md"])

    def test_issue_sync_opens_updates_and_closes(self):
        from discover import hubcheck
        calls = []

        class Out:
            stdout = json.dumps([{"number": 7, "title": "[hub-check] gone: adapter-drift", "body": "x"},
                                 {"number": 8, "title": "[hub-check] p: assessment-stale", "body": "old"}])

        def run(args, **kw):
            calls.append(args[:3])
            return Out()
        found = [{"slug": "p", "kind": "assessment-stale", "severity": "warning", "title": "t", "detail": "d"},
                 {"slug": "q", "kind": "opted-out", "severity": "error", "title": "t", "detail": "d"},
                 {"slug": "r", "kind": "not-assessed", "severity": "info", "title": "t", "detail": "d"}]
        done = hubcheck.sync_issues(found, "h/h", run)
        self.assertEqual(sorted(a for a, _ in done), ["closed", "opened", "updated"])
        self.assertNotIn("] r:", " ".join(t for _, t in done))


class PresetTests(unittest.TestCase):
    def test_presets_merge_without_clobbering_and_are_idempotent(self):
        from discover import presets
        self.assertNotIn("allow", presets.settings("donor-local")["permissions"])
        local_deny = presets.PRESETS["donor-local"]["deny"]
        for write in ("Bash(git push *)", "Bash(gh pr create *)", "Bash(gh pr merge *)"):
            self.assertIn(write, local_deny)
            self.assertNotIn(write, presets.PRESETS["donor-local"]["allow"])
        self.assertIn("Bash(gh pr merge *)", presets.PRESETS["donor-post"]["deny"])
        self.assertEqual(presets.PRESETS["maintainer"]["allow"], [])  # maintainers are asked, not bypassed
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / ".claude" / "settings.local.json"
            f.parent.mkdir()
            f.write_text(json.dumps({"model": "x", "permissions": {"allow": ["Read"]}}))
            self.assertTrue(presets.merge_into(f, "maintainer"))
            self.assertEqual(presets.merge_into(f, "maintainer"), [])
            s = json.loads(f.read_text())
            self.assertEqual(s["model"], "x")
            self.assertIn("Read", s["permissions"]["allow"])
            self.assertIn("Bash(gh pr merge *)", s["permissions"]["ask"])


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
        overlay = {"manifest_origin": "adapter", "manifest": {"hubs": [{"hub": "Hub/Repo", "list": True}]}}
        self.assertEqual(hub.listing_state(nominated, hub.consent_record(none, overlay, "Hub/Repo")), "nominated")

    def test_start_prompt_quotes_the_problem(self):
        from discover import prompt
        text = prompt.start_prompt('  Is X "open"?\n', local=True, site="https://h/")
        self.assertTrue(text.startswith("Fetch https://h/v0/start.md"))
        self.assertIn("Mode: local", text)
        self.assertTrue(text.endswith('<<<\nIs X "open"?\n>>>'))
        self.assertNotIn("Mode: local", prompt.start_prompt("p", site="https://h/"))
        import io, contextlib
        with contextlib.redirect_stdout(io.StringIO()) as buf:
            self.assertEqual(main(["prompt", "--action", "start", "--problem", "p"]), 0)
        self.assertIn("v0/start.md", buf.getvalue())

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
