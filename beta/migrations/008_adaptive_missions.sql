CREATE TABLE adaptive_missions (
 id TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
 idempotency_key TEXT NOT NULL, request_sha256 TEXT NOT NULL, input_json TEXT NOT NULL,
 status TEXT NOT NULL CHECK(status IN ('draft','queued','running','completed','interrupted','failed','needs_review','cancelled')),
 last_stage TEXT, state_bundle BLOB, state_sha256 TEXT, result_json TEXT,
 artifact BLOB, artifact_name TEXT, artifact_sha256 TEXT,
 attempts INTEGER NOT NULL DEFAULT 0, cancel_requested INTEGER NOT NULL DEFAULT 0,
 error TEXT, created_at INTEGER NOT NULL, updated_at INTEGER NOT NULL,
 UNIQUE(user_id,idempotency_key)
);
CREATE INDEX adaptive_missions_queue ON adaptive_missions(status,created_at);
CREATE INDEX adaptive_missions_owner ON adaptive_missions(user_id,updated_at);
