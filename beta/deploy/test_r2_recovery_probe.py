import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location('r2_recovery_probe', Path(__file__).with_name('r2_recovery_probe.py'))
probe = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(probe)


class Transport:
    def __init__(self):
        self.objects = {'snapshots/untouched.gcm': b'production sentinel',
                        'privacy/untouched.gcm': b'privacy sentinel'}
        self.calls = []
    def list(self, prefix):
        self.calls.append(('list', prefix))
        return [{'key': key, 'size': len(value)} for key, value in self.objects.items() if key.startswith(prefix)]
    def put(self, key, path):
        self.calls.append(('put', key))
        self.objects[key] = Path(path).read_bytes()
    def get(self, key, path, maximum):
        self.calls.append(('get', key))
        value = self.objects[key]
        if len(value) > maximum:
            raise probe.r2.BackupError('DOWNLOAD_LIMIT')
        with Path(path).open('xb') as file:
            file.write(value)


class ProbeTests(unittest.TestCase):
    def test_loss_recovery_uses_only_two_ciphertexts_in_probe_namespace(self):
        transport = Transport()
        result = probe.run_fixture(transport, os.urandom(32), '20261005T000000Z_1234abcd')
        self.assertEqual(result['status'], 'PASS')
        self.assertEqual(result['uploaded_objects'], 2)
        self.assertLess(result['uploaded_bytes'], probe.MAX_PROBE_UPLOAD)
        self.assertTrue(all(key.startswith('probes/') for _, key in transport.calls))
        self.assertEqual(transport.objects['snapshots/untouched.gcm'], b'production sentinel')
        self.assertEqual(transport.objects['privacy/untouched.gcm'], b'privacy sentinel')
        for key, value in transport.objects.items():
            if key.startswith('probes/'):
                self.assertTrue(value.startswith(probe.r2.MAGIC))
                self.assertNotIn(b'SYNTHETIC-NO-LOGIN', value)

    def test_adapter_rejects_escape_plaintext_and_extra_uploads(self):
        transport = Transport()
        store = probe.ProbeStore(transport, '20261005T000000Z_1234abcd')
        for key in ('snapshots/../escape.gcm', 'probes/direct.gcm', '/data/genius'):
            with self.assertRaises(probe.r2.BackupError):
                store.physical(key)
        with tempfile.TemporaryDirectory() as folder:
            file = Path(folder) / 'data'
            file.write_bytes(b'plaintext')
            with self.assertRaisesRegex(probe.r2.BackupError, 'PROBE_REQUIRES_CIPHERTEXT'):
                store.put('snapshots/test.gcm', file)
            self.assertEqual(store.puts, 0)
            file.write_bytes(probe.r2.MAGIC + b'fixture')
            store.put('snapshots/test.gcm', file)
            store.put('privacy/test.gcm', file)
            with self.assertRaisesRegex(probe.r2.BackupError, 'PROBE_UPLOAD_BUDGET'):
                store.put('snapshots/third.gcm', file)

    def test_cli_redacts_errors_and_keeps_remote_failure_nonzero(self):
        env = {'GENIUS_R2_BACKUP_ENABLED': 'false', 'GENIUS_REGISTRATION_OPEN': 'false',
               'GENIUS_R2_ACCOUNT_ID': probe.ACCOUNT}
        output = io.StringIO()
        with patch.dict(os.environ, env), patch.object(os, 'geteuid', return_value=10001), \
             patch.object(probe.r2, 'encryption_key', return_value=b'x' * 32), \
             patch.object(probe.r2, 'R2Store', side_effect=RuntimeError('SECRET-MUST-NOT-ESCAPE')), \
             contextlib.redirect_stdout(output):
            self.assertEqual(probe.main(), 1)
        self.assertNotIn('SECRET-MUST-NOT-ESCAPE', output.getvalue())
        self.assertEqual(json.loads(output.getvalue())['code'], 'PROBE_INTERNAL_ERROR')

    def test_cli_rejects_open_registration_enabled_backups_and_wrong_account(self):
        baseline = {'GENIUS_R2_BACKUP_ENABLED': 'false', 'GENIUS_REGISTRATION_OPEN': 'false',
                    'GENIUS_R2_ACCOUNT_ID': probe.ACCOUNT}
        for name, value, code in (
            ('GENIUS_R2_BACKUP_ENABLED', 'true', 'PROBE_BACKUPS_MUST_BE_DISABLED'),
            ('GENIUS_REGISTRATION_OPEN', 'true', 'PROBE_REGISTRATION_MUST_BE_CLOSED'),
            ('GENIUS_R2_ACCOUNT_ID', 'wrong', 'PROBE_ACCOUNT_MISMATCH'),
        ):
            output = io.StringIO()
            with self.subTest(name=name), patch.dict(os.environ, {**baseline, name: value}), \
                 patch.object(os, 'geteuid', return_value=10001), \
                 patch.object(probe.r2, 'R2Store') as remote, contextlib.redirect_stdout(output):
                self.assertEqual(probe.main(), 1)
                remote.assert_not_called()
            self.assertEqual(json.loads(output.getvalue())['code'], code)


if __name__ == '__main__':
    unittest.main()
