"""Local SQLite dossier store. Model versions and observations are append-only."""
from __future__ import annotations

from contextlib import closing, contextmanager
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sqlite3
import uuid


def now():
    return datetime.now(timezone.utc).isoformat()


def identifier():
    return uuid.uuid4().hex


def dumps(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def sha(value):
    return hashlib.sha256(dumps(value).encode("utf-8")).hexdigest()


class Store:
    def __init__(self, path):
        self.path = str(path)
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        with closing(self.connect()) as conn:
            conn.executescript("""
            PRAGMA journal_mode=WAL;
            CREATE TABLE IF NOT EXISTS cases (
                id TEXT PRIMARY KEY, title TEXT NOT NULL, narrative TEXT NOT NULL,
                current_version INTEGER NOT NULL DEFAULT 0, status TEXT NOT NULL,
                created_at TEXT NOT NULL, updated_at TEXT NOT NULL, obligations_json TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS versions (
                case_id TEXT NOT NULL REFERENCES cases(id), version INTEGER NOT NULL,
                parent_version INTEGER, model_json TEXT NOT NULL, model_sha256 TEXT NOT NULL,
                metadata_json TEXT NOT NULL, created_at TEXT NOT NULL,
                PRIMARY KEY(case_id,version));
            CREATE TABLE IF NOT EXISTS proposals (
                id TEXT PRIMARY KEY, case_id TEXT NOT NULL REFERENCES cases(id),
                base_version INTEGER NOT NULL, kind TEXT NOT NULL, text TEXT NOT NULL,
                model_json TEXT, metadata_json TEXT NOT NULL, status TEXT NOT NULL,
                accepted_version INTEGER, created_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS jobs (
                id TEXT PRIMARY KEY, case_id TEXT NOT NULL REFERENCES cases(id),
                version INTEGER NOT NULL, status TEXT NOT NULL, created_at TEXT NOT NULL,
                finished_at TEXT, result_json TEXT, error_json TEXT,
                FOREIGN KEY(case_id,version) REFERENCES versions(case_id,version));
            CREATE TABLE IF NOT EXISTS observations (
                id TEXT PRIMARY KEY, case_id TEXT NOT NULL REFERENCES cases(id),
                base_version INTEGER NOT NULL, recorded_version INTEGER NOT NULL,
                record_json TEXT NOT NULL, created_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS idempotency (
                case_id TEXT NOT NULL REFERENCES cases(id), key TEXT NOT NULL,
                request_sha256 TEXT NOT NULL, response_json TEXT NOT NULL,
                PRIMARY KEY(case_id,key));
            CREATE TABLE IF NOT EXISTS drafts (
                case_id TEXT PRIMARY KEY REFERENCES cases(id), revision INTEGER NOT NULL,
                base_version INTEGER NOT NULL, text TEXT NOT NULL, model_json TEXT,
                updated_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS erasure_markers (case_id TEXT PRIMARY KEY);
            CREATE TRIGGER IF NOT EXISTS immutable_version_update
                BEFORE UPDATE ON versions BEGIN SELECT RAISE(ABORT,'immutable version'); END;
            CREATE TRIGGER IF NOT EXISTS immutable_observation_update
                BEFORE UPDATE ON observations BEGIN SELECT RAISE(ABORT,'immutable observation'); END;
            CREATE UNIQUE INDEX IF NOT EXISTS one_running_version
                ON jobs(case_id,version) WHERE status='running';
            """)
            # Additive migration preserves all D1 snapshots and receipts.
            columns = {row[1] for row in conn.execute("PRAGMA table_info(cases)")}
            if "profile" not in columns:
                conn.execute("ALTER TABLE cases ADD COLUMN profile TEXT")
            columns = {row[1] for row in conn.execute("PRAGMA table_info(jobs)")}
            for name in ("execution_key", "execution_identity_json"):
                if name not in columns:
                    conn.execute(f"ALTER TABLE jobs ADD COLUMN {name} TEXT")
            conn.executescript("""
            DROP TRIGGER IF EXISTS immutable_version_delete;
            DROP TRIGGER IF EXISTS immutable_observation_delete;
            CREATE TRIGGER immutable_version_delete BEFORE DELETE ON versions
                WHEN NOT EXISTS(SELECT 1 FROM erasure_markers WHERE case_id=OLD.case_id)
                BEGIN SELECT RAISE(ABORT,'immutable version'); END;
            CREATE TRIGGER immutable_observation_delete BEFORE DELETE ON observations
                WHEN NOT EXISTS(SELECT 1 FROM erasure_markers WHERE case_id=OLD.case_id)
                BEGIN SELECT RAISE(ABORT,'immutable observation'); END;
            """)
            conn.commit()

    def connect(self):
        conn = sqlite3.connect(self.path, timeout=15)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("PRAGMA secure_delete=ON")
        return conn

    @contextmanager
    def transaction(self):
        conn = self.connect()
        try:
            conn.execute("BEGIN IMMEDIATE")
            yield conn
            conn.commit()
        except BaseException:
            conn.rollback()
            raise
        finally:
            conn.close()

    def read(self, sql, args=()):
        with closing(self.connect()) as conn:
            return conn.execute(sql, args).fetchall()

    def one(self, sql, args=()):
        rows = self.read(sql, args)
        return rows[0] if rows else None

    def erase_case(self, case_id, conn=None):
        """Erase an entire dossier, never a selected immutable snapshot.

        Callers own authorization/lifecycle locking. The scoped marker exists
        only inside the transaction and does not permit ordinary history edits.
        """
        if conn is None:
            with self.transaction() as transaction:
                return self.erase_case(case_id, transaction)
        conn.execute("INSERT INTO erasure_markers VALUES(?)", (case_id,))
        for table in ("idempotency", "observations", "jobs", "proposals", "drafts", "versions"):
            conn.execute(f"DELETE FROM {table} WHERE case_id=?", (case_id,))
        count = conn.execute("DELETE FROM cases WHERE id=?", (case_id,)).rowcount
        conn.execute("DELETE FROM erasure_markers WHERE case_id=?", (case_id,))
        return count

    @staticmethod
    def draft(row):
        if row is None:
            return None
        value = dict(row)
        raw = value.pop("model_json")
        value["model"] = json.loads(raw) if raw is not None else None
        value["state"] = "DRAFT_NOT_ADMITTED"
        return value

    @staticmethod
    def case(row):
        if row is None:
            return None
        value = dict(row)
        value["obligations"] = json.loads(value.pop("obligations_json"))
        return value

    @staticmethod
    def version(row):
        if row is None:
            return None
        value = dict(row)
        value["model"] = json.loads(value.pop("model_json"))
        value["metadata"] = json.loads(value.pop("metadata_json"))
        return value

    @staticmethod
    def proposal(row):
        value = dict(row)
        value["model"] = json.loads(value.pop("model_json")) if row["model_json"] else None
        metadata = json.loads(value.pop("metadata_json"))
        value["metadata"] = metadata
        value["material_changes"] = metadata.get("material_changes", [])
        value["synthetic"] = bool(metadata.get("synthetic", False))
        return value

    @staticmethod
    def job(row, full=False):
        value = dict(row)
        identity = value.pop("execution_identity_json", None)
        value["execution_identity"] = json.loads(identity) if identity else None
        raw = value.pop("result_json")
        error = value.pop("error_json")
        value["error"] = json.loads(error) if error else None
        result = json.loads(raw) if raw else None
        if full:
            value["evaluation"] = result
        elif result:
            value["canonical_results"] = result.get("canonical_results")
            value["admission"] = result.get("admission")
        return value

    @staticmethod
    def add_version(conn, case_id, parent, model, metadata):
        version = parent + 1
        timestamp = now()
        conn.execute("INSERT INTO versions VALUES(?,?,?,?,?,?,?)",
                     (case_id, version, parent or None, dumps(model), sha(model), dumps(metadata), timestamp))
        state = "review_required" if metadata.get("review_required") else ("confirmed_synthetic" if metadata.get("synthetic") else "confirmed_declared")
        conn.execute("UPDATE cases SET current_version=?,status=?,updated_at=?,profile=?,obligations_json='[]' WHERE id=?",
                     (version, state, timestamp, model["profile"], case_id))
        return Store.version(conn.execute("SELECT * FROM versions WHERE case_id=? AND version=?", (case_id, version)).fetchone())
