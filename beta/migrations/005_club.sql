-- Additive: private member data is separate from the public contribution inbox.
CREATE TABLE club_members (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL UNIQUE REFERENCES agent_accounts(user_id) ON DELETE CASCADE,
    alias TEXT,
    policy_version TEXT NOT NULL,
    profile_version INTEGER NOT NULL DEFAULT 1,
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL
);
CREATE TABLE club_files (
    id TEXT PRIMARY KEY,
    member_id TEXT NOT NULL REFERENCES club_members(id) ON DELETE CASCADE,
    request_id TEXT NOT NULL,
    name TEXT NOT NULL,
    media_type TEXT NOT NULL,
    current_version INTEGER NOT NULL DEFAULT 1,
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL,
    UNIQUE(member_id, request_id)
);
CREATE TABLE club_file_versions (
    file_id TEXT NOT NULL REFERENCES club_files(id) ON DELETE CASCADE,
    version INTEGER NOT NULL,
    content TEXT NOT NULL,
    sha256 TEXT NOT NULL,
    size_bytes INTEGER NOT NULL,
    created_at INTEGER NOT NULL,
    PRIMARY KEY(file_id, version)
);
CREATE INDEX club_files_member ON club_files(member_id, created_at, id);
