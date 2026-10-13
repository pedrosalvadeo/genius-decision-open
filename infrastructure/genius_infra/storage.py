"""Local, single-owner evidence store. Hashes detect bytes, not truth or authorship.

Linux/POSIX only. Call all operations inside ``Store.exclusive()``; the lock is
nonblocking and is deliberately held across execution by the integrating CLI.
Committed runs are append-only through this API. A pending transaction is never
recovered as a completed result automatically.
"""
from __future__ import annotations

import contextlib
import errno
import fcntl
import hashlib
import json
import os
import re
import stat
import uuid
from pathlib import Path

FORMAT = "genius-local-store/1.0"
BACKUP_FORMAT = "genius-local-backup/1.0"
RUN_FORMAT = "genius-local-run/1.0"
DEFAULTS = dict(max_store_bytes=536870912, max_file_bytes=50331648,
                max_run_bytes=100663296, max_runs=128)
SAFE_NAME = re.compile(r"[a-z][a-z0-9_.-]{0,63}\Z")
RUN_NAME = re.compile(r"run-[0-9a-f]{32}\Z")
RESERVED = {"start.json", "outcome.json", "MANIFEST.json"}
ROOT_NAMES = {"store.json", ".lock", "runs", "staging"}
MAX_FILES = 35  # 32 opaque artifacts plus start/outcome/manifest.
META_CAP = 1024 * 1024
DIR_FLAGS = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
READ_FLAGS = os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK


class StoreError(Exception):
    """Operational rejection; never a Kernel or mathematical result."""


class BusyError(StoreError):
    pass


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=True, sort_keys=True,
                       separators=(",", ":"), allow_nan=False) + "\n").encode()


def _unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise StoreError("DUPLICATE_METADATA_KEY")
        result[key] = value
    return result


def _json(raw):
    try:
        return json.loads(raw.decode("utf-8"), object_pairs_hook=_unique,
                          parse_constant=lambda _: (_ for _ in ()).throw(StoreError("NONFINITE_METADATA")))
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise StoreError("INVALID_METADATA") from exc


def _directory(path):
    """Pin every path component; never follow a symbolic link."""
    path = os.fspath(path)
    if not isinstance(path, str) or "\0" in path or ".." in path.split("/"):
        raise StoreError("UNSAFE_PATH")
    absolute = os.path.abspath(path)
    fd = os.open("/", DIR_FLAGS)
    try:
        for part in absolute.split("/")[1:]:
            if part:
                next_fd = os.open(part, DIR_FLAGS, dir_fd=fd)
                os.close(fd)
                fd = next_fd
        return fd
    except BaseException:
        os.close(fd)
        raise


def _private(fd, *, directory=False):
    info = os.fstat(fd)
    expected = stat.S_ISDIR if directory else stat.S_ISREG
    if not expected(info.st_mode) or info.st_uid != os.geteuid():
        raise StoreError("UNSAFE_OWNER_OR_TYPE")
    if stat.S_IMODE(info.st_mode) != (0o700 if directory else 0o600):
        raise StoreError("UNSAFE_PERMISSIONS")
    if not directory and info.st_nlink != 1:
        raise StoreError("HARDLINK_REJECTED")
    return info


def _new_directory(path):
    path = os.fspath(path)
    if ".." in path.split("/") or "\0" in path:
        raise StoreError("UNSAFE_PATH")
    absolute = os.path.abspath(path)
    parent, name = os.path.split(absolute)
    if not name:
        raise StoreError("UNSAFE_PATH")
    parent_fd = _directory(parent)
    try:
        os.mkdir(name, mode=0o700, dir_fd=parent_fd)
        fd = os.open(name, DIR_FLAGS, dir_fd=parent_fd)
        os.fchmod(fd, 0o700)
        os.fsync(parent_fd)
        return fd
    finally:
        os.close(parent_fd)


def _outside_source(source, destination):
    """Never let a backup/restore mutate its own source inventory."""
    raw = os.fspath(destination)
    if ".." in raw.split("/") or "\0" in raw:
        raise StoreError("UNSAFE_PATH")
    if os.path.commonpath([os.path.abspath(os.fspath(source)), os.path.abspath(raw)]) == os.path.abspath(os.fspath(source)):
        raise StoreError("DESTINATION_INSIDE_SOURCE")


def _subdirectory(parent, name):
    fd = os.open(name, DIR_FLAGS, dir_fd=parent)
    try:
        _private(fd, directory=True)
        return fd
    except BaseException:
        os.close(fd)
        raise


def _read(parent, name, cap):
    fd = os.open(name, READ_FLAGS, dir_fd=parent)
    try:
        info = _private(fd)
        if info.st_size > cap:
            raise StoreError("FILE_LIMIT")
        chunks, total = [], 0
        while True:
            chunk = os.read(fd, min(1024 * 1024, cap + 1 - total))
            if not chunk:
                break
            total += len(chunk)
            if total > cap:
                raise StoreError("FILE_LIMIT")
            chunks.append(chunk)
        after = os.fstat(fd)
        if after.st_size != info.st_size or after.st_mtime_ns != info.st_mtime_ns:
            raise StoreError("CHANGED_DURING_READ")
        return b"".join(chunks)
    finally:
        os.close(fd)


def _write(parent, name, raw):
    if type(raw) is not bytes:
        raise StoreError("ARTIFACT_REQUIRES_BYTES")
    fd = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL |
                 os.O_NOFOLLOW | os.O_CLOEXEC, 0o600, dir_fd=parent)
    try:
        os.fchmod(fd, 0o600)
        remaining = memoryview(raw)
        while remaining:
            count = os.write(fd, remaining)
            if count <= 0:
                raise OSError(errno.EIO, "short write")
            remaining = remaining[count:]
        os.fsync(fd)
    finally:
        os.close(fd)
    os.fsync(parent)


def _record(raw):
    return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def _config(raw):
    obj = _json(raw)
    if not isinstance(obj, dict) or set(obj) != {"format", "limits"} or obj["format"] != FORMAT:
        raise StoreError("INCOMPATIBLE_STORE")
    limits = obj["limits"]
    if not isinstance(limits, dict) or set(limits) != set(DEFAULTS):
        raise StoreError("INVALID_LIMITS")
    for key, maximum in DEFAULTS.items():
        if type(limits[key]) is not int or not 0 < limits[key] <= maximum:
            raise StoreError("INVALID_LIMITS")
    if limits["max_file_bytes"] > limits["max_run_bytes"] or limits["max_run_bytes"] > limits["max_store_bytes"]:
        raise StoreError("INVALID_LIMITS")
    return obj


def _names(fd):
    return sorted(os.listdir(fd))


def _run_files(fd, limits):
    names = _names(fd)
    if len(names) > MAX_FILES:
        raise StoreError("FILE_COUNT_LIMIT")
    records = {}
    for name in names:
        if name not in RESERVED and not SAFE_NAME.fullmatch(name):
            raise StoreError("UNSAFE_ARTIFACT_NAME")
        raw = _read(fd, name, limits["max_file_bytes"])
        records[name] = _record(raw)
    if sum(v["bytes"] for v in records.values()) > limits["max_run_bytes"]:
        raise StoreError("RUN_LIMIT")
    return records


def _verify_run(fd, run_id, limits):
    records = _run_files(fd, limits)
    if not RESERVED.issubset(records):
        raise StoreError("INCOMPLETE_COMMITTED_RUN")
    manifest = _json(_read(fd, "MANIFEST.json", META_CAP))
    if not isinstance(manifest, dict) or set(manifest) != {"format", "run_id", "files"}:
        raise StoreError("INVALID_RUN_MANIFEST")
    actual = {k: v for k, v in records.items() if k != "MANIFEST.json"}
    if manifest["format"] != RUN_FORMAT or manifest["run_id"] != run_id or manifest["files"] != actual:
        raise StoreError("RUN_INTEGRITY_MISMATCH")
    for name in ("start.json", "outcome.json"):
        obj = _json(_read(fd, name, META_CAP))
        if not isinstance(obj, dict) or obj.get("run_id") != run_id:
            raise StoreError("INVALID_RUN_METADATA")
    return records


class Store:
    def __init__(self, path):
        self.path = Path(os.path.abspath(os.fspath(path)))
        self.fd = _directory(path)
        self._locked = False
        self._transactions = []
        try:
            _private(self.fd, directory=True)
            if set(_names(self.fd)) != ROOT_NAMES:
                raise StoreError("STORE_INVENTORY_MISMATCH")
            self.config = _config(_read(self.fd, "store.json", META_CAP))
            self.limits = self.config["limits"]
            for name in ("runs", "staging"):
                os.close(_subdirectory(self.fd, name))
            _read(self.fd, ".lock", 0)
        except BaseException:
            os.close(self.fd)
            self.fd = -1
            raise

    @classmethod
    def create(cls, path, **limits):
        if set(limits) - set(DEFAULTS):
            raise StoreError("UNKNOWN_LIMIT")
        config = {"format": FORMAT, "limits": DEFAULTS | limits}
        _config(json_bytes(config))
        fd = _new_directory(path)
        try:
            for name in ("runs", "staging"):
                os.mkdir(name, 0o700, dir_fd=fd)
                child = os.open(name, DIR_FLAGS, dir_fd=fd)
                os.fchmod(child, 0o700)
                os.close(child)
            _write(fd, ".lock", b"")
            _write(fd, "store.json", json_bytes(config))
            os.fsync(fd)
        finally:
            os.close(fd)
        return cls(path)

    def close(self):
        if self._locked:
            raise StoreError("CLOSE_WHILE_LOCKED")
        if self.fd >= 0:
            os.close(self.fd)
            self.fd = -1

    def _require_lock(self):
        if not self._locked:
            raise StoreError("EXCLUSIVE_REQUIRED")

    @contextlib.contextmanager
    def exclusive(self):
        if self._locked or self.fd < 0:
            raise StoreError("NESTED_OR_CLOSED_STORE")
        lock = os.open(".lock", os.O_RDWR | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK,
                       dir_fd=self.fd)
        try:
            _private(lock)
            if os.fstat(lock).st_size != 0:
                raise StoreError("INVALID_LOCK")
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError as exc:
                if exc.errno in (errno.EAGAIN, errno.EACCES):
                    raise BusyError("STORE_BUSY") from exc
                raise
            self._locked = True
            yield self
        finally:
            for transaction in self._transactions:
                transaction._close()
            self._transactions = []
            self._locked = False
            os.close(lock)

    def verify(self):
        self._require_lock()
        _private(self.fd, directory=True)
        if set(_names(self.fd)) != ROOT_NAMES or _config(_read(self.fd, "store.json", META_CAP)) != self.config:
            raise StoreError("STORE_CHANGED")
        result = {"status": "PASS", "format": FORMAT, "runs": [], "incomplete": [], "bytes": 0}
        result["bytes"] += len(_read(self.fd, "store.json", META_CAP))
        count = 0
        for group in ("runs", "staging"):
            parent = _subdirectory(self.fd, group)
            try:
                names = _names(parent)
                count += len(names)
                if count > self.limits["max_runs"]:
                    raise StoreError("RUN_COUNT_LIMIT")
                for run_id in names:
                    if not RUN_NAME.fullmatch(run_id):
                        raise StoreError("UNSAFE_RUN_NAME")
                    child = _subdirectory(parent, run_id)
                    try:
                        records = (_verify_run(child, run_id, self.limits) if group == "runs"
                                   else _run_files(child, self.limits))
                    finally:
                        os.close(child)
                    total = sum(v["bytes"] for v in records.values())
                    result["bytes"] += total
                    result["runs" if group == "runs" else "incomplete"].append(
                        {"run_id": run_id, "bytes": total, "files": records,
                         "state": "COMMITTED" if group == "runs" else "INCOMPLETE"})
            finally:
                os.close(parent)
        if result["bytes"] > self.limits["max_store_bytes"]:
            raise StoreError("STORE_LIMIT")
        return result

    def begin(self, artifacts, metadata):
        self._require_lock()
        status = self.verify()
        if len(status["runs"]) + len(status["incomplete"]) >= self.limits["max_runs"]:
            raise StoreError("RUN_COUNT_LIMIT")
        run_id = "run-" + uuid.uuid4().hex
        staging = _subdirectory(self.fd, "staging")
        try:
            os.mkdir(run_id, 0o700, dir_fd=staging)
            child = _subdirectory(staging, run_id)
            os.fsync(staging)
        finally:
            os.close(staging)
        transaction = Transaction(self, run_id, child)
        self._transactions.append(transaction)
        transaction._add({"start.json": json_bytes({"run_id": run_id, "metadata": metadata})}, internal=True)
        transaction.add(artifacts)
        return transaction

    def publish(self, artifacts, metadata):
        return self.begin(artifacts, metadata).commit(metadata)

    def backup(self, destination):
        self._require_lock()
        _outside_source(self.path, destination)
        self.verify()
        dest = _new_directory(destination)
        try:
            files = {}
            directories = ["runs", "staging"]
            config_raw = _read(self.fd, "store.json", META_CAP)
            _write(dest, "store.json", config_raw)
            files["store.json"] = _record(config_raw)
            for group in ("runs", "staging"):
                source_group = _subdirectory(self.fd, group)
                os.mkdir(group, 0o700, dir_fd=dest)
                target_group = _subdirectory(dest, group)
                try:
                    for run_id in _names(source_group):
                        directories.append(f"{group}/{run_id}")
                        source_run = _subdirectory(source_group, run_id)
                        os.mkdir(run_id, 0o700, dir_fd=target_group)
                        target_run = _subdirectory(target_group, run_id)
                        try:
                            for name in _names(source_run):
                                raw = _read(source_run, name, self.limits["max_file_bytes"])
                                _write(target_run, name, raw)
                                files[f"{group}/{run_id}/{name}"] = _record(raw)
                        finally:
                            os.close(source_run)
                            os.close(target_run)
                    os.fsync(target_group)
                finally:
                    os.close(source_group)
                    os.close(target_group)
            manifest = {"format": BACKUP_FORMAT, "files": files,
                        "directories": sorted(directories)}
            raw = json_bytes(manifest)
            if len(raw) > META_CAP:
                raise StoreError("BACKUP_METADATA_LIMIT")
            _write(dest, "BACKUP.json", raw)  # Completion marker written last.
            os.fsync(dest)
            return {"status": "PASS", "format": BACKUP_FORMAT, "sha256": hashlib.sha256(raw).hexdigest(),
                    "files": len(files), "bytes": sum(v["bytes"] for v in files.values())}
        finally:
            os.close(dest)

    @classmethod
    def restore(cls, source, destination):
        """Data rollback is restoration to a fresh root; never replaces history."""
        _outside_source(source, destination)
        backup = _directory(source)
        try:
            _private(backup, directory=True)
            if set(_names(backup)) != {"store.json", "runs", "staging", "BACKUP.json"}:
                raise StoreError("INCOMPLETE_BACKUP")
            manifest = _json(_read(backup, "BACKUP.json", META_CAP))
            if not isinstance(manifest, dict) or set(manifest) != {"format", "files", "directories"} or manifest["format"] != BACKUP_FORMAT:
                raise StoreError("INVALID_BACKUP")
            config_raw = _read(backup, "store.json", META_CAP)
            limits = _config(config_raw)["limits"]
            actual, count = {"store.json": _record(config_raw)}, 0
            directories = ["runs", "staging"]
            # Validate actual paths first; manifest names are never used as paths.
            for group in ("runs", "staging"):
                parent = _subdirectory(backup, group)
                try:
                    for run_id in _names(parent):
                        directories.append(f"{group}/{run_id}")
                        count += 1
                        if count > limits["max_runs"] or not RUN_NAME.fullmatch(run_id):
                            raise StoreError("INVALID_BACKUP_RUN")
                        child = _subdirectory(parent, run_id)
                        try:
                            records = (_verify_run(child, run_id, limits) if group == "runs"
                                       else _run_files(child, limits))
                            for name, record in records.items():
                                actual[f"{group}/{run_id}/{name}"] = record
                        finally:
                            os.close(child)
                finally:
                    os.close(parent)
            if (sum(v["bytes"] for v in actual.values()) > limits["max_store_bytes"] or
                manifest["files"] != actual or manifest["directories"] != sorted(directories)):
                raise StoreError("BACKUP_INTEGRITY_MISMATCH")
            dest = _new_directory(destination)
            try:
                for group in ("runs", "staging"):
                    os.mkdir(group, 0o700, dir_fd=dest)
                    source_group, target_group = _subdirectory(backup, group), _subdirectory(dest, group)
                    try:
                        for run_id in _names(source_group):
                            os.mkdir(run_id, 0o700, dir_fd=target_group)
                            source_run = _subdirectory(source_group, run_id)
                            target_run = _subdirectory(target_group, run_id)
                            try:
                                for name in _names(source_run):
                                    raw = _read(source_run, name, limits["max_file_bytes"])
                                    if _record(raw) != actual[f"{group}/{run_id}/{name}"]:
                                        raise StoreError("BACKUP_CHANGED_DURING_RESTORE")
                                    _write(target_run, name, raw)
                            finally:
                                os.close(source_run)
                                os.close(target_run)
                        os.fsync(target_group)
                    finally:
                        os.close(source_group)
                        os.close(target_group)
                _write(dest, ".lock", b"")
                _write(dest, "store.json", config_raw)  # Completion marker last.
                os.fsync(dest)
            finally:
                os.close(dest)
        finally:
            os.close(backup)
        restored = cls(destination)
        with restored.exclusive():
            restored.verify()
        return restored


class Transaction:
    def __init__(self, store, run_id, fd):
        self.store, self.run_id, self.fd = store, run_id, fd
        self.committed = False
        self.poisoned = False

    def _close(self):
        if self.fd >= 0:
            os.close(self.fd)
            self.fd = -1

    def _add(self, artifacts, *, internal=False):
        self.store._require_lock()
        if self.fd < 0 or self.committed or self.poisoned or type(artifacts) is not dict:
            raise StoreError("INACTIVE_TRANSACTION")
        for name, raw in artifacts.items():
            if (not isinstance(name, str) or
                (name not in RESERVED and not SAFE_NAME.fullmatch(name)) or
                (name in RESERVED and not internal)):
                raise StoreError("UNSAFE_OR_RESERVED_ARTIFACT_NAME")
            if type(raw) is not bytes or len(raw) > self.store.limits["max_file_bytes"]:
                raise StoreError("ARTIFACT_TYPE_OR_LIMIT")
            if name in RESERVED and len(raw) > META_CAP:
                raise StoreError("METADATA_LIMIT")
            if name in _names(self.fd):
                raise StoreError("NO_OVERWRITE")
        current = _run_files(self.fd, self.store.limits)
        if len(current) + len(artifacts) > MAX_FILES:
            raise StoreError("FILE_COUNT_LIMIT")
        if len(set(current) - RESERVED) + len(set(artifacts) - RESERVED) > MAX_FILES - len(RESERVED):
            raise StoreError("ARTIFACT_COUNT_LIMIT")
        added = sum(map(len, artifacts.values()))
        if sum(v["bytes"] for v in current.values()) + added > self.store.limits["max_run_bytes"]:
            raise StoreError("RUN_LIMIT")
        if self.store.verify()["bytes"] + added > self.store.limits["max_store_bytes"]:
            raise StoreError("STORE_LIMIT")
        try:
            for name, raw in artifacts.items():
                _write(self.fd, name, raw)
        except BaseException:
            # A failed write may have created a prefix. It must never become a
            # manifest-certified artifact, even if the caller catches the I/O
            # exception and later tries to commit this transaction.
            self.poisoned = True
            raise

    def add(self, artifacts):
        self._add(artifacts)

    def commit(self, metadata):
        self._add({"outcome.json": json_bytes({"run_id": self.run_id, "metadata": metadata})}, internal=True)
        files = _run_files(self.fd, self.store.limits)
        raw = json_bytes({"format": RUN_FORMAT, "run_id": self.run_id, "files": files})
        self._add({"MANIFEST.json": raw}, internal=True)
        _verify_run(self.fd, self.run_id, self.store.limits)
        staging, runs = _subdirectory(self.store.fd, "staging"), _subdirectory(self.store.fd, "runs")
        try:
            # Protected by the one-owner store lock. UUID destination cannot be
            # supplied by payloads; explicit check also rejects an empty target.
            if self.run_id in _names(runs):
                raise StoreError("NO_OVERWRITE")
            os.rename(self.run_id, self.run_id, src_dir_fd=staging, dst_dir_fd=runs)
            self.committed = True
            os.fsync(runs)
            os.fsync(staging)
        finally:
            os.close(staging)
            os.close(runs)
        self._close()
        return self.run_id
