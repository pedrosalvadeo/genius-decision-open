"""Recovery and effect semantics tested across actual Python process exits."""
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
for folder in ("adaptive", "twin", "kernel"):
    sys.path.insert(0, str(ROOT / folder))

from genius_adaptive.distribution import Distribution, inventory_of, prepare
from genius_adaptive.journal import Conflict, Journal, OutcomeUnknown, exclusive, publish
from genius_adaptive.runtime import run


class MissionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.source = self.root / "source"
        self.source.mkdir()
        subprocess.run(["git", "init", "-q", str(self.source)], check=True)
        (self.source / "README.txt").write_text("Genius: una misión observable.\n" * 100)
        (self.source / "run.sh").write_text("#!/bin/sh\nexit 0\n")
        (self.source / "run.sh").chmod(0o755)
        self.commit()
        self.state = self.root / "mission"
        prepare(self.source, self.sha, self.state)
        self.env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1",
                    "PYTHONPATH": os.pathsep.join(str(ROOT / f) for f in ("adaptive", "twin", "kernel")),
                    "LANGSMITH_TRACING": "false", "LANGCHAIN_TRACING_V2": "false"}

    def commit(self):
        subprocess.run(["git", "-C", str(self.source), "add", "."], check=True)
        subprocess.run(["git", "-C", str(self.source), "-c", "user.name=Mission Test",
                        "-c", "user.email=mission@example.invalid", "commit", "-qm", "fixture"], check=True)
        self.sha = subprocess.check_output(["git", "-C", str(self.source), "rev-parse", "HEAD"]).decode().strip()

    def child(self, program):
        return subprocess.run([sys.executable, "-c", program, str(self.state)],
                              env=self.env, capture_output=True, text=True, timeout=45)

    def crash(self, when):
        program = """
import os, sys
from pathlib import Path
from unittest.mock import patch
from genius_adaptive.distribution import Distribution
from genius_adaptive.journal import publish
from genius_adaptive.runtime import run
when = WHEN
def after(stage):
    if when == stage:
        os._exit(73)
def effect(path, raw):
    if Path(path).parent.name == 'delivery' and when == 'before_effect':
        os._exit(73)
    publish(path, raw)
    if Path(path).parent.name == 'delivery' and when == 'after_effect':
        os._exit(73)
with patch('genius_adaptive.distribution.publish', effect):
    run(Path(sys.argv[1]), Distribution(), after_stage=after)
""".replace("WHEN", repr(when))
        result = self.child(program)
        self.assertEqual(result.returncode, 73, result.stderr)

    def resume(self):
        result = self.child("from pathlib import Path; import sys,json; from genius_adaptive.runtime import run; "
                            "from genius_adaptive.distribution import Distribution; "
                            "print(json.dumps(run(Path(sys.argv[1]), Distribution())))")
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def test_complete_cycle_native_result_and_independent_round_trip(self):
        with patch("socket.create_connection", side_effect=AssertionError("No network expected")):
            result = run(self.state, Distribution())
        self.assertEqual(result["status"], "completed")
        journal = Journal(self.state / "journal.sqlite3")
        native = journal.get("evaluate")
        self.assertTrue(native["verification"]["valid"])
        self.assertEqual(result["memory"]["selected"], "gzip")
        # Read the final artifact independently of the adapter's decoder.
        with tarfile.open(self.state / "delivery/source.tar.gz") as archive:
            self.assertEqual(archive.extractfile("README.txt").read(), (self.source / "README.txt").read_bytes())
            self.assertEqual(archive.getmember("run.sh").mode, 0o755)
        observation = result["memory"]["observation"]
        self.assertEqual(observation["human_wellbeing_effect"], "UNMEASURED")
        self.assertEqual(observation["network_transfers"], 0)
        self.assertEqual(len(journal.export()["receipts"]), 6)

    def test_restart_after_receipt_before_checkpoint_does_not_remeasure(self):
        self.crash("measure")
        before = Journal(self.state / "journal.sqlite3").export()["receipts"]["measure"]
        self.resume()
        after = Journal(self.state / "journal.sqlite3").export()["receipts"]["measure"]
        self.assertEqual(before, after)

    def test_restart_after_decision_keeps_verified_choice(self):
        self.crash("evaluate")
        before = Journal(self.state / "journal.sqlite3").get("evaluate")
        self.resume()
        self.assertEqual(before, Journal(self.state / "journal.sqlite3").get("evaluate"))

    def test_unknown_effect_is_not_blindly_repeated(self):
        self.crash("before_effect")
        with self.assertRaises(OutcomeUnknown):
            run(self.state, Distribution())
        with self.assertRaises(OutcomeUnknown):
            run(self.state, Distribution())
        self.assertFalse((self.state / "delivery/source.tar.gz").exists())
        self.assertEqual(Journal(self.state / "journal.sqlite3").export()["effects"][0]["state"], "pending")

    def test_effect_completed_before_receipt_is_reconciled_without_rewrite(self):
        self.crash("after_effect")
        artifact = self.state / "delivery/source.tar.gz"
        stat = artifact.stat()
        self.resume()
        self.assertEqual(stat.st_ino, artifact.stat().st_ino)
        self.assertEqual(stat.st_mtime_ns, artifact.stat().st_mtime_ns)
        rows = Journal(self.state / "journal.sqlite3").export()["effects"]
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["state"], "confirmed")

    def test_completed_restart_reuses_result_and_revalidates_delivery(self):
        self.resume()
        before = Journal(self.state / "journal.sqlite3").export()
        self.assertTrue(self.resume()["reused"])
        self.assertEqual(before, Journal(self.state / "journal.sqlite3").export())
        (self.state / "delivery/source.tar.gz").write_bytes(b"damaged")
        with self.assertRaisesRegex(Conflict, "DELIVERY_READBACK_FAILED"):
            run(self.state, Distribution())

    def test_changed_source_is_not_reinterpreted_as_old_evidence(self):
        self.crash("measure")
        (self.state / "input/README.txt").write_text("changed")
        with self.assertRaisesRegex(Conflict, "SOURCE_BYTES_CHANGED"):
            run(self.state, Distribution())

    def test_changed_runtime_requires_explicit_new_mission(self):
        self.crash("measure")
        with patch("genius_adaptive.runtime.identity", return_value={"changed": True}):
            with self.assertRaisesRegex(Conflict, "MISSION_OR_RUNTIME_CHANGED"):
                run(self.state, Distribution())

    def test_changed_objective_cannot_reuse_prior_checkpoint(self):
        self.crash("measure")
        path = self.state / "mission.json"
        spec = json.loads(path.read_text()); spec["source_commit"] = "0" * 40
        path.write_text(json.dumps(spec))
        with self.assertRaisesRegex(Conflict, "MISSION_OR_RUNTIME_CHANGED"):
            run(self.state, Distribution())

    def test_concurrent_writer_is_rejected(self):
        with exclusive(self.state):
            with self.assertRaisesRegex(Conflict, "MISSION_BUSY"):
                run(self.state, Distribution())

    def test_unverified_choice_never_reaches_effect(self):
        from genius_twin.registry import evaluate as native
        def broken(model):
            result = native(model)
            result["canonical_results"]["decision"]["selected"] = "tar"
            return result
        with patch("genius_twin.registry.evaluate", broken):
            with self.assertRaisesRegex(ValueError, "NO_UNIQUE_VERIFIED_CHOICE"):
                run(self.state, Distribution())
        self.assertEqual(Journal(self.state / "journal.sqlite3").export()["effects"], [])

    def test_capture_uses_git_bytes_and_rejects_symlinks(self):
        (self.source / "README.txt").write_text("uncommitted content must not leak")
        other = self.root / "other"
        prepare(self.source, self.sha, other)
        self.assertEqual((other / "input/README.txt").read_bytes(), (self.state / "input/README.txt").read_bytes())
        (self.source / "link").symlink_to("README.txt")
        self.commit()
        with self.assertRaisesRegex(ValueError, "ONLY_REGULAR_GIT_FILES_SUPPORTED"):
            prepare(self.source, self.sha, self.root / "unsafe")

    def test_source_budget_checked_before_blob_allocation(self):
        with patch("genius_adaptive.distribution.MAX_INPUT_BYTES", 1):
            with self.assertRaisesRegex(ValueError, "SOURCE_BUDGET_EXCEEDED"):
                prepare(self.source, self.sha, self.root / "too_big")


class JournalTests(unittest.TestCase):
    def test_conflicting_effect_key_cannot_publish_a_second_action(self):
        with tempfile.TemporaryDirectory() as tmp:
            journal = Journal(Path(tmp) / "journal.sqlite3")
            calls = []
            effect = lambda: calls.append(1) or {"receipt": 1}
            journal.effect("send", {"to": "a"}, effect, lambda: None)
            journal.effect("send", {"to": "a"}, effect, lambda: None)
            with self.assertRaisesRegex(Conflict, "EFFECT_KEY_REUSED"):
                journal.effect("send", {"to": "b"}, effect, lambda: None)
            self.assertEqual(calls, [1])

    def test_conflicting_artifact_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "artifact"
            publish(path, b"original")
            with self.assertRaises(Conflict):
                publish(path, b"replacement")
            self.assertEqual(path.read_bytes(), b"original")

    def test_unsafe_archive_path_rejected_without_extraction(self):
        output = io.BytesIO()
        with tarfile.open(fileobj=output, mode="w") as archive:
            info = tarfile.TarInfo("../escape"); info.size = 1
            archive.addfile(info, io.BytesIO(b"x"))
        with self.assertRaisesRegex(ValueError, "UNSAFE_SOURCE_PATH"):
            inventory_of("tar", output.getvalue())


if __name__ == "__main__":
    unittest.main()
