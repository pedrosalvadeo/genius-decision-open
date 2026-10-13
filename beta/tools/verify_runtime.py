"""Verify received immutable dependencies without recertifying historical tests."""
import hashlib
import json
from pathlib import Path


def verify(root=None):
    root = Path(root) if root else Path(__file__).resolve().parents[2]
    manifest = json.loads((root / 'beta/vendor/MANIFEST.json').read_text())
    errors = []
    for row in manifest['files']:
        path = root / row['path']
        if path.is_symlink() or not path.is_file():
            errors.append({'path': row['path'], 'reason': 'missing_or_symlink'})
            continue
        raw = path.read_bytes()
        if len(raw) != row['size'] or hashlib.sha256(raw).hexdigest() != row['sha256']:
            errors.append({'path': row['path'], 'reason': 'identity_mismatch'})
    upstream = json.loads((root / 'beta/vendor/UPSTREAM_MANIFEST.json').read_text())
    for row in upstream['files']:
        path = root / row['path']
        if path.is_symlink() or not path.is_file():
            errors.append({'path': row['path'], 'reason': 'upstream_missing_or_symlink'})
            continue
        raw = path.read_bytes()
        if len(raw) != row['size'] or hashlib.sha256(raw).hexdigest() != row['sha256']:
            errors.append({'path': row['path'], 'reason': 'upstream_identity_mismatch'})
    expected = {row['path'] for row in manifest['files']}
    actual = {str(p.relative_to(root)) for p in (root/'beta/vendor').rglob('*.py')}
    if actual != expected:
        errors.append({'reason': 'runtime_module_set_mismatch', 'extra': sorted(actual-expected), 'missing': sorted(expected-actual)})
    result = {'format': 'genius-beta-runtime-check/1', 'checked': len(expected), 'upstream_checked': len(upstream['files']), 'errors': errors}
    return result


if __name__ == '__main__':
    result = verify()
    print(json.dumps(result, indent=2))
    raise SystemExit(bool(result['errors']))
