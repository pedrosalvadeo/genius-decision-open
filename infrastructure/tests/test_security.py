"""Author security cases. Run non-root or explicit UID0LAB opt-in; outputs in a NEW directory.

Trusted probes use the product interpreter flags and common containment code.
They are explicit synthetic peers, not adversarial FP1 mathematical instances.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict, replace
import hashlib
import json
import os
from pathlib import Path
import signal
import select
import subprocess
import sys
import threading
import time
import traceback
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'infrastructure'))
from genius_infra import supervisor as subject

MIB = 1024 ** 2
BASE = subject.SupervisorLimits(cpu_seconds=3, address_space_bytes=64*MIB,
    wall_seconds=5.0, max_stdout_bytes=128*1024, max_stderr_bytes=16*1024)
ORIGINAL_COMMAND = subject._worker_command
LAB = False
READY_DIR = None


def command(mode, limits):
    # Reuse flags of the real product launcher, replace only trusted entrypoint.
    original = ORIGINAL_COMMAND(limits)
    return original[:4] + [str(ROOT/'infrastructure/tests/fixtures/security_probe.py'),
        '--root', str(ROOT), '--mode', mode, '--cpu', str(limits.cpu_seconds),
        '--memory', str(limits.address_space_bytes), '--parent', str(os.getpid())] + (
            ['--lab-single-uid-root'] if LAB else []) + (
            ['--ready-dir', str(READY_DIR)] if READY_DIR else [])


def run_probe(mode, limits=BASE, cancel_event=None):
    with patch.object(subject, '_worker_command', lambda actual, **kwargs: command(mode, actual)):
        return subject.run_worker('evaluate', b'{}', limits=limits, cancel_event=cancel_event,
                                  lab_single_uid_root=LAB)


def was_reaped(pid):
    # waitpid/kill use our PID namespace. Mounted /proc numeric paths do not
    # necessarily use that namespace, and cannot identify this child here.
    try:
        os.waitpid(pid, os.WNOHANG)
    except ChildProcessError:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return True
    return False


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def source_map():
    paths = [Path(__file__), ROOT/'infrastructure/tests/fixtures/security_probe.py',
        ROOT/'infrastructure/genius_infra/supervisor.py', ROOT/'infrastructure/genius_infra/worker.py']
    return {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}


def save_outcome(dest, outcome):
    for name, data in outcome.artifacts.items():
        (dest/name).write_bytes(data)
    (dest/'outcome.json').write_text(json.dumps(outcome.metadata, indent=2)+'\n')
    require(outcome.status != 'DELIVERED', 'Synthetic failed peer became DELIVERED')
    require('result.json' not in outcome.artifacts, 'Operational failure forged a mathematical Result')
    require(outcome.metadata['result_or_report_received'] is False, 'Failure invented result receipt')
    require(was_reaped(outcome.metadata['worker_pid']), 'Supervisor did not reap worker')


def cases():
    def cpu(dest):
        limits = replace(BASE, cpu_seconds=1)
        outcome = run_probe('cpu', limits)
        save_outcome(dest, outcome)
        require(outcome.reason == 'EXIT_NONZERO', outcome.reason)
        require(outcome.metadata['signal'] in (signal.SIGKILL, signal.SIGXCPU), 'CPU signal missing')
        require(outcome.metadata['wall_seconds'] < limits.wall_seconds, 'Wall timeout hid CPU control')
        return {'observed_signal': outcome.metadata['signal'], 'fixture': 'CPU spinner, CPU=1s'}

    def memory(dest):
        outcome = run_probe('memory')
        save_outcome(dest, outcome)
        require(outcome.reason == 'EXIT_NONZERO', outcome.reason)
        require(outcome.metadata['returncode'] == 74, 'Allocation was not caught by AS limit')
        require(b'MEMORY_LIMIT_OBSERVED' in outcome.artifacts['worker.stderr'], 'No memory witness')
        return {'fixture': '128MiB allocation under 64MiB AS; controlled MemoryError'}

    def wall(dest):
        limits = replace(BASE, wall_seconds=0.35)
        outcome = run_probe('sleep', limits)
        save_outcome(dest, outcome)
        require(outcome.reason == 'WALL_LIMIT', outcome.reason)
        require(outcome.metadata['wall_seconds'] < 2.0, 'Deadline not bounded in observed environment')
        return {'fixture': '30s sleep under 0.35s wall budget'}

    def output(dest):
        limits = replace(BASE, max_stdout_bytes=8192)
        outcome = run_probe('stdout', limits)
        save_outcome(dest, outcome)
        require(outcome.reason == 'STDOUT_LIMIT', outcome.reason)
        require(len(outcome.artifacts['worker.stdout']) == limits.max_stdout_bytes, 'Output cap not enforced')
        require(outcome.metadata['stdout_is_prefix'], 'Truncation evidence missing')
        return {'retained_bytes': len(outcome.artifacts['worker.stdout'])}

    def error_output(dest):
        limits = replace(BASE, max_stderr_bytes=4096)
        outcome = run_probe('stderr', limits)
        save_outcome(dest, outcome)
        require(outcome.reason == 'STDERR_LIMIT', outcome.reason)
        require(len(outcome.artifacts['worker.stderr']) == limits.max_stderr_bytes, 'Stderr cap not enforced')
        require(outcome.metadata['stderr_is_prefix'], 'Truncation evidence missing')
        return {'retained_bytes': len(outcome.artifacts['worker.stderr'])}

    def partial(dest):
        outcome = run_probe('partial')
        save_outcome(dest, outcome)
        require(outcome.reason == 'TRANSPORT_INCOMPLETE_OR_INVALID', outcome.reason)
        return {'fixture': 'Complete handshake, partial operation JSON, clean EOF'}

    def foreign_id(dest):
        outcome = run_probe('foreign_id')
        save_outcome(dest, outcome)
        require(outcome.reason == 'TRANSPORT_INCOMPLETE_OR_INVALID', outcome.reason)
        return {'fixture': 'Complete handshake and response with foreign RPC id'}

    def shape(dest):
        outcome = run_probe('malformed_result')
        save_outcome(dest, outcome)
        require(outcome.reason == 'TRANSPORT_INCOMPLETE_OR_INVALID', outcome.reason)
        return {'fixture': 'Valid envelope; Result lacks mandatory top-level fields'}

    def incompatible(dest):
        outcome = run_probe('incompatible')
        save_outcome(dest, outcome)
        require(outcome.reason == 'INITIALIZATION_INVALID', outcome.reason)
        require(not any(e['event'] == 'operation_sent' for e in outcome.metadata['events']),
                'Input sent before compatible negotiation')
        require(b'INSTANCE_REACHED' not in outcome.artifacts['worker.stderr'], 'Peer received instance')
        return {'fixture': 'Unsupported wire version; no instance transmitted'}

    def cancel(dest):
        event = threading.Event()
        timer = threading.Timer(0.25, event.set)
        timer.start()
        try:
            outcome = run_probe('sleep', cancel_event=event)
        finally:
            timer.cancel()
        save_outcome(dest, outcome)
        require(outcome.reason == 'CANCELLED' and outcome.status == 'CANCELLED', outcome.reason)
        return {'fixture': 'Cancellation event during sleeping peer'}

    def environment(dest):
        request = b'{"jsonrpc":"2.0","id":"f5-job","method":"genius.evaluate","params":{}}\n'
        # Markers are synthetic, never real user credentials.
        marker_dir = dest/'injected_imports'
        marker_dir.mkdir()
        (marker_dir/'sitecustomize.py').write_text('raise RuntimeError("SYNTHETIC_IMPORT_INJECTION")\n')
        with patch.dict(os.environ, {'GENIUS_SECURITY_SYNTHETIC_SECRET': 'NOT_A_REAL_SECRET',
                                     'PYTHONPATH': str(marker_dir)}):
            captured = subject._run_process(command('inspect', BASE), request_bytes=request, limits=BASE)
        (dest/'worker.stdout').write_bytes(captured.stdout)
        (dest/'worker.stderr').write_bytes(captured.stderr)
        require(captured.reason == 'OK', captured.reason)
        lines = captured.stdout.splitlines()
        require(len(lines) == 2, 'Probe expected exactly two replies')
        report = json.loads(lines[1])['result']
        (dest/'observed.json').write_text(json.dumps(report, indent=2)+'\n')
        if LAB:
            snap = report['identity_snapshot']
            require(report['uid'] == 0, 'Lab UID identity hidden')
            require(snap['NoNewPrivs'] == '1', 'NNP absent')
            try:
                subject.run_worker('evaluate', b'{}', limits=BASE)
            except PermissionError:
                pass
            else:
                raise AssertionError('Normal API admitted root after lab privilege reduction')
            require(all(int(snap[k], 16) == 0 for k in ('CapEff','CapPrm','CapInh','CapAmb')),
                    'Capabilities retained')
        else:
            require(report['uid'] != 0, 'Worker root')
        require(report['isolated'] == 1 and report['no_site'] == 1 and report['dont_write_bytecode'],
                'Required interpreter isolation flags absent')
        require(not report['sentinel_visible'] and not report['pythonpath_visible'], 'Parent env leaked')
        require(report['limits']['RLIMIT_CPU'] == [BASE.cpu_seconds]*2, 'CPU soft/hard mismatch')
        require(report['limits']['RLIMIT_AS'] == [BASE.address_space_bytes]*2, 'AS soft/hard mismatch')
        for name, value in [('RLIMIT_CORE', 0), ('RLIMIT_FSIZE', 0), ('RLIMIT_NOFILE', 32)]:
            require(report['limits'][name] == [value]*2, name)
        require(report['nofile_observed'], 'No EMFILE witness')
        require(report['file_limit_observed'] and report['file_size'] == 0, 'No FSIZE witness')
        require(was_reaped(captured.worker_pid), 'Probe not reaped')
        return {'fixture': 'Synthetic env markers; actual rlimits, EMFILE and EFBIG'}

    def parent_death(dest):
        ready = dest/'worker_ready'
        ready.mkdir()
        parent = subprocess.Popen([sys.executable, '-I', '-S', '-B', str(Path(__file__).resolve()),
                                   '--parent-only', '--parent-ready-dir', str(ready.resolve())] +
                                  (['--lab-single-uid-root'] if LAB else []),
                                  stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                  env={'PATH': '/usr/bin:/bin', 'LANG': 'C.UTF-8'}, start_new_session=True)
        worker_pid = None
        pidfd = None
        try:
            deadline = time.monotonic()+4
            while time.monotonic() < deadline:
                markers = list(ready.iterdir())
                if markers:
                    worker_pid = int(markers[0].name)
                    break
                if parent.poll() is not None:
                    break
                time.sleep(0.01)
            require(worker_pid is not None, 'Worker did not signal post-bootstrap readiness')
            pidfd = os.pidfd_open(worker_pid)
            parent.kill()
            parent.wait(timeout=2)
            readable, _, _ = select.select([pidfd], [], [], 2)
            require(bool(readable), 'Worker survived parent SIGKILL')
            observation = {'parent_pid': parent.pid, 'worker_pid': worker_pid,
                           'parent_returncode': parent.returncode, 'pidfd_exit_observed': True,
                           'post_bootstrap_readiness_observed': True,
                           'method': 'Linux pidfd readiness; does not depend on mounted proc PID namespace',
                           'reaper_of_orphan_not_claimed': True}
            (dest/'observed.json').write_text(json.dumps(observation, indent=2)+'\n')
            return observation
        finally:
            if parent.poll() is None:
                parent.kill()
                parent.wait(timeout=2)
            if worker_pid and pidfd is not None:
                ready_fds, _, _ = select.select([pidfd], [], [], 0)
                if not ready_fds:
                    os.kill(worker_pid, signal.SIGKILL)
                os.close(pidfd)
            out, err = parent.communicate(timeout=2)
            (dest/'parent.stdout').write_bytes(out)
            (dest/'parent.stderr').write_bytes(err)

    return [('SEC5-CPU', cpu), ('SEC5-AS', memory), ('SEC5-WALL', wall),
            ('SEC5-OUT', output), ('SEC5-ERR', error_output), ('SEC5-PARTIAL', partial),
            ('SEC5-ID', foreign_id), ('SEC5-SHAPE', shape), ('SEC5-NEGOTIATE', incompatible), ('SEC5-CANCEL', cancel),
            ('SEC5-ENV', environment), ('SEC5-PARENT', parent_death)]


def main():
    global LAB, READY_DIR
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', type=Path)
    ap.add_argument('--parent-only', action='store_true')
    ap.add_argument('--parent-ready-dir', type=Path)
    ap.add_argument('--lab-single-uid-root', action='store_true')
    args = ap.parse_args()
    LAB = args.lab_single_uid_root
    READY_DIR = args.parent_ready_dir
    if LAB:
        from genius_infra.worker import enter_lab_containment
        enter_lab_containment()
    elif os.geteuid() == 0:
        raise SystemExit('Run as non-root or explicit --lab-single-uid-root in authorized namespace')
    if args.parent_only:
        run_probe('parent', replace(BASE, wall_seconds=20))
        return 77
    if args.out is None:
        ap.error('--out is required')
    args.out.mkdir(parents=False, exist_ok=False)
    initial_sources = source_map()
    results = []
    for case_id, operation in cases():
        dest = args.out/case_id
        dest.mkdir()
        started = time.monotonic()
        try:
            observation = operation(dest)
            result = {'id': case_id, 'status': 'PASS', 'observations': observation}
        except Exception:
            result = {'id': case_id, 'status': 'FAIL', 'traceback': traceback.format_exc()}
        result['wall_seconds'] = time.monotonic()-started
        (dest/'case.json').write_text(json.dumps(result, indent=2)+'\n')
        results.append(result)
    final_sources = source_map()
    passed = all(x['status'] == 'PASS' for x in results) and initial_sources == final_sources
    report = {'suite': 'F5_SECURITY_AUTHOR', 'passed': passed, 'count': len(results),
              'passed_count': sum(x['status'] == 'PASS' for x in results),
              'uid': os.geteuid(), 'lab_single_uid_root': LAB, 'python': sys.version, 'platform': sys.platform,
              'limits_default': asdict(BASE), 'sources_before': initial_sources,
              'sources_after': final_sources, 'sources_unchanged': initial_sources == final_sources,
              'scope': 'Trusted synthetic peers testing shared F5 controls; not external audit or adversarial FP1 computation',
              'cases': results}
    (args.out/'SUMMARY.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({'passed': passed, 'count': len(results), 'passed_count': report['passed_count']}))
    return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main())
