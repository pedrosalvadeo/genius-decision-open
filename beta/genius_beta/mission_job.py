"""Isolated child. Every stage waits for its durable parent ACK before continuing."""
import base64
import contextlib
import json
import os
from pathlib import Path
import resource
import sys
import threading

from .engine_job import install_parent_death_guard
from .mission_state import digest, pack, unpack, MAX_BUNDLE

PROTOCOL = sys.stdout

def emit(value):
    PROTOCOL.write(json.dumps(value, separators=(',', ':'), allow_nan=False) + '\n')
    PROTOCOL.flush()

def main():
    install_parent_death_guard()
    resource.setrlimit(resource.RLIMIT_CPU, (45, 45))
    resource.setrlimit(resource.RLIMIT_AS, (384*1024*1024, 384*1024*1024))
    resource.setrlimit(resource.RLIMIT_FSIZE, (32*1024*1024, 32*1024*1024))
    resource.setrlimit(resource.RLIMIT_NOFILE, (128, 128))
    os.umask(0o077)
    threading.stack_size(1024*1024)
    from genius_adaptive.distribution import Distribution, prepare_files
    from genius_adaptive.runtime import run
    from genius_adaptive.journal import Conflict, OutcomeUnknown
    payload = json.loads(sys.stdin.buffer.readline(2*MAX_BUNDLE))
    directory = Path(sys.argv[1]) / 'mission'
    try:
        if payload.get('state'):
            raw = base64.b64decode(payload['state'], validate=True)
            unpack(raw, payload['state_sha256'], directory)
        else:
            prepare_files(payload['files'], directory, payload['id'])
        def checkpoint(stage):
            raw = pack(directory)
            emit(dict(type='checkpoint', stage=stage, state=base64.b64encode(raw).decode(), sha256=digest(raw)))
            if sys.stdin.buffer.readline(8) != b'ACK\n':
                raise RuntimeError('DURABLE_ACK_REQUIRED')
        # Adapter output is evidence data; stdout is exclusively our protocol.
        with contextlib.redirect_stdout(sys.stderr):
            result = run(directory, Distribution(), after_stage=checkpoint)
        delivery = list((directory / 'delivery').iterdir())
        if len(delivery) != 1:
            raise ValueError('DELIVERY_COUNT')
        raw = delivery[0].read_bytes()
        emit(dict(type='completed', result=result, artifact=base64.b64encode(raw).decode(),
                  artifact_name=delivery[0].name, artifact_sha256=digest(raw)))
    except (Conflict, OutcomeUnknown):
        emit(dict(type='needs_review', error='STATE_OR_RUNTIME_REQUIRES_REVIEW'))
    except Exception:
        emit(dict(type='failed', error='MISSION_EXECUTION_FAILED'))

if __name__ == '__main__':
    main()
