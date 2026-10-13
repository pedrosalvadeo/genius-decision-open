"""Focal PID/lifecycle regression tests; no Docker/UID/cloud claims."""
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

DEPLOY = Path(__file__).resolve().parent
ROOT = DEPLOY.parents[1]
sys.path.insert(0, str(DEPLOY))
import trial_supervisor as supervisor


class TrialSupervisorTests(unittest.TestCase):
    def test_received_engine_rejects_pid1_parent_metadata(self):
        with tempfile.TemporaryDirectory() as temp:
            env = {'PATH': os.defpath, 'PYTHONPATH': str(ROOT / 'beta'),
                   'GENIUS_WORKER_PID': '1', 'PYTHONDONTWRITEBYTECODE': '1'}
            result = subprocess.run([sys.executable, '-m', 'genius_beta.engine_job', temp],
                                    input=(ROOT / 'beta/examples/hours-known.json').read_bytes(),
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                    env=env, start_new_session=True, timeout=5)
            self.assertEqual(result.returncode, 1)
            self.assertIn(b'Invalid engine process supervision', result.stderr)
            self.assertEqual(result.stdout, b'')

    def test_supervised_probe_has_noninit_pid_real_oracles_and_exit_status(self):
        with tempfile.TemporaryDirectory() as temp:
            report = Path(temp) / 'report.json'
            script = '''import json,os,sys
from pathlib import Path
sys.path.insert(0,sys.argv[1])
import trial_probe
for name in ('hours-known','fdq-frontier'):
    trial_probe.engine(name,Path(sys.argv[2]))
Path(sys.argv[3]).write_text(json.dumps(dict(pid=os.getpid(),ppid=os.getppid(),real_oracles_matched=True)))
'''
            result = supervisor.supervise([sys.executable, '-c', script, str(DEPLOY), temp, str(report)], timeout=10)
            self.assertEqual(result, 0)
            value = json.loads(report.read_text())
            self.assertGreater(value['pid'], 1)
            self.assertEqual(value['ppid'], os.getpid())
            self.assertTrue(value['real_oracles_matched'])
            self.assertEqual(supervisor.supervise([sys.executable, '-c', 'raise SystemExit(7)'], timeout=2), 7)

    def test_supervisor_checks_source_before_bootstrap_or_child(self):
        env = dict(GENIUS_TRIAL_PHASE='seed', GENIUS_TRIAL_RUN_ID='author-local',
                   GENIUS_TRIAL_EXPECTED_COMMIT='a' * 40, RAILWAY_GIT_COMMIT_SHA='b' * 40)
        with patch.dict(os.environ, env, clear=True), patch.object(supervisor.start, 'prepare_identity') as identity, patch.object(supervisor.subprocess, 'Popen') as child:
            with self.assertRaisesRegex(supervisor.trial_probe.ProbeError, 'RECEIVED_SOURCE_MISMATCH'):
                supervisor.main()
            identity.assert_not_called()
            child.assert_not_called()

    def test_noninit_supervisor_fails_before_bootstrap_or_child(self):
        env = dict(GENIUS_TRIAL_PHASE='seed', GENIUS_TRIAL_RUN_ID='author-local',
                   GENIUS_TRIAL_EXPECTED_COMMIT='a' * 40, RAILWAY_GIT_COMMIT_SHA='a' * 40,
                   GENIUS_ENV='production', GENIUS_DATA_DIR='/data/genius',
                   GENIUS_PUBLIC_URL='https://trial.invalid',
                   RAILWAY_SERVICE_ID='synthetic', RAILWAY_PROJECT_ID='synthetic')
        with patch.dict(os.environ, env, clear=True), patch.object(supervisor.os, 'getpid', return_value=2), patch.object(supervisor.start, 'validate_runtime_environment') as runtime, patch.object(supervisor.start, 'prepare_identity') as identity, patch.object(supervisor.subprocess, 'Popen') as child:
            with self.assertRaisesRegex(supervisor.trial_probe.ProbeError, 'SUPERVISOR_REQUIRES_PID1'):
                supervisor.main()
            runtime.assert_not_called()
            identity.assert_not_called()
            child.assert_not_called()

    def test_timeout_escalates_when_probe_ignores_term(self):
        with tempfile.TemporaryDirectory() as temp:
            ready = Path(temp) / 'ready'
            script = "import signal,sys,time; from pathlib import Path; signal.signal(signal.SIGTERM,lambda *_:None); Path(sys.argv[1]).touch(); time.sleep(60)"
            status = supervisor.supervise([sys.executable, '-c', script, str(ready)], timeout=0.5, grace=0.1)
            self.assertTrue(ready.exists())
            self.assertEqual(status, 128 + signal.SIGKILL)

    def test_signal_and_timeout_reap_real_guarded_descendants(self):
        # A dedicated subreaper reproduces PID-1 adoption semantics, not PID=1.
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            engine = directory / 'guarded_engine.py'
            engine.write_text('''import os,signal,subprocess,sys,time
from pathlib import Path
from genius_beta.engine_job import install_parent_death_guard
install_parent_death_guard()
signal.signal(signal.SIGTERM,lambda *_:None)
child=subprocess.Popen([sys.executable,'-c','import time; time.sleep(60)'])
Path(sys.argv[1]).write_text('ready')
time.sleep(60)
''')
            probe = directory / 'controlled_probe.py'
            probe.write_text('''import os,subprocess,sys,time
env={'PATH':os.defpath,'PYTHONPATH':sys.argv[1],'GENIUS_WORKER_PID':str(os.getpid())}
subprocess.Popen([sys.executable,sys.argv[2],sys.argv[3]],env=env,start_new_session=True)
time.sleep(60)
''')
            harness = directory / 'supervisor_harness.py'
            harness.write_text('''import ctypes,json,os,sys
from pathlib import Path
sys.path.insert(0,sys.argv[1])
import trial_supervisor
# Linux PR_SET_CHILD_SUBREAPER=36, isolated to this fixture process.
if ctypes.CDLL(None,use_errno=True).prctl(36,1,0,0,0)!=0: raise RuntimeError('subreaper unavailable')
rc=trial_supervisor.supervise([sys.executable,sys.argv[2],sys.argv[3],sys.argv[4],sys.argv[5]],timeout=float(sys.argv[6]),grace=2)
try: os.waitpid(-1,os.WNOHANG)
except ChildProcessError: clean=True
else: clean=False
Path(sys.argv[7]).write_text(json.dumps(dict(returncode=rc,no_children=clean)))
''')
            for mode in ('signal', 'timeout'):
                with self.subTest(mode=mode):
                    ready, report = directory / (mode + '.ready'), directory / (mode + '.json')
                    process = subprocess.Popen([sys.executable, str(harness), str(DEPLOY), str(probe), str(ROOT / 'beta'), str(engine), str(ready), '10' if mode == 'signal' else '0.5', str(report)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    try:
                        deadline = time.monotonic() + 3
                        while not ready.exists() and process.poll() is None and time.monotonic() < deadline:
                            time.sleep(0.01)
                        self.assertTrue(ready.exists(), 'guarded subtree did not start')
                        if mode == 'signal':
                            process.send_signal(signal.SIGTERM)
                        output, errors = process.communicate(timeout=5)
                        self.assertEqual(process.returncode, 0, errors.decode())
                        self.assertEqual(output, b'')
                        value = json.loads(report.read_text())
                        self.assertEqual(value['returncode'], 128 + signal.SIGTERM)
                        self.assertTrue(value['no_children'])
                    finally:
                        if process.poll() is None:
                            process.kill()
                            process.wait(timeout=3)


if __name__ == '__main__':
    unittest.main(verbosity=2)
