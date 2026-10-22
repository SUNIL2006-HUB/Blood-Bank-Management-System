CREATE TABLE IF NOT EXISTS donor (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL,
    age         INTEGER NOT NULL CHECK (age > 0),
    blood_group TEXT    NOT NULL,
    phone       TEXT    NOT NULL UNIQUE,
    created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);
