"""Bounded local model execution; no network, provider, or external side effect.

The child receives an explicit model through stdin. It loads a registered
compiler, not code from the request. A file size limit bounds native artifacts.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile

from .envelope import pack, unpack


class ProcessEvaluator:
    def __init__(self, timeout=90, memory_mb=384, output_bytes=67108864):
        self.timeout = int(timeout)
        self.memory_mb = int(memory_mb)
        self.output_bytes = int(output_bytes)
        if not 1 <= self.timeout <= 300 or not 128 <= self.memory_mb <= 2048 or not 1024 <= self.output_bytes <= 134217728:
            raise ValueError('Invalid execution limits')

    def __call__(self, model):
        encoded = json.dumps(model, ensure_ascii=False, allow_nan=False, separators=(',', ':')).encode()
        if len(encoded) > 262144:
            raise ValueError('Model exceeds the execution input limit')
        root = Path(__file__).resolve().parents[2]
        env = {k: v for k, v in os.environ.items() if k in ('PATH', 'LANG', 'LC_ALL', 'TMPDIR', 'PYTHONPATH')}
        env['PYTHONPATH'] = os.pathsep.join([str(root/'twin'), str(root/'kernel'), env.get('PYTHONPATH', '')])
        # Imports run under RLIMIT_FSIZE; a cached .pyc written there can be truncated.
        env['PYTHONDONTWRITEBYTECODE'] = '1'
        cmd = [sys.executable, '-m', 'genius_twin.process_runner', '--child',
               '--parent', str(os.getpid()), '--seconds', str(self.timeout),
               '--memory', str(self.memory_mb), '--output', str(self.output_bytes)]
        with tempfile.TemporaryFile() as output:
            try:
                completed = subprocess.run(cmd, input=encoded, stdout=output,
                                           stderr=subprocess.DEVNULL, env=env,
                                           timeout=self.timeout, check=False)
            except subprocess.TimeoutExpired as exc:
                raise TimeoutError('Execution deadline exceeded; no mathematical result was received') from exc
            if completed.returncode != 0:
                raise RuntimeError('Execution interrupted or failed; no mathematical conclusion follows')
            if output.tell() > self.output_bytes:
                raise RuntimeError('Execution artifact exceeds its limit')
            output.seek(0)
            result = unpack(json.load(output))
        if type(result) is not dict or 'canonical_results' not in result or 'native_result' not in result:
            raise RuntimeError('Invalid compiler envelope')
        return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--child', action='store_true', required=True)
    parser.add_argument('--parent', type=int, required=True)
    parser.add_argument('--seconds', type=int, required=True)
    parser.add_argument('--memory', type=int, required=True)
    parser.add_argument('--output', type=int, required=True)
    args = parser.parse_args()
    # Linux deployment: ensure a killed web worker cannot leave a compiler alive.
    if sys.platform == 'linux':
        import ctypes
        if ctypes.CDLL(None, use_errno=True).prctl(1, signal.SIGKILL, 0, 0, 0) != 0:
            raise RuntimeError('Cannot install parent-death boundary')
        if os.getppid() != args.parent:
            raise RuntimeError('Parent exited before execution boundary')
    import resource
    memory = args.memory * 1024 * 1024
    resource.setrlimit(resource.RLIMIT_AS, (memory, memory))
    resource.setrlimit(resource.RLIMIT_CPU, (args.seconds + 1, args.seconds + 1))
    resource.setrlimit(resource.RLIMIT_FSIZE, (args.output, args.output))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    model = json.loads(sys.stdin.buffer.read(262145))
    from .registry import evaluate
    result = evaluate(model)
    # Packed: the output limit counts each native Result once.
    json.dump(pack(result), sys.stdout, ensure_ascii=False, allow_nan=False, separators=(',', ':'))


if __name__ == '__main__':
    main()
