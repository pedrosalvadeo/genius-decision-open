"""Trusted security peer. Never selected by the product CLI or FP1 payload."""
from __future__ import annotations

import argparse
import base64
import hashlib
import errno
import json
import os
from pathlib import Path
import resource
import runpy
import sys
import tempfile
import time


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', required=True)
    ap.add_argument('--mode', required=True)
    ap.add_argument('--cpu', required=True, type=int)
    ap.add_argument('--memory', required=True, type=int)
    ap.add_argument('--parent', required=True, type=int)
    ap.add_argument('--lab-single-uid-root', action='store_true')
    ap.add_argument('--ready-dir')
    args = ap.parse_args()
    root = Path(args.root)
    bootstrap = runpy.run_path(str(root / 'infrastructure/genius_infra/worker.py'),
                              run_name='security_probe_bootstrap')
    bootstrap['apply_containment'](args.cpu, args.memory, args.parent,
                                    lab_single_uid_root=args.lab_single_uid_root)
    sys.path[:0] = [str(root / 'kernel'), str(root / 'protocols')]
    from genius_protocols.server import initialization_result
    initial = json.loads(sys.stdin.buffer.readline())
    initialization = initialization_result()
    if args.mode == 'incompatible':
        initialization['protocol_version'] = 'unsupported-security-test/0'
    def emit(value):
        sys.stdout.buffer.write(json.dumps(value, separators=(',', ':')).encode() + b'\n')
        sys.stdout.buffer.flush()
    emit({'jsonrpc': '2.0', 'id': initial['id'], 'result': initialization})
    pending = sys.stdin.buffer.readline()
    if not pending:
        return 0
    request = json.loads(pending)
    if args.mode == 'incompatible':
        sys.stderr.buffer.write(b'INSTANCE_REACHED_INCOMPATIBLE_PEER\n')
        sys.stderr.buffer.flush()
        return 76
    if args.mode == 'cpu':
        while True:
            pass
    if args.mode in {'sleep', 'parent'}:
        if args.mode == 'parent':
            (Path(args.ready_dir) / str(os.getpid())).mkdir()
        time.sleep(30)
    elif args.mode == 'memory':
        try:
            bytearray(args.memory * 2)
        except MemoryError:
            sys.stderr.buffer.write(b'MEMORY_LIMIT_OBSERVED\n')
            sys.stderr.buffer.flush()
            return 74
        return 75
    elif args.mode == 'stdout':
        while True:
            os.write(1, b'x' * 65536)
    elif args.mode == 'stderr':
        while True:
            os.write(2, b'x' * 65536)
    elif args.mode == 'partial':
        os.write(1, b'{"jsonrpc":"2.0","id":')
        return 0
    elif args.mode == 'malformed_result':
        input_env = request['params']['input']
        raw = json.dumps({'format': 'genius-fp1-result/1.0',
                          'input_digest': input_env['sha256']}).encode()
        result_env = {'encoding': 'base64', 'data': base64.b64encode(raw).decode(),
                      'sha256': hashlib.sha256(raw).hexdigest()}
        emit({'jsonrpc': '2.0', 'id': request['id'],
              'result': {'input': input_env, 'result': result_env}})
    elif args.mode == 'foreign_id':
        emit({'jsonrpc': '2.0', 'id': 'FOREIGN_ID', 'result': {}})
    elif args.mode == 'inspect':
        fds = []
        exhausted = False
        try:
            for _ in range(64):
                fds.append(os.open('/dev/null', os.O_RDONLY))
        except OSError as exc:
            exhausted = exc.errno == errno.EMFILE
        finally:
            for fd in fds:
                os.close(fd)
        file_limit = False
        with tempfile.TemporaryDirectory(prefix='genius-security-file-', dir='/tmp') as directory:
            dest = Path(directory) / 'controlled.bin'
            fd = os.open(dest, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            try:
                try:
                    os.write(fd, b'x')
                except OSError as exc:
                    file_limit = exc.errno == errno.EFBIG
            finally:
                os.close(fd)
            observed_file_size = dest.stat().st_size
        result = {
            'uid': os.geteuid(),
            'identity_snapshot': bootstrap['identity_snapshot'](),
            'isolated': sys.flags.isolated,
            'no_site': sys.flags.no_site,
            'dont_write_bytecode': sys.dont_write_bytecode,
            'sentinel_visible': 'GENIUS_SECURITY_SYNTHETIC_SECRET' in os.environ,
            'pythonpath_visible': 'PYTHONPATH' in os.environ,
            'limits': {name: list(resource.getrlimit(getattr(resource, name)))
                       for name in ['RLIMIT_CPU', 'RLIMIT_AS', 'RLIMIT_NOFILE',
                                    'RLIMIT_FSIZE', 'RLIMIT_CORE']},
            'nofile_observed': exhausted,
            'file_limit_observed': file_limit,
            'file_size': observed_file_size,
        }
        emit({'jsonrpc': '2.0', 'id': request['id'], 'result': result})
    else:
        raise ValueError('Unknown trusted test mode')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
