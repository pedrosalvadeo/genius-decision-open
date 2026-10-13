"""Bounded PID-1 supervisor for the no-socket synthetic probe.

The received engine requires its direct parent to have PID > 1. Keep that
guard unchanged: launch the probe as a child after validated non-root bootstrap.
"""
from __future__ import annotations

import contextlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

import start
import trial_probe


def signal_group(child, sig):
    with contextlib.suppress(ProcessLookupError):
        os.killpg(child.pid, sig)


def reap_adopted_children(grace):
    """As PID 1, collect descendants killed by the engine parent-death guard."""
    deadline = time.monotonic() + grace
    while True:
        try:
            pid, _status = os.waitpid(-1, os.WNOHANG)
        except ChildProcessError:
            return
        if pid:
            continue
        if time.monotonic() >= deadline:
            raise trial_probe.ProbeError('DESCENDANTS_NOT_REAPED')
        time.sleep(0.02)


def supervise(command, timeout=120, grace=5):
    stopping = False

    def stop(_signum, _frame):
        nonlocal stopping
        stopping = True

    previous = {sig: signal.signal(sig, stop) for sig in (signal.SIGTERM, signal.SIGINT)}
    child = None
    try:
        child = subprocess.Popen(command, start_new_session=True)
        deadline = time.monotonic() + timeout
        while child.poll() is None and not stopping and time.monotonic() < deadline:
            time.sleep(0.02)
        if child.poll() is None:
            signal_group(child, signal.SIGTERM)
            try:
                child.wait(timeout=grace)
            except subprocess.TimeoutExpired:
                signal_group(child, signal.SIGKILL)
                child.wait(timeout=grace)
        returncode = child.wait()
        reap_adopted_children(grace)
        return returncode if returncode >= 0 else 128 - returncode
    finally:
        if child is not None and child.poll() is None:
            signal_group(child, signal.SIGKILL)
            child.wait(timeout=grace)
        for sig, handler in previous.items():
            signal.signal(sig, handler)


def main():
    trial_probe.preflight()
    trial_probe.require(os.getpid() == 1, 'SUPERVISOR_REQUIRES_PID1')
    start.validate_runtime_environment()
    start.prepare_identity()
    trial_probe.require(os.geteuid() == 10001 and os.getegid() == 10001, 'UNEXPECTED_RUNTIME_IDENTITY')
    return supervise([sys.executable, str(Path(__file__).with_name('trial_probe.py'))])


if __name__ == '__main__':
    try:
        result = main()
    except Exception as error:
        code = str(error) if isinstance(error, trial_probe.ProbeError) else type(error).__name__
        print(json.dumps(dict(format='genius-internal-trial/1', status='FAIL', stage='supervisor', code=code), sort_keys=True), flush=True)
        raise SystemExit(1)
    raise SystemExit(result)
