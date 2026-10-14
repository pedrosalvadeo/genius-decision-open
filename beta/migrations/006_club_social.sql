-- Public discovery and contact are opt-in, separate from the private member alias.
ALTER TABLE club_members ADD COLUMN social_version INTEGER NOT NULL DEFAULT 0;
CREATE TABLE club_social_profiles (
    id TEXT PRIMARY KEY,
    member_id TEXT NOT NULL UNIQUE REFERENCES club_members(id) ON DELETE CASCADE,
    version INTEGER NOT NULL,
    public_name TEXT,
    summary TEXT NOT NULL,
    capabilities_json TEXT NOT NULL,
    directory_visible INTEGER NOT NULL CHECK(directory_visible IN (0,1)),
    accept_requests INTEGER NOT NULL CHECK(accept_requests IN (0,1)),
    policy_version TEXT NOT NULL,
    updated_at INTEGER NOT NULL
);
CREATE TABLE club_conversations (
    id TEXT PRIMARY KEY,
    initiator_id TEXT NOT NULL REFERENCES club_members(id) ON DELETE CASCADE,
    recipient_id TEXT NOT NULL REFERENCES club_members(id) ON DELETE CASCADE,
    pair_low TEXT NOT NULL,
    pair_high TEXT NOT NULL,
    request_id TEXT NOT NULL,
    topic TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('pending','active','declined','closed')),
    version INTEGER NOT NULL DEFAULT 1,
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL,
    CHECK(initiator_id != recipient_id),
    UNIQUE(pair_low,pair_high),
    UNIQUE(initiator_id,request_id)
);
CREATE TABLE club_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id TEXT NOT NULL REFERENCES club_conversations(id) ON DELETE CASCADE,
    sender_id TEXT NOT NULL REFERENCES club_members(id) ON DELETE CASCADE,
    request_id TEXT NOT NULL,
    content TEXT NOT NULL,
    sha256 TEXT NOT NULL,
    size_bytes INTEGER NOT NULL,
    created_at INTEGER NOT NULL,
    UNIQUE(conversation_id,sender_id,request_id)
);
CREATE TABLE club_blocks (
    id TEXT PRIMARY KEY,
    blocker_id TEXT NOT NULL REFERENCES club_members(id) ON DELETE CASCADE,
    blocked_id TEXT NOT NULL REFERENCES club_members(id) ON DELETE CASCADE,
    created_at INTEGER NOT NULL,
    CHECK(blocker_id != blocked_id),
    UNIQUE(blocker_id,blocked_id)
);
CREATE INDEX club_messages_conversation ON club_messages(conversation_id,id);
CREATE INDEX club_conversations_recipient ON club_conversations(recipient_id,updated_at);
