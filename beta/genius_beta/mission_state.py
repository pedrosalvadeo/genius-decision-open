"""Bounded service-owned state bundles. Never accept bundles from API clients."""
import contextlib
import hashlib
import io
from pathlib import Path, PurePosixPath
import sqlite3
import tempfile
import zipfile

MAX_BUNDLE = 4 * 1024 * 1024
MAX_EXPANDED = 24 * 1024 * 1024
MAX_ENTRIES = 128

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def allowed(name):
    path = PurePosixPath(name)
    return (path.as_posix() == name and not path.is_absolute() and
            not any(p in ('.', '..') or p.startswith('.') for p in path.parts) and
            '\\' not in name and '\x00' not in name and
            (name in ('mission.json', 'journal.sqlite3', 'checkpoints.sqlite3') or
             path.parts[0] in ('input', 'candidates', 'delivery', 'evidence')))

def pack(directory):
    directory = Path(directory)
    output, total, count = io.BytesIO(), 0, 0
    with tempfile.TemporaryDirectory() as tmp, zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(directory.rglob('*')):
            if path.is_symlink():
                raise ValueError('STATE_SYMLINK')
            name = path.relative_to(directory).as_posix()
            if not path.is_file() or not allowed(name):
                continue
            source = path
            if name.endswith('.sqlite3'):
                source = Path(tmp) / path.name
                with contextlib.closing(sqlite3.connect(path)) as src, contextlib.closing(sqlite3.connect(source)) as dst:
                    src.backup(dst)
            total += source.stat().st_size
            count += 1
            if total > MAX_EXPANDED or count > MAX_ENTRIES:
                raise ValueError('STATE_BUDGET')
            archive.write(source, name)
    raw = output.getvalue()
    if len(raw) > MAX_BUNDLE:
        raise ValueError('STATE_BUDGET')
    return raw

def unpack(raw, expected, directory):
    if len(raw) > MAX_BUNDLE or digest(raw) != expected:
        raise ValueError('STATE_DIGEST')
    directory = Path(directory)
    directory.mkdir(mode=0o700, exist_ok=False)
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        entries = archive.infolist()
        if len(entries) > MAX_ENTRIES or sum(e.file_size for e in entries) > MAX_EXPANDED:
            raise ValueError('STATE_BUDGET')
        seen = set()
        for entry in entries:
            name = entry.filename
            if not allowed(name) or entry.is_dir() or name in seen or entry.external_attr >> 28 == 0o12:
                raise ValueError('STATE_PATH')
            seen.add(name)
            path = directory / name
            path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            with archive.open(entry) as source:
                body = source.read(entry.file_size + 1)
            if len(body) != entry.file_size:
                raise ValueError('STATE_SIZE')
            path.write_bytes(body)
