"""Reproduce a synthetic observation report; never connects to a live service."""
import argparse
import contextlib
import importlib.util
from pathlib import Path
import sqlite3
import tempfile
from unittest.mock import patch

from genius_beta import regulation as reg
from genius_beta.db import initialize, transaction

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location('regulation_observation', ROOT/'beta/tools/regulation_observation.py')
observation = importlib.util.module_from_spec(spec)
spec.loader.exec_module(observation)


def example():
    config = dict(ADAPTIVE_ENABLED=True, MISSION_REGULATION_ENABLED=True,
                  MAX_DATABASE_BYTES=100*1024**2, MIN_FREE_BYTES=10*1024**2)
    now = 1_000_000_000
    with tempfile.TemporaryDirectory() as directory:
        path = initialize(Path(directory)/'synthetic.sqlite3')
        with contextlib.closing(sqlite3.connect(path, isolation_level=None)) as db:
            db.row_factory = sqlite3.Row
            with patch.object(reg, 'observe', return_value=dict(storage_bytes=1000,
                    free_bytes=1024**3, pending=0)), patch.object(reg.time, 'time', side_effect=lambda: now):
                for outcome, reason, elapsed in (('completed', None, 2),
                        ('failed', 'MISSION_TIMEOUT', 9), ('cancelled', 'CANCELLED', 1)):
                    with transaction(db):
                        state = reg.refresh(db, config, force=True, now=now)
                        token = reg.begin(db, config, state)
                        now += elapsed
                        reg.finish(db, config, token, outcome, reason)
                with transaction(db):
                    reg.begin(db, config, reg.refresh(db, config, force=True, now=now))
                now += 7
                reg.recover(db, config)
                # These are independent current rows, not IDs paired with events.
                for status in ('queued', 'running', 'completed'):
                    db.execute('INSERT INTO adaptive_missions '
                        '(id,user_id,idempotency_key,request_sha256,input_json,status,created_at,updated_at) '
                        'VALUES(?,?,?,?,?,?,?,?)', ('synthetic-'+status, 'synthetic-user', status,
                            'synthetic-hash', '{}', status, now, now))
                return observation.report(path, since=999_999_999, until=now+1,
                                          now=now+1, source='synthetic')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    observation.write_private(args.output, example())
