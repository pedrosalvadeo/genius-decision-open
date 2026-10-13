"""Author tests: controls and recovery, not an independent acceptance audit.

Run: PYTHONPATH=infrastructure python3 infrastructure/tests/test_storage.py OUT
The optional new evidence directory keeps every negative/positive store.
"""
import errno
import base64
import json
import os
from pathlib import Path
import signal
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from genius_infra import storage

EVIDENCE = None
CONTAINMENT = None


def portable_snapshot(base):
    """Describe special files; never publish live symlinks/FIFOs in a handoff."""
    entries = []
    for current, directories, files in os.walk(base, followlinks=False):
        for name in sorted(directories + files):
            path = Path(current) / name
            info = path.lstat()
            entry = {"path": str(path.relative_to(base)), "mode": oct(stat.S_IMODE(info.st_mode)),
                     "links": info.st_nlink}
            if stat.S_ISLNK(info.st_mode):
                entry.update(type="symlink", target=os.readlink(path))
            elif stat.S_ISDIR(info.st_mode):
                entry["type"] = "directory"
            elif stat.S_ISREG(info.st_mode):
                raw = path.read_bytes()
                entry.update(type="file", bytes=len(raw), base64=base64.b64encode(raw).decode(),
                             sha256=storage._record(raw)["sha256"])
            elif stat.S_ISFIFO(info.st_mode):
                entry["type"] = "fifo"
            else:
                entry["type"] = "other"
            entries.append(entry)
    return {"format": "genius-author-fixture-snapshot/1.0", "entries": entries,
            "note": "Special files are descriptions; test source reconstructs the controls."}


class StorageTests(unittest.TestCase):
    def setUp(self):
        if EVIDENCE:
            self.base = EVIDENCE / self._testMethodName
            self.base.mkdir(mode=0o700)
        else:
            self.base = Path(tempfile.mkdtemp(prefix="genius-data-test-"))
        self.store = storage.Store.create(self.base / "store")
        self.stores = [self.store]

    def tearDown(self):
        for store in self.stores:
            store.close()

    def run_pair(self, source=None):
        source = source or self.store
        with source.exclusive():
            tx = source.begin({"input.json": b' { "n":"9007199254740993/7", "x":"e\\u0301" }\r\n'},
                              {"profile": "local-fp1-v1", "kernel": "GENIUS-KERNEL-1.0.1"})
            tx.add({"result.json": b'{"checks":[],"opaque":"bytes only"}\n'})
            return tx.commit({"operational_status": "DELIVERED"})

    def test_01_exact_bytes_and_no_overwrite(self):
        raw = b'\xff\x00unicode-invalid-but-byte-exact\r\n'
        with self.store.exclusive():
            tx = self.store.begin({"input.json": raw}, {})
            with self.assertRaisesRegex(storage.StoreError, "NO_OVERWRITE"):
                tx.add({"input.json": b"different"})
            tx.add({"result.json": b' { "q" : "9007199254740993/7" }\n'})
            run = tx.commit({"operational_status": "DELIVERED"})
            self.assertEqual(self.store.verify()["status"], "PASS")
        self.assertEqual((self.store.path / "runs" / run / "input.json").read_bytes(), raw)

    def test_02_lock_other_process_and_release(self):
        code = """from genius_infra.storage import Store, BusyError
import sys
s=Store(sys.argv[1])
try:
 with s.exclusive(): print('ACQUIRED')
except BusyError: print('BUSY')
finally: s.close()
"""
        with self.store.exclusive():
            child = subprocess.run([sys.executable, "-B", "-c", code, str(self.store.path)],
                                   capture_output=True, text=True, timeout=5)
            self.assertEqual(child.stdout.strip(), "BUSY", child.stderr)
        child = subprocess.run([sys.executable, "-B", "-c", code, str(self.store.path)],
                               capture_output=True, text=True, timeout=5)
        self.assertEqual(child.stdout.strip(), "ACQUIRED", child.stderr)

    def test_03_paths_and_artifact_traversal(self):
        with self.store.exclusive():
            tx = self.store.begin({}, {})
            for name in ("../escape", "/tmp/escape", "nested/file", ".hidden", "outcome.json", "MANIFEST.json"):
                with self.subTest(name=name), self.assertRaises(storage.StoreError):
                    tx.add({name: b"untrusted"})
        with self.assertRaises(storage.StoreError):
            storage.Store(self.base / "store" / ".." / "store")
        self.assertFalse((self.base / "escape").exists())

    def test_04_symlink_root_ancestor_and_artifact(self):
        os.symlink(self.store.path, self.base / "alias")
        with self.assertRaises(OSError):
            storage.Store(self.base / "alias")
        os.symlink(self.base, self.base / "parentalias")
        with self.assertRaises(OSError):
            storage.Store.create(self.base / "parentalias" / "escaped")
        run = self.run_pair()
        path = self.store.path / "runs" / run / "result.json"
        path.rename(path.with_name("evidence.original"))
        os.symlink(path.with_name("evidence.original"), path)
        with self.store.exclusive(), self.assertRaises(OSError):
            self.store.verify()

    def test_05_hardlink_and_fifo_rejected(self):
        run = self.run_pair()
        path = self.store.path / "runs" / run / "input.json"
        os.link(path, self.base / "outside-hardlink")
        with self.store.exclusive(), self.assertRaisesRegex(storage.StoreError, "HARDLINK"):
            self.store.verify()
        os.unlink(self.base / "outside-hardlink")
        os.mkfifo(path.parent / "fifo", mode=0o600)
        with self.store.exclusive(), self.assertRaisesRegex(storage.StoreError, "OWNER_OR_TYPE"):
            self.store.verify()

    def test_06_owner_modes_and_actual_permission_denied(self):
        self.store.path.chmod(0o755)
        with self.assertRaisesRegex(storage.StoreError, "PERMISSIONS"):
            storage.Store(self.store.path)
        self.store.path.chmod(0o700)
        denied = self.base / "denied"
        denied.mkdir(mode=0o500)
        with self.assertRaises(PermissionError):
            storage.Store.create(denied / "new")

    def test_07_corruption_missing_extra_detected(self):
        run = self.run_pair()
        path = self.store.path / "runs" / run / "result.json"
        original = path.read_bytes()
        path.write_bytes(original + b"corrupt")
        with self.store.exclusive(), self.assertRaisesRegex(storage.StoreError, "INTEGRITY"):
            self.store.verify()
        path.write_bytes(original)
        path.rename(path.with_name("unlisted.json"))
        with self.store.exclusive(), self.assertRaisesRegex(storage.StoreError, "INTEGRITY"):
            self.store.verify()
        path.with_name("unlisted.json").rename(path)
        extra = path.with_name("extra.json")
        extra.write_bytes(b"extra")
        extra.chmod(0o600)
        with self.store.exclusive(), self.assertRaisesRegex(storage.StoreError, "INTEGRITY"):
            self.store.verify()

    def test_08_real_process_kill_preserves_pending(self):
        code = """from genius_infra.storage import Store
import sys,signal
s=Store(sys.argv[1])
with s.exclusive():
 t=s.begin({'input.json':b'exact accepted bytes'}, {'method':'evaluate'})
 print(t.run_id, flush=True)
 signal.pause()
"""
        process = subprocess.Popen([sys.executable, "-B", "-c", code, str(self.store.path)],
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        import select
        ready, _, _ = select.select([process.stdout], [], [], 5)
        self.assertTrue(ready)
        run_id = process.stdout.readline().strip()
        self.assertTrue(storage.RUN_NAME.fullmatch(run_id))
        process.kill()
        _, stderr = process.communicate(timeout=5)
        self.assertEqual(process.returncode, -signal.SIGKILL, stderr)
        with self.store.exclusive():
            report = self.store.verify()
        self.assertEqual(report["runs"], [])
        self.assertEqual(report["incomplete"][0]["run_id"], run_id)
        self.assertEqual((self.store.path / "staging" / run_id / "input.json").read_bytes(), b"exact accepted bytes")

    def test_09_injected_enospc_partial_never_committed(self):
        real_write = os.write
        calls = 0
        def limited_write(fd, raw):
            nonlocal calls
            calls += 1
            if calls == 1:
                return real_write(fd, raw[:3])
            raise OSError(errno.ENOSPC, "INJECTED disk full")
        with self.store.exclusive():
            tx = self.store.begin({"input.json": b"input"}, {})
            with mock.patch.object(storage.os, "write", limited_write):
                with self.assertRaises(OSError) as raised:
                    tx.add({"result.json": b"long-result-in-progress"})
            self.assertEqual(raised.exception.errno, errno.ENOSPC)
            with self.assertRaisesRegex(storage.StoreError, "INACTIVE_TRANSACTION"):
                tx.commit({"operational_status": "DELIVERED"})
            report = self.store.verify()
        self.assertFalse(report["runs"])
        self.assertEqual(len(report["incomplete"]), 1)
        self.assertEqual((self.store.path / "staging" / tx.run_id / "result.json").read_bytes(), b"lon")

    def test_10_backup_restore_and_data_rollback(self):
        first = self.run_pair()
        with self.store.exclusive():
            pending = self.store.begin({"input.json": b"pending"}, {})
            original = self.store.verify()
            backup_report = self.store.backup(self.base / "backup")
        self.assertEqual(backup_report["status"], "PASS")
        second = self.run_pair()
        restored = storage.Store.restore(self.base / "backup", self.base / "restored")
        self.stores.append(restored)
        with restored.exclusive():
            self.assertEqual(restored.verify(), original)
        with self.store.exclusive():
            self.assertEqual([r["run_id"] for r in self.store.verify()["runs"]], sorted([first, second]))
        with self.assertRaises(FileExistsError):
            storage.Store.restore(self.base / "backup", self.base / "restored")
        self.assertEqual((restored.path / "staging" / pending.run_id / "input.json").read_bytes(), b"pending")

    def test_11_corrupt_backup_and_malicious_manifest(self):
        run = self.run_pair()
        with self.store.exclusive():
            self.store.backup(self.base / "backup")
        path = self.base / "backup" / "runs" / run / "result.json"
        path.write_bytes(b"corrupt snapshot")
        with self.assertRaises(storage.StoreError):
            storage.Store.restore(self.base / "backup", self.base / "restored")
        self.assertFalse((self.base / "restored").exists())
        manifest = self.base / "backup" / "BACKUP.json"
        obj = json.loads(manifest.read_bytes())
        obj["files"]["../../outside"] = {"bytes": 1, "sha256": "0" * 64}
        manifest.write_bytes(storage.json_bytes(obj))
        with self.assertRaises(storage.StoreError):
            storage.Store.restore(self.base / "backup", self.base / "restored")
        self.assertFalse((self.base / "restored").exists())

    def test_12_backup_interruption_incomplete_not_restorable(self):
        self.run_pair()
        real_write = storage._write
        count = 0
        def fail_after_two(fd, name, raw):
            nonlocal count
            count += 1
            if count == 3:
                raise OSError(errno.EIO, "INJECTED interrupted backup")
            return real_write(fd, name, raw)
        with self.store.exclusive(), mock.patch.object(storage, "_write", fail_after_two):
            with self.assertRaises(OSError):
                self.store.backup(self.base / "backup")
        self.assertFalse((self.base / "backup" / "BACKUP.json").exists())
        with self.assertRaises(storage.StoreError):
            storage.Store.restore(self.base / "backup", self.base / "restored")

    def test_13_limits_and_lock_requirement(self):
        with self.assertRaises(storage.StoreError):
            self.store.begin({}, {})
        with self.assertRaises(storage.StoreError):
            storage.Store.create(self.base / "too-big", max_runs=129)
        small = storage.Store.create(self.base / "small", max_file_bytes=2048,
                                     max_run_bytes=8192, max_store_bytes=16384, max_runs=1)
        self.stores.append(small)
        with small.exclusive():
            tx = small.begin({"input.json": b"ok"}, {})
            with self.assertRaisesRegex(storage.StoreError, "LIMIT"):
                tx.add({"big.bin": b"a" * 2049})
            tx.commit({})
            with self.assertRaisesRegex(storage.StoreError, "COUNT_LIMIT"):
                small.begin({}, {})

    def test_14_post_rename_sync_failure_is_not_acknowledged(self):
        with self.store.exclusive():
            tx = self.store.begin({"input.json": b"input"}, {})
            runs_inode = os.stat(self.store.path / "runs").st_ino
            real_fsync = os.fsync
            def fail_runs_sync(fd):
                if os.fstat(fd).st_ino == runs_inode:
                    raise OSError(errno.EIO, "INJECTED post-rename fsync")
                return real_fsync(fd)
            with mock.patch.object(storage.os, "fsync", fail_runs_sync):
                with self.assertRaises(OSError):
                    tx.commit({"operational_status": "FAILED"})
            report = self.store.verify()
        self.assertEqual(len(report["runs"]), 1)
        self.assertFalse(report["incomplete"])

    def test_15_backup_empty_directory_inventory(self):
        self.run_pair()
        with self.store.exclusive():
            self.store.backup(self.base / "backup")
        (self.base / "backup" / "staging" / ("run-" + "0" * 32)).mkdir(mode=0o700)
        with self.assertRaisesRegex(storage.StoreError, "INTEGRITY"):
            storage.Store.restore(self.base / "backup", self.base / "restored")

    def test_16_artifact_count_and_metadata_duplicates(self):
        with self.store.exclusive():
            tx = self.store.begin({}, {})
            with self.assertRaisesRegex(storage.StoreError, "COUNT_LIMIT"):
                tx.add({f"f{i}": b"a" for i in range(33)})
        config = self.store.path / "store.json"
        original = config.read_bytes()
        config.write_bytes(b'{"format":"bad","format":"bad","limits":{}}')
        with self.assertRaisesRegex(storage.StoreError, "DUPLICATE"):
            storage.Store(self.store.path)
        (self.base / "config-original.bin").write_bytes(original)

    def test_17_nested_destinations_cannot_mutate_sources(self):
        self.run_pair()
        with self.store.exclusive():
            before = self.store.verify()
            with self.assertRaisesRegex(storage.StoreError, "DESTINATION_INSIDE_SOURCE"):
                self.store.backup(self.store.path / "nested")
            self.assertEqual(self.store.verify(), before)
            self.store.backup(self.base / "backup")
        with self.assertRaisesRegex(storage.StoreError, "DESTINATION_INSIDE_SOURCE"):
            storage.Store.restore(self.base / "backup", self.base / "backup" / "nested")
        self.assertFalse((self.store.path / "nested").exists())
        self.assertFalse((self.base / "backup" / "nested").exists())
        restored = storage.Store.restore(self.base / "backup", self.base / "restored")
        self.stores.append(restored)
        with restored.exclusive():
            self.assertEqual(restored.verify(), before)


if __name__ == "__main__":
    if "--laboratory-root" in sys.argv:
        sys.argv.remove("--laboratory-root")
        from genius_infra.worker import enter_lab_containment
        CONTAINMENT = enter_lab_containment()
    if len(sys.argv) > 1 and not sys.argv[1].startswith("-"):
        EVIDENCE = Path(os.path.abspath(sys.argv.pop(1)))
        EVIDENCE.mkdir(mode=0o700)
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(StorageTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    failed_names = {case._testMethodName for case, _ in result.failures + result.errors}
    passed_names = [name for name in unittest.defaultTestLoader.getTestCaseNames(StorageTests) if name not in failed_names]
    report = {"role": "author", "independent_audit": False,
              "tests": result.testsRun, "failures": len(result.failures), "errors": len(result.errors),
              "status": "PASS" if result.wasSuccessful() else "FAIL", "euid": os.geteuid(),
              "containment": CONTAINMENT,
              "python": sys.version, "fault_injections": ["ENOSPC partial write", "backup EIO", "post-rename fsync EIO"],
              "passed_cases": passed_names,
              "actual_controls": [label for name, label in [
                  ("test_08_real_process_kill_preserves_pending", "SIGKILL child"),
                  ("test_02_lock_other_process_and_release", "flock child"),
                  ("test_06_owner_modes_and_actual_permission_denied", "filesystem permissions"),
                  ("test_04_symlink_root_ancestor_and_artifact", "symlink"),
                  ("test_05_hardlink_and_fifo_rejected", "hardlink and FIFO")]
                  if name in passed_names],
              "details": [{"case": str(case), "traceback": trace} for case, trace in result.failures + result.errors]}
    if EVIDENCE:
        (EVIDENCE / "REPORT.json").write_bytes(storage.json_bytes(report))
        (EVIDENCE / "SNAPSHOT.json").write_bytes(storage.json_bytes(portable_snapshot(EVIDENCE)))
    print(json.dumps(report, indent=2))
    sys.exit(0 if result.wasSuccessful() else 1)
