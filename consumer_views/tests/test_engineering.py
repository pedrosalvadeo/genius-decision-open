"""Focal author tests; independent-client suite supplies the semantic oracle."""
import base64
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent / "product_local"))
sys.path.insert(0, str(ROOT.parent / "product_local" / "tests"))
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "examples"))

from genius_local.controller import execute
from genius_local.store import Store, canonical
from genius_views import render_case, ViewError
from generate_cases import SCENARIOS, scenario_fixture
from test_acceptance import make_fdq, make_hours
from test_independent_client import VisibleOracle, leaves

WORK = ROOT.parents[1]
R0 = Path(os.environ.get("GENIUS_R0_BASELINE", WORK / "dependencies/R0_dependency/R0"))
R1 = Path(os.environ.get("GENIUS_R1_BASELINE", WORK / "dependencies/R1"))


class EngineeringTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def case(self):
        fixture = make_hours(self.root / "input")
        case = self.root / "case"
        response = execute(fixture.save(), case, R0, R1)
        return case, response

    def test_real_fdq_receipts_all_views_frozen_expectations(self):
        for name, family, kind, mutation, expected in SCENARIOS:
            with self.subTest(name=name):
                fixture = scenario_fixture(self.root / name / "input", family, kind, mutation, R0)
                case = self.root / name / "case"
                response = execute(fixture.save(), case, R0, R1)
                self.assertEqual(response["decisions"][0]["state"], expected)
                out = self.root / name / "views"
                render_case(case, out)
                self.assertEqual(json.loads((out / "app.json").read_text())["response"], response)
                self.assertEqual(json.loads((out / "agent.json").read_text())["response"], response)
                oracle = VisibleOracle()
                oracle.feed((out / "human.html").read_text())
                self.assertEqual(oracle.rows, dict(leaves(response)))
                self.assertIn("alcance formal y condicional", (out / "human.html").read_text())

    def test_witnesses_recover_exact_original_bytes_and_manifest(self):
        case, response = self.case()
        out = self.root / "views"
        render_case(case, out)
        manifest = json.loads((out / "manifest.json").read_text())
        for row in manifest["files"]:
            raw = (out / row["path"]).read_bytes()
            self.assertEqual(len(raw), row["size"])
            self.assertEqual(hashlib.sha256(raw).hexdigest(), row["sha256"])
        for path in (out / "witnesses").iterdir():
            witness = json.loads(path.read_text())
            raw = base64.b64decode(witness["bytes"], validate=True)
            self.assertEqual(raw, (case / "objects" / witness["sha256"]).read_bytes())

    def test_orphan_revision_preserved_and_not_promoted(self):
        case, response = self.case()
        store = Store(case)
        old_head = store.head()
        last = store.load_chain()[-1]
        payload = dict(last["payload"])
        payload["orphan_fixture_note"] = "SYNTHETIC_ORPHAN; no changed conclusion"
        new_head = store.commit(payload, old_head)["sha256"]
        (case / "HEAD").write_bytes(canonical({"format":"genius-local-head/0.1.0", "sha256":old_head}))
        out = self.root / "views"
        render_case(case, out)
        source = json.loads((out / "source.json").read_text())
        self.assertEqual(source["head"], old_head)
        self.assertEqual([row["sha256"] for row in source["uncommitted_revisions"]], [new_head])
        self.assertEqual(json.loads((out / "app.json").read_text())["response"], response)

    def test_floats_even_in_historical_envelope_rejected(self):
        case, _ = self.case()
        store = Store(case)
        latest = store.load_chain()[-1]
        payload = dict(latest["payload"])
        payload["untrusted_extra"] = {"number": 1.5}
        store.commit(payload, store.head())
        with self.assertRaises(Exception):
            render_case(case, self.root / "views")
        self.assertFalse((self.root / "views").exists())

    def test_unknown_historical_or_orphan_snapshot_version_rejected(self):
        case, _ = self.case()
        original = Store(case).load_chain()
        for mode in ("committed_history", "orphan"):
            with self.subTest(mode=mode):
                target = self.root / mode
                shutil.copytree(case, target)
                parent = None
                for index, entry in enumerate(original):
                    envelope = {key: value for key, value in entry.items() if key != "sha256"}
                    envelope["parent"] = parent
                    if index == 0:
                        envelope["payload"] = dict(envelope["payload"])
                        envelope["payload"]["storage_format"] = "genius-local-snapshot-refs/9.0.0"
                    raw = canonical(envelope)
                    parent = hashlib.sha256(raw).hexdigest()
                    (target / "revisions" / parent).write_bytes(raw)
                if mode == "committed_history":
                    (target / "HEAD").write_bytes(canonical({"format":"genius-local-head/0.1.0", "sha256":parent}))
                with self.assertRaisesRegex(ViewError, "UNSUPPORTED_SNAPSHOT_VERSION"):
                    render_case(target, self.root / (mode + "-view"))
                self.assertFalse((self.root / (mode + "-view")).exists())

    def test_root_and_output_budgets_fail_without_publication(self):
        case, _ = self.case()
        (case / "COMMIT_LOCK").write_bytes(b"x" * 1025)
        with self.assertRaisesRegex(ViewError, "ROOT_FILE_BYTE_BUDGET"):
            render_case(case, self.root / "views")
        (case / "COMMIT_LOCK").write_bytes(b"")
        with patch("genius_views.views.MAX_EXPORT_BYTES", 1):
            with self.assertRaisesRegex(ViewError, "EXPORT_BYTE_BUDGET"):
                render_case(case, self.root / "views")
        self.assertFalse((self.root / "views").exists())
        self.assertFalse(list(self.root.glob(".genius-view-*")))

    def test_missing_case_and_output_inside_source_never_mutate(self):
        with self.assertRaises(ViewError):
            render_case(self.root / "missing", self.root / "views")
        self.assertFalse((self.root / "missing").exists())
        case, _ = self.case()
        with self.assertRaisesRegex(ViewError, "OUTPUT_INSIDE_SOURCE"):
            render_case(case, case / "views")
        self.assertFalse((case / "views").exists())


if __name__ == "__main__":
    unittest.main()
