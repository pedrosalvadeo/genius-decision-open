"""Durable receipts and effect intents, independent of graph task caching.

The caller holds a process lock for the whole mission. A recorded intent is
not evidence of success. An interrupted effect must be reconciled from its
destination; it is never retried merely because its receipt is missing.
"""
from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import tempfile
import time


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


class Conflict(ValueError):
    pass


class OutcomeUnknown(RuntimeError):
    pass


@contextmanager
def exclusive(directory):
    """Single writer, including checkpointing, with automatic crash release."""
    with (Path(directory) / "mission.lock").open("a+b") as handle:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise Conflict("MISSION_BUSY") from exc
        try:
            yield
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)


def publish(path, raw):
    """Immutable atomic local effect. Existing different bytes are a conflict."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".pending-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.link(temporary, path)
        except FileExistsError:
            if path.is_symlink() or not path.is_file() or path.read_bytes() != raw:
                raise Conflict("ARTIFACT_CONFLICT")
        directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        os.unlink(temporary)


class Journal:
    def __init__(self, path):
        self.path = str(path)
        with self.connection() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS identity (id INTEGER PRIMARY KEY CHECK(id=1), body TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS receipts (stage TEXT PRIMARY KEY, body TEXT NOT NULL, observed_at INTEGER NOT NULL);
                CREATE TABLE IF NOT EXISTS effects (
                    key TEXT PRIMARY KEY, request TEXT NOT NULL,
                    state TEXT NOT NULL CHECK(state IN ('pending','confirmed')),
                    receipt TEXT, created_at INTEGER NOT NULL);
            """)

    @contextmanager
    def connection(self):
        db = sqlite3.connect(self.path, timeout=10)
        try:
            db.execute("PRAGMA journal_mode=WAL")
            db.execute("PRAGMA synchronous=FULL")
            with db:
                yield db
        finally:
            db.close()

    def bind(self, identity):
        body = canonical(identity)
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            prior = db.execute("SELECT body FROM identity WHERE id=1").fetchone()
            if prior and prior[0] != body:
                raise Conflict("MISSION_OR_RUNTIME_CHANGED")
            db.execute("INSERT OR IGNORE INTO identity VALUES (1,?)", (body,))

    def get(self, stage):
        with self.connection() as db:
            row = db.execute("SELECT body FROM receipts WHERE stage=?", (stage,)).fetchone()
        return json.loads(row[0]) if row else None

    def record(self, stage, value):
        body = canonical(value)
        if len(body.encode()) > 8 * 1024 * 1024:
            raise ValueError("RECEIPT_TOO_LARGE")
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT body FROM receipts WHERE stage=?", (stage,)).fetchone()
            if row and row[0] != body:
                raise Conflict("RECEIPT_CONFLICT:" + stage)
            db.execute("INSERT OR IGNORE INTO receipts VALUES (?,?,?)", (stage, body, time.time_ns()))
        return value

    def once(self, stage, operation):
        prior = self.get(stage)
        return prior if prior is not None else self.record(stage, operation())

    def effect(self, key, request, apply, reconcile):
        body = canonical(request)
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT request,state,receipt FROM effects WHERE key=?", (key,)).fetchone()
            if row and row[0] != body:
                raise Conflict("EFFECT_KEY_REUSED_WITH_DIFFERENT_REQUEST")
            if row and row[1] == "confirmed":
                return json.loads(row[2])
            if row is None:
                db.execute("INSERT INTO effects VALUES (?,?,'pending',NULL,?)", (key, body, time.time_ns()))
        # The intent above is committed BEFORE interacting with the destination.
        # Any exception or hard process exit leaves a pending, uncertain effect.
        receipt = apply() if row is None else reconcile()
        if receipt is None:
            raise OutcomeUnknown("EFFECT_OUTCOME_UNKNOWN:" + key)
        encoded = canonical(receipt)
        with self.connection() as db:
            db.execute("UPDATE effects SET state='confirmed',receipt=? WHERE key=?", (encoded, key))
        return receipt

    def export(self):
        with self.connection() as db:
            receipts = {r[0]: {"value": json.loads(r[1]), "observed_at_ns": r[2]}
                        for r in db.execute("SELECT stage,body,observed_at FROM receipts ORDER BY observed_at")}
            effects = [{"key": r[0], "request": json.loads(r[1]), "state": r[2],
                        "receipt": json.loads(r[3]) if r[3] else None}
                       for r in db.execute("SELECT key,request,state,receipt FROM effects ORDER BY key")]
        return {"receipts": receipts, "effects": effects}
