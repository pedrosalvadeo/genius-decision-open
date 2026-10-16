-- Preserve every identity, request and accepted birth; NULL means no time expiry.
CREATE TABLE network_hosts_v2 (
    node_id TEXT PRIMARY KEY REFERENCES network_nodes(id) ON DELETE CASCADE,
    offer_hash TEXT NOT NULL,
    signed_offer TEXT NOT NULL,
    expires_at INTEGER,
    disabled INTEGER NOT NULL DEFAULT 0 CHECK(disabled IN (0,1))
);
CREATE TABLE network_host_requests_v2 (
    id TEXT PRIMARY KEY,
    host_id TEXT NOT NULL REFERENCES network_hosts_v2(node_id) ON DELETE CASCADE,
    requester_id TEXT NOT NULL REFERENCES network_nodes(id) ON DELETE CASCADE,
    offer_hash TEXT NOT NULL,
    world_id TEXT NOT NULL,
    focus_json TEXT NOT NULL,
    created_at INTEGER NOT NULL,
    expires_at INTEGER,
    status TEXT NOT NULL CHECK(status IN ('PENDING','ACTIVE','REJECTED','CANCELLED','STOPPED')),
    child_id TEXT UNIQUE REFERENCES network_nodes(id) ON DELETE SET NULL,
    accepted_at INTEGER
);
INSERT INTO network_hosts_v2 SELECT * FROM network_hosts;
INSERT INTO network_host_requests_v2 SELECT * FROM network_host_requests;
DROP TABLE network_host_requests;
DROP TABLE network_hosts;
ALTER TABLE network_hosts_v2 RENAME TO network_hosts;
ALTER TABLE network_host_requests_v2 RENAME TO network_host_requests;
CREATE INDEX network_host_queue ON network_host_requests(host_id,created_at,id);
ALTER TABLE network_hosts ADD COLUMN previous_signed_offer TEXT;
