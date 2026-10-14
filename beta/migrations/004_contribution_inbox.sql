CREATE TABLE contribution_inbox (
  sequence INTEGER PRIMARY KEY AUTOINCREMENT,
  id TEXT NOT NULL UNIQUE,
  received_at INTEGER NOT NULL,
  payload_json TEXT NOT NULL,
  payload_bytes INTEGER NOT NULL
);
