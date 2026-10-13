"""Exercise real SQLite recovery, including deletion and revoked consent."""
import contextlib
from datetime import datetime, timedelta, timezone
import importlib.util
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'beta'))
from genius_beta.db import initialize

spec = importlib.util.spec_from_file_location('genius_backup', Path(__file__).with_name('backup.py'))
backup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(backup)


class RecoveryTests(unittest.TestCase):
    def test_restore_does_not_resurrect_deleted_accounts_or_permissions(self):
        with tempfile.TemporaryDirectory() as directory:
            live, saved, restored = [Path(directory) / name for name in ('live.sqlite3', 'saved.sqlite3', 'restored.sqlite3')]
            initialize(live)
            now = int(time.time())
            with contextlib.closing(sqlite3.connect(live)) as db:
                for user in ('kept', 'deleted'):
                    db.execute('INSERT INTO users VALUES(?,?,?,?,?,?)', (user, user, 'synthetic-password-hash', now, now, 'test'))
                    db.execute('INSERT INTO consents VALUES(?,?,?,?)', (user, 1, 1, now))
                    db.execute('INSERT INTO sessions VALUES(?,?,?,?)', (user, user, 'synthetic-csrf', now + 3600))
                    db.execute('INSERT INTO api_tokens VALUES(?,?,?,?,?,?)', (user, user, user, 'synthetic', now, None))
                    db.execute('INSERT INTO cases VALUES(?,?,?,?,?,?,?,?)', (user, user, 'synthetic', 'hours', 'human', 1, now, now))
                    db.execute('INSERT INTO revisions VALUES(?,?,?,?,?)', (user, 1, '{}', 'synthetic', now))
                    db.execute('INSERT INTO jobs(id,case_id,revision,status,created_at) VALUES(?,?,?,?,?)', (user, user, 1, 'running', now))
                db.commit()
            backup.snapshot(live, saved)
            with contextlib.closing(sqlite3.connect(live)) as db:
                db.execute('PRAGMA foreign_keys=ON')
                db.execute('INSERT INTO deletion_ledger VALUES(?,?,?)', ('deleted', 'user', now))
                db.execute('DELETE FROM users WHERE id=?', ('deleted',))
                db.execute('UPDATE consents SET research=0,followup=0')
                db.commit()
            before = backup.digest(saved)
            backup.restore(saved, restored, live, services_stopped=True)
            with contextlib.closing(sqlite3.connect(restored)) as db:
                self.assertEqual(db.execute('SELECT id FROM users').fetchall(), [('kept',)])
                self.assertEqual(db.execute('SELECT id FROM cases').fetchall(), [('kept',)])
                self.assertEqual(db.execute('SELECT research,followup FROM consents').fetchall(), [(0, 0)])
                self.assertEqual(db.execute('SELECT COUNT(*) FROM api_tokens').fetchone()[0], 0)
                self.assertEqual(db.execute('SELECT COUNT(*) FROM sessions').fetchone()[0], 0)
                self.assertEqual(db.execute('SELECT status FROM jobs').fetchall(), [('interrupted',)])
                self.assertEqual(db.execute('PRAGMA integrity_check').fetchone()[0], 'ok')
            self.assertEqual(before, backup.digest(saved))

    def test_tamper_and_unsafe_restore_are_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            live, saved, restored = [Path(directory) / name for name in ('live.sqlite3', 'saved.sqlite3', 'restored.sqlite3')]
            initialize(live)
            backup.snapshot(live, saved)
            with self.assertRaises(RuntimeError):
                backup.restore(saved, restored, live)
            with saved.open('ab') as file:
                file.write(b'tamper')
            with self.assertRaisesRegex(RuntimeError, 'SHA256'):
                backup.restore(saved, restored, live, services_stopped=True)
            self.assertFalse(restored.exists())
            with self.assertRaises(FileExistsError):
                backup.snapshot(live, saved)

    def test_expired_backup_cannot_bypass_deletion_retention(self):
        with tempfile.TemporaryDirectory() as directory:
            live, saved, restored = [Path(directory) / name for name in ('live.sqlite3', 'saved.sqlite3', 'restored.sqlite3')]
            initialize(live)
            backup.snapshot(live, saved)
            manifest=backup.manifest_path(saved)
            doc=json.loads(manifest.read_text())
            doc['created_at']=(datetime.now(timezone.utc)-timedelta(days=8)).isoformat()
            manifest.write_text(json.dumps(doc))
            with self.assertRaisesRegex(RuntimeError,'seven-day'):
                backup.restore(saved, restored, live, services_stopped=True)
            self.assertFalse(restored.exists())


if __name__ == '__main__':
    unittest.main(verbosity=2)
