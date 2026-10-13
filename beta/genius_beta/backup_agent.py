"""One supervised backup loop. An outage is visible and never prints secrets."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import signal
import time
from .r2_backup import BackupError, R2Store, backup_once, enabled, encryption_key, recover


def main():
    os.umask(0o077)
    parser = argparse.ArgumentParser()
    parser.add_argument('--once', action='store_true')
    parser.add_argument('--restore-object')
    parser.add_argument('--output', type=Path)
    parser.add_argument('--services-stopped', action='store_true')
    args = parser.parse_args()
    if not enabled():
        raise BackupError('BACKUP_NOT_ENABLED')
    store, key = R2Store(), encryption_key()
    if args.restore_object:
        if args.output is None:
            parser.error('--output is required for recovery')
        print(json.dumps(recover(store, key, args.restore_object, args.output, args.services_stopped)))
        return
    data = Path(os.environ.get('GENIUS_DATA_DIR', '/data/genius'))
    with (data/'backup.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        stopping = False
        def stop(*_):
            nonlocal stopping
            stopping = True
        signal.signal(signal.SIGTERM, stop)
        signal.signal(signal.SIGINT, stop)
        while not stopping:
            try:
                result = backup_once(data/'genius.sqlite3', data/'backup-status.json', store, key)
                if result['status'] == 'ok':
                    print('backup_verified', flush=True)
            except BackupError as error:
                print('backup_unavailable code=' + str(error), flush=True)
                if args.once:
                    raise SystemExit(1) from None
            if args.once:
                return
            for _ in range(60):
                if stopping:
                    break
                time.sleep(1)


if __name__ == '__main__':
    try:
        main()
    except BackupError as error:
        raise SystemExit(str(error)) from None
