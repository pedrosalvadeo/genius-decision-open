import argparse
import json
import os
from pathlib import Path
import subprocess
from .pipeline import encoded, strict, prepare, verify_bundle, audit_current
from .model import require
from .github import API, Publisher, REPOSITORY


def main():
    parser = argparse.ArgumentParser(description='Generate, evaluate and publish a bounded code proposal.')
    parser.add_argument('command', choices=('prepare', 'verify', 'publish'))
    parser.add_argument('--root', type=Path, default=Path.cwd())
    parser.add_argument('--bundle', type=Path, required=True)
    parser.add_argument('--base')
    parser.add_argument('--result', type=Path)
    args = parser.parse_args()
    require(not args.bundle.is_symlink(), 'BUNDLE_SYMLINK')
    if args.command == 'prepare':
        audit_current(args.root)
        bundle = prepare(args.root, args.base)
        raw = encoded(bundle)
        if args.bundle.exists():
            require(args.bundle.read_bytes() == raw, 'BUNDLE_ALREADY_EXISTS_DIFFERENT')
        else:
            # Exclusive creation: retries may read, never replace another result.
            with args.bundle.open('xb') as handle:
                handle.write(raw); handle.flush(); os.fsync(handle.fileno())
        print(json.dumps({'status': 'PREPARED', 'proposal_id': bundle['proposal_id']}))
        return
    require(args.bundle.stat().st_size <= 256*1024, 'BUNDLE_SIZE')
    bundle = strict(args.bundle.read_bytes())
    if args.command == 'verify':
        verify_bundle(args.root, bundle)
        print(json.dumps({'status': 'VERIFIED', 'proposal_id': bundle['proposal_id']}))
        return
    require(os.environ.get('GITHUB_REPOSITORY') == REPOSITORY and
            os.environ.get('GITHUB_REF') == 'refs/heads/main' and
            os.environ.get('GITHUB_EVENT_NAME') in ('push', 'workflow_dispatch'), 'PUBLISH_WORKFLOW_SCOPE')
    require(os.environ.get('GITHUB_SHA') == bundle['base_revision'], 'PUBLISH_REVISION')
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=args.root, text=True).strip()
    require(head == bundle['base_revision'], 'CHECKOUT_REVISION')
    require(not subprocess.check_output(['git', 'diff', '--name-only', 'HEAD'], cwd=args.root), 'CHECKOUT_MODIFIED')
    result = Publisher(args.root, API()).publish(bundle)
    if args.result:
        require(not args.result.is_symlink(), 'RESULT_SYMLINK')
        args.result.write_bytes(encoded(result))
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        # Never print remote bodies, headers, environment, or tokens.
        message = str(exc)
        code = message if isinstance(exc, ValueError) and message.replace('_', '').isalnum() and message.isupper() else type(exc).__name__
        print(json.dumps({'status': 'STOPPED', 'error': code}))
        raise SystemExit(1) from None
