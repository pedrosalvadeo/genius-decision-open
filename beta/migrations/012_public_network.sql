-- Public opt-in node profiles and signed public views; account deletion cascades.
CREATE TABLE network_nodes (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL UNIQUE REFERENCES agent_accounts(user_id) ON DELETE CASCADE,
    public_key TEXT NOT NULL UNIQUE,
    label TEXT NOT NULL,
    topics_json TEXT NOT NULL,
    created_at INTEGER NOT NULL,
    last_seen INTEGER NOT NULL
);
CREATE TABLE network_views (
    hash TEXT PRIMARY KEY,
    node_id TEXT NOT NULL REFERENCES network_nodes(id) ON DELETE CASCADE,
    world_id TEXT NOT NULL,
    view_hash TEXT NOT NULL,
    envelope_json TEXT NOT NULL,
    size_bytes INTEGER NOT NULL,
    created_at INTEGER NOT NULL
);
CREATE INDEX network_views_world ON network_views(world_id,hash);
CREATE INDEX network_views_node ON network_views(node_id,hash);
