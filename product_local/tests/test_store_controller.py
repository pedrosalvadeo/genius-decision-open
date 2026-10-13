import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
import subprocess
import sys
import copy
import shutil
from unittest.mock import patch

from genius_local.store import Store, CorruptStore, ConflictError, UnsafePath, StoreError
from genius_local import controller


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "case"
        self.store = Store(self.root)

    def test_bytes_and_chain_are_preserved_and_reloaded(self):
        raw = b'{ "exact": "9007199254740993/7" }\n'
        artifact = self.store.put_bytes(raw)
        first = self.store.commit({"artifact": artifact}, None)
        second = self.store.commit({"status": "COMPLETE"}, first["sha256"])
        fresh = Store(self.root)
        self.assertEqual(fresh.get_bytes(artifact["sha256"]), raw)
        chain = fresh.load_chain()
        self.assertEqual([item["revision"] for item in chain], [1, 2])
        self.assertEqual(chain[1]["parent"], first["sha256"])
        self.assertEqual(chain[1]["sha256"], second["sha256"])
        self.assertEqual(fresh.put_bytes(raw), artifact)

    def test_parent_conflict_never_rewrites_previous_revision(self):
        first = self.store.commit({"x": 1}, None)
        raw = (self.root / first["path"]).read_bytes()
        with self.assertRaises(ConflictError):
            self.store.commit({"x": 2}, None)
        self.assertEqual((self.root / first["path"]).read_bytes(), raw)
        self.assertEqual(self.store.head(), first["sha256"])

    def test_interruption_before_head_preserves_previous_commit_and_orphan(self):
        first = self.store.commit({"x": 1}, None)
        with patch("genius_local.store.os.replace", side_effect=OSError("injected pre-commit interruption")):
            with self.assertRaises(OSError):
                self.store.commit({"x": 2}, first["sha256"])
        state = Store(self.root).inspect()
        self.assertEqual(state["head"], first["sha256"])
        self.assertEqual(len(state["uncommitted_revisions"]), 1)
        self.assertEqual(len(state["revisions"]), 1)

    def test_interruption_after_head_is_reconstructible(self):
        original = os.replace
        def replace_then_fail(source, target):
            original(source, target)
            raise OSError("injected lost commit acknowledgement")
        with patch("genius_local.store.os.replace", side_effect=replace_then_fail):
            with self.assertRaises(OSError):
                self.store.commit({"status": "RUNNING"}, None)
        chain = Store(self.root).load_chain()
        self.assertEqual(len(chain), 1)
        self.assertEqual(chain[0]["payload"]["status"], "RUNNING")

    def test_corrupt_artifact_or_revision_is_never_ignored(self):
        obj = self.store.put_bytes(b"original")
        ref = self.store.commit({"artifact": obj}, None)
        (self.root / obj["path"]).write_bytes(b"corrupt")
        with self.assertRaises(CorruptStore):
            self.store.load_chain()
        (self.root / obj["path"]).write_bytes(b"original")
        (self.root / ref["path"]).write_bytes(b"corrupt")
        with self.assertRaises(CorruptStore):
            self.store.load_chain()

    def test_missing_committed_artifact_is_detected(self):
        obj = self.store.put_bytes(b"original")
        self.store.commit({"artifact": obj}, None)
        (self.root / obj["path"]).unlink()
        with self.assertRaises(CorruptStore):
            self.store.load_chain()

    def test_symlink_and_digest_traversal_are_rejected(self):
        with self.assertRaises(UnsafePath):
            self.store.get_bytes("../outside")
        external = Path(self.temp.name) / "outside"
        external.write_bytes(b"external")
        digest = hashlib.sha256(b"external").hexdigest()
        (self.root / "objects" / digest).symlink_to(external)
        with self.assertRaises(UnsafePath):
            self.store.get_bytes(digest)
        link = Path(self.temp.name) / "link"
        link.symlink_to(self.root, target_is_directory=True)
        with self.assertRaises(UnsafePath):
            Store(link)

    def test_size_limit_and_active_writer(self):
        with self.assertRaises(StoreError):
            self.store.put_bytes(b"x" * (8 * 1024 * 1024 + 1))
        with self.store._commit_lock():
            with self.assertRaises(ConflictError):
                self.store.commit({"x": 1}, None)

    def test_process_death_releases_lock_and_preserves_precommit_state(self):
        first = self.store.commit({"status": "RUNNING"}, None)
        script = """
import os, sys
from genius_local.store import Store
store = Store(sys.argv[1])
original = os.replace
def die_before_replace(source, target):
    os._exit(17)
os.replace = die_before_replace
store.commit({'status': 'COMPLETE'}, store.head())
"""
        result = subprocess.run([sys.executable, "-c", script, str(self.root)], timeout=5, capture_output=True)
        self.assertEqual(result.returncode, 17, result.stderr)
        fresh = Store(self.root)
        self.assertEqual(fresh.head(), first["sha256"])
        self.assertEqual(len(fresh.inspect()["uncommitted_revisions"]), 1)
        recovered = fresh.commit({"status": "UNKNOWN", "reason": "operation had no receipt"}, first["sha256"])
        self.assertEqual(recovered["revision"], 2)


class ControllerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.fixture = self.root / "request"
        shutil.copytree(Path(__file__).resolve().parents[1] / "examples" / "hours", self.fixture)
        self.request = self.fixture / "request.json"
        self.case = self.root / "case"

    def run_request(self):
        # Contract hours does not consume Kernel/FDQ dependencies; these paths
        # are explicit unused values, never inferred workspace baselines.
        return controller.execute(self.request, self.case, self.root, self.root)

    def write_request(self, data):
        self.request.write_text(json.dumps(data), encoding="utf-8")

    def test_controller_process_death_orphan_recover_and_explicit_retry(self):
        script = """
import os, sys
from genius_local.controller import execute
original = os.replace
counter = [0]
def die_on_outcome_commit(source, target):
    counter[0] += 1
    if counter[0] == 3:
        os._exit(23)
    original(source, target)
os.replace = die_on_outcome_commit
execute(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[3])
"""
        result = subprocess.run([sys.executable, "-c", script, str(self.request), str(self.case), str(self.root)], timeout=10, capture_output=True)
        self.assertEqual(result.returncode, 23, result.stderr)
        interrupted = controller.inspect(self.case)
        self.assertEqual(interrupted["latest"]["active_operation"], "OP1")
        self.assertEqual(interrupted["latest"]["outcomes"], [])
        self.assertEqual(len(interrupted["uncommitted_revisions"]), 1)
        recovered = controller.recover(self.case)
        self.assertEqual(recovered["execution"]["state"], "PE_UNKNOWN")
        self.assertNotEqual(recovered["decisions"][0]["state"], "PR_JUSTIFIED_RESULT")
        head = Store(self.case).load_chain()[-1]
        request = json.loads(self.request.read_text())
        request.update(revision=2, supersedes={"revision": head["revision"], "sha256": head["sha256"]}, novelty={"reason": "RETRY_INTERRUPTED_OPERATION", "changed_refs": ["OP1"]})
        self.write_request(request)
        answer = self.run_request()
        self.assertEqual(answer["execution"]["state"], "PE_COMPLETE")
        self.assertEqual(answer["decisions"][0]["state"], "PR_JUSTIFIED_RESULT")
        self.assertEqual(len(Store(self.case).inspect()["uncommitted_revisions"]), 1)

    def test_response_budget_commits_explicit_closure_and_unpublished_bytes(self):
        with patch("genius_local.controller.MAX_RESPONSE", 100):
            with self.assertRaises(controller.PublicationBudgetExceeded):
                self.run_request()
        latest = controller.inspect(self.case)["latest"]
        self.assertEqual(latest["phase"], "BUDGET_CLOSED")
        self.assertEqual(latest["execution"]["state"], "PE_BUDGET_EXHAUSTED")
        self.assertNotIn("response", latest)
        raw = controller._read_chunks(Store(self.case), latest["unpublished_response_ref"])
        self.assertEqual(json.loads(raw)["decisions"][0]["state"], "PR_JUSTIFIED_RESULT")
        with self.assertRaises(controller.PublicationBudgetExceeded):
            controller.recover(self.case)

    def test_snapshot_budget_is_explicit_and_chunk_hash_is_verified(self):
        with patch("genius_local.controller.MAX_SNAPSHOT", 100):
            with self.assertRaises(controller.PublicationBudgetExceeded):
                self.run_request()
        latest = controller.inspect(self.case)["latest"]
        self.assertEqual(latest["phase"], "BUDGET_CLOSED")
        self.assertEqual(latest["closure_reason"], "SNAPSHOT_SIZE_BUDGET_EXHAUSTED")
        store = Store(self.case)
        raw = b"x" * (8 * 1024 * 1024 + 1)
        ref = controller._store_chunks(store, raw)
        self.assertEqual(len(ref["chunks"]), 2)
        self.assertEqual(controller._read_chunks(store, ref), raw)
        ref["sha256"] = "0" * 64
        with self.assertRaises(controller.ControllerError):
            controller._read_chunks(store, ref)

    def test_shared_dependency_dag_novelty_is_bounded(self):
        raw, request, artifacts = controller._import_request(self.request)
        template = request["obligations"][0]
        obligations = []
        for index in range(80):
            item = copy.deepcopy(template)
            item["id"] = "O" + str(index)
            item["dependencies"] = [{"ref": "O" + str(prior), "revision": 1, "role": "input"} for prior in (index - 1, index - 2) if prior >= 0]
            obligations.append(item)
        request["obligations"] = obligations
        request["queries"][0]["obligation_refs"] = [item["id"] for item in obligations]
        request["operations"][0]["obligation_refs"] = ["O79"]
        semantic = controller._semantic_request(request, artifacts)
        self.assertEqual(len(semantic["obligations"]), 80)
        self.assertTrue(all(isinstance(signature, str) and len(signature) == 64 for signature in semantic["obligations"]))

    def test_reused_receipt_does_not_count_as_new_progress(self):
        self.assertFalse(controller._has_progress([{"status": "CONDITIONAL", "evidence": [{"type": "LOCAL_RECEIPT_REUSE"}]}]))
        self.assertTrue(controller._has_progress([{"status": "CONDITIONAL", "evidence": [{"type": "NEW_COMPUTATION"}]}]))


if __name__ == "__main__":
    unittest.main()
