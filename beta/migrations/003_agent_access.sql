-- Additive migration: keep human accounts and their credentials unchanged.
CREATE TABLE agent_accounts (
    user_id TEXT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    kind TEXT NOT NULL CHECK(kind IN('agent','demo')),
    policy_version TEXT NOT NULL,
    created_at INTEGER NOT NULL,
    expires_at INTEGER
);
CREATE TABLE agent_token_grants (
    token_id TEXT PRIMARY KEY REFERENCES api_tokens(id) ON DELETE CASCADE,
    scopes_json TEXT NOT NULL,
    expires_at INTEGER NOT NULL
);
CREATE INDEX agent_account_expiry ON agent_accounts(expires_at);
CREATE INDEX agent_token_expiry ON agent_token_grants(expires_at);
