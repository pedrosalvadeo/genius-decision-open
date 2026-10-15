CREATE TABLE mission_regulation (
 singleton INTEGER PRIMARY KEY CHECK(singleton=1), state_json TEXT NOT NULL
);
CREATE TABLE mission_regulation_events (
 sequence INTEGER PRIMARY KEY AUTOINCREMENT, created_at INTEGER NOT NULL,
 kind TEXT NOT NULL, receipt_json TEXT NOT NULL
);
CREATE INDEX mission_regulation_event_time ON mission_regulation_events(created_at);
