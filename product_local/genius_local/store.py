"""Local immutable case journal; one writer per case, no power-loss guarantee.

Only HEAD is replaced. Artifact and revision names are content digests and are
created without overwrite. Unreferenced, valid revisions are reported as
orphans after an interrupted commit; corrupt files are never silently skipped.
"""
from __future__ import annotations

from contextlib import contextmanager
import hashlib
import json
import os
import fcntl
from pathlib import Path
import re
import secrets

MAX_ARTIFACT_BYTES = 8 * 1024 * 1024
MAX_REVISION_BYTES = 8 * 1024 * 1024
DIGEST = re.compile(r"[0-9a-f]{64}\Z")


class StoreError(ValueError):
    pass


class CorruptStore(StoreError):
    pass


class ConflictError(StoreError):
    pass


class UnsafePath(StoreError):
    pass


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def _no_duplicate(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise CorruptStore("duplicate JSON key")
        result[key] = value
    return result


def parse_json(raw):
    try:
        return json.loads(raw, object_pairs_hook=_no_duplicate,
                          parse_constant=lambda value: (_ for _ in ()).throw(
                              CorruptStore("non-finite JSON number")))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CorruptStore("invalid JSON") from exc


def _digest(value):
    if not isinstance(value, str) or not DIGEST.fullmatch(value):
        raise UnsafePath("expected SHA-256 digest")
    return value


def _safe_directory(path):
    path = Path(path).absolute()
    if ".." in path.parts:
        raise UnsafePath("parent traversal is forbidden")
    for part in [*reversed(path.parents), path]:
        if part.is_symlink():
            raise UnsafePath("symlink directory is forbidden")
        if part.exists() and not part.is_dir():
            raise UnsafePath("expected directory")
    return path


class Store:
    def __init__(self, root):
        self.root = _safe_directory(root)
        self.root.mkdir(parents=True, exist_ok=True)
        for name in ("objects", "revisions", "tmp"):
            directory = _safe_directory(self.root / name)
            directory.mkdir(exist_ok=True)

    def _path(self, group, digest):
        _safe_directory(self.root / group)
        return self.root / group / _digest(digest)

    def _read(self, path, limit):
        _safe_directory(path.parent)
        if path.is_symlink():
            raise UnsafePath("symlink file is forbidden")
        try:
            descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0))
            with os.fdopen(descriptor, "rb") as stream:
                import stat
                if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                    raise UnsafePath("only regular files are permitted")
                raw = stream.read(limit + 1)
        except OSError as exc:
            raise CorruptStore("unreadable file: " + str(path.relative_to(self.root))) from exc
        if len(raw) > limit:
            raise CorruptStore("stored file exceeds size limit")
        return raw

    def _temporary(self, raw):
        _safe_directory(self.root / "tmp")
        path = self.root / "tmp" / ("pending-" + secrets.token_hex(16))
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        return path

    def _immutable(self, group, raw, limit):
        if not isinstance(raw, bytes):
            raise StoreError("artifact must be exact bytes")
        if len(raw) > limit:
            raise StoreError("artifact exceeds size limit")
        digest = hashlib.sha256(raw).hexdigest()
        destination = self._path(group, digest)
        if destination.exists() or destination.is_symlink():
            if self._read(destination, limit) != raw:
                raise CorruptStore("existing content-addressed file is corrupt")
        else:
            temporary = self._temporary(raw)
            try:
                try:
                    os.link(temporary, destination)
                except FileExistsError:
                    if self._read(destination, limit) != raw:
                        raise CorruptStore("content-addressed collision or corruption")
            finally:
                temporary.unlink(missing_ok=True)
        return {"sha256": digest, "path": group + "/" + digest, "size": len(raw)}

    def put_bytes(self, raw):
        return self._immutable("objects", raw, MAX_ARTIFACT_BYTES)

    def get_bytes(self, digest):
        raw = self._read(self._path("objects", digest), MAX_ARTIFACT_BYTES)
        if hashlib.sha256(raw).hexdigest() != digest:
            raise CorruptStore("artifact digest mismatch")
        return raw

    def head(self):
        path = self.root / "HEAD"
        if not path.exists() and not path.is_symlink():
            return None
        data = parse_json(self._read(path, 1024))
        if not isinstance(data, dict) or set(data) != {"format", "sha256"} or data["format"] != "genius-local-head/0.1.0":
            raise CorruptStore("invalid HEAD")
        return _digest(data["sha256"])

    @contextmanager
    def _commit_lock(self, name="COMMIT_LOCK"):
        if name not in ("COMMIT_LOCK", "WRITER_LOCK"):
            raise UnsafePath("invalid lock name")
        path = self.root / name
        _safe_directory(self.root)
        if path.is_symlink():
            raise UnsafePath("symlink writer lock is forbidden")
        descriptor = os.open(path, os.O_RDWR | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0), 0o600)
        # POSIX advisory locks are released by the OS on process death. Unlike
        # PID-file recovery this has no half-written lock or PID-reuse window.
        try:
            import stat
            if not stat.S_ISREG(os.fstat(descriptor).st_mode):
                raise UnsafePath("writer lock must be a regular file")
            try:
                fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as exc:
                raise ConflictError("another local commit is active") from exc
            try:
                yield
            finally:
                fcntl.flock(descriptor, fcntl.LOCK_UN)
        finally:
            os.close(descriptor)

    def writer(self):
        """Exclusive cooperative writer for a complete controller attempt."""
        return self._commit_lock("WRITER_LOCK")

    def _revisions(self):
        found = {}
        for path in (self.root / "revisions").iterdir():
            digest = _digest(path.name)
            raw = self._read(path, MAX_REVISION_BYTES)
            if hashlib.sha256(raw).hexdigest() != digest:
                raise CorruptStore("revision digest mismatch")
            data = parse_json(raw)
            if not isinstance(data, dict) or set(data) != {"format", "revision", "parent", "objects", "payload"}:
                raise CorruptStore("invalid revision fields")
            if data["format"] != "genius-local-revision/0.1.0" or type(data["revision"]) is not int or data["revision"] < 1 or not isinstance(data["payload"], dict):
                raise CorruptStore("invalid revision envelope")
            if data["parent"] is not None:
                _digest(data["parent"])
            if not isinstance(data["objects"], list) or data["objects"] != sorted(set(data["objects"])):
                raise CorruptStore("invalid revision object manifest")
            for object_digest in data["objects"]:
                self.get_bytes(_digest(object_digest))
            found[digest] = data
        for digest, data in found.items():
            parent = data["parent"]
            if parent is None:
                if data["revision"] != 1:
                    raise CorruptStore("invalid initial revision")
            elif parent not in found or found[parent]["revision"] + 1 != data["revision"]:
                raise CorruptStore("broken revision parent or number")
        return found

    def load_chain(self):
        revisions = self._revisions()
        for path in (self.root / "objects").iterdir():
            self.get_bytes(_digest(path.name))
        head = self.head()
        chain = []
        seen = set()
        while head is not None:
            if head in seen or head not in revisions:
                raise CorruptStore("broken HEAD chain")
            seen.add(head)
            item = revisions[head]
            chain.append({**item, "sha256": head})
            head = item["parent"]
        return list(reversed(chain))

    def inspect(self):
        chain = self.load_chain()
        committed = {item["sha256"] for item in chain}
        return {"head": chain[-1]["sha256"] if chain else None,
                "revisions": chain,
                "uncommitted_revisions": sorted(set(self._revisions()) - committed),
                "temporary_files": sorted(path.name for path in (self.root / "tmp").iterdir()),
                "model": "POSIX single-local-writer; process interruption; no power-loss guarantee"}

    def commit(self, payload, parent_digest):
        if not isinstance(payload, dict):
            raise StoreError("revision payload must be a JSON object")
        if parent_digest is not None:
            _digest(parent_digest)
        with self._commit_lock():
            chain = self.load_chain()
            current = chain[-1]["sha256"] if chain else None
            if current != parent_digest:
                raise ConflictError("parent is not current HEAD")
            envelope = {"format": "genius-local-revision/0.1.0",
                        "revision": len(chain) + 1, "parent": current,
                        "objects": sorted(path.name for path in (self.root / "objects").iterdir()),
                        "payload": payload}
            reference = self._immutable("revisions", canonical(envelope), MAX_REVISION_BYTES)
            temporary = self._temporary(canonical({"format": "genius-local-head/0.1.0", "sha256": reference["sha256"]}))
            try:
                target = self.root / "HEAD"
                if target.is_symlink():
                    raise UnsafePath("symlink HEAD is forbidden")
                os.replace(temporary, target)
            finally:
                temporary.unlink(missing_ok=True)
            return {**reference, "revision": envelope["revision"], "parent": current}
