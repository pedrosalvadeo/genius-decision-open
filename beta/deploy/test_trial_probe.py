"""Focal author checks. Real engine/SQLite locally, not a cloud/UID assertion."""
import contextlib
import copy
import importlib.util
import json
import os
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import patch

DEPLOY = Path(__file__).resolve().parent
sys.path.insert(0, str(DEPLOY))
import trial_probe as probe


class TrialProbeTests(unittest.TestCase):
    def metadata(self):
        return dict(source_commit='a' * 40, run_id='author-local', deployment_id='local-not-cloud')

    def test_real_engine_persistence_restore_and_no_destructive_rerun(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / 'trial'
            initial = probe.seed(root, self.metadata())
            self.assertEqual(initial['engine_profiles'], ['hours', 'fdq'])
            self.assertEqual(initial['synthetic_owner_rows_seeded'], 2)
            with contextlib.closing(sqlite3.connect(root / 'live.sqlite3')) as db:
                actual = json.loads(db.execute('SELECT result_json FROM jobs WHERE id=?', ('kept',)).fetchone()[0])
            wrong = copy.deepcopy(actual)
            wrong['response']['decisions'][0]['state'] = 'PR_UNKNOWN'
            with self.assertRaisesRegex(probe.ProbeError, 'UNEXPECTED_DECISION'):
                probe.check_expected('hours-known', wrong)
            wrong = copy.deepcopy(actual)
            wrong['response']['decisions'][0]['answers'][0]['value']['assigned']['value'] = '0/1'
            with self.assertRaisesRegex(probe.ProbeError, 'UNEXPECTED_FORMAL_VALUES'):
                probe.check_expected('hours-known', wrong)
            before = probe.fingerprint(root / 'live.sqlite3')
            with self.assertRaises(FileExistsError):
                probe.seed(root, self.metadata())
            self.assertEqual(probe.fingerprint(root / 'live.sqlite3'), before)
            result = probe.verify(root, self.metadata())
            self.assertTrue(result['deletion_ledger_preserved'])
            self.assertTrue(result['credentials_and_consent_revoked'])
            self.assertTrue(result['artifact_preserved'])
            with self.assertRaisesRegex(probe.ProbeError, 'VERIFY_ALREADY_COMPLETED'):
                probe.verify(root, self.metadata())
            self.assertEqual(probe.fingerprint(root / 'live.sqlite3'), before)

    def test_verify_missing_or_changed_seed_fails_without_creating_data(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / 'missing'
            with self.assertRaisesRegex(probe.ProbeError, 'TRIAL_DIRECTORY_INVALID'):
                probe.verify(root, self.metadata())
            self.assertFalse(root.exists())
            root.mkdir()
            probe.record(root / 'seed.json', dict(self.metadata(), phase='seed', status='PASS'))
            with self.assertRaisesRegex(probe.ProbeError, 'SOURCE_OR_RUN_CHANGED'):
                probe.verify(root, dict(self.metadata(), source_commit='b' * 40))
            self.assertFalse((root / 'live.sqlite3').exists())

    def test_cloud_entry_requires_explicit_source_phase_and_mount(self):
        environment = dict(GENIUS_TRIAL_PHASE='seed', GENIUS_TRIAL_RUN_ID='author-local',
                           GENIUS_TRIAL_EXPECTED_COMMIT='a' * 40, RAILWAY_GIT_COMMIT_SHA='a' * 40,
                           GENIUS_ENV='production', GENIUS_DATA_DIR='/data/genius',
                           GENIUS_PUBLIC_URL='https://trial.invalid',
                           RAILWAY_SERVICE_ID='synthetic', RAILWAY_PROJECT_ID='synthetic')
        with patch.dict(os.environ, environment, clear=True), patch.object(probe.start, 'prepare_identity') as identity:
            with patch.object(probe.start.os.path, 'ismount', return_value=False):
                with self.assertRaisesRegex(RuntimeError, 'mounted at /data'):
                    probe.main()
            identity.assert_not_called()
            os.environ['GENIUS_TRIAL_PHASE'] = ''
            with self.assertRaisesRegex(probe.ProbeError, 'EXPLICIT_PHASE_REQUIRED'):
                probe.main()
            os.environ['GENIUS_TRIAL_PHASE'] = 'seed'
            os.environ['RAILWAY_GIT_COMMIT_SHA'] = 'b' * 40
            with self.assertRaisesRegex(probe.ProbeError, 'RECEIVED_SOURCE_MISMATCH'):
                probe.main()

    def test_production_legal_configuration_still_rejects_empty_identity(self):
        from genius_beta.config import settings
        with patch.dict(os.environ, {'GENIUS_ENV': 'production', 'GENIUS_PUBLIC_URL': 'https://trial.invalid'}, clear=True):
            with self.assertRaises(ValueError) as error:
                settings()
            self.assertEqual(str(error.exception), probe.LEGAL_ERROR)


if __name__ == '__main__':
    unittest.main(verbosity=2)
