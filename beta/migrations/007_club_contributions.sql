-- Private provenance links to immutable public deposits; no credential storage.
CREATE TABLE club_contributions (
    member_id TEXT NOT NULL REFERENCES club_members(id) ON DELETE CASCADE,
    request_id TEXT NOT NULL,
    contribution_id TEXT NOT NULL REFERENCES contribution_inbox(id),
    request_sha256 TEXT NOT NULL,
    selections_json TEXT NOT NULL,
    previous_id TEXT,
    created_at INTEGER NOT NULL,
    PRIMARY KEY(member_id,request_id),
    UNIQUE(member_id,contribution_id)
);
CREATE TABLE contribution_review_cache (
    contribution_id TEXT PRIMARY KEY REFERENCES contribution_inbox(id),
    checked_at INTEGER,
    next_check_at INTEGER NOT NULL DEFAULT 0,
    result_json TEXT,
    error_code TEXT
);
CREATE TABLE contribution_public_revisions (
    sha TEXT PRIMARY KEY,
    verified_at INTEGER NOT NULL
);
