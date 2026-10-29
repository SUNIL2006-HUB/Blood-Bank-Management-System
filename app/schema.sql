CREATE TABLE IF NOT EXISTS donor (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL,
    age         INTEGER NOT NULL CHECK (age > 0),
    blood_group TEXT    NOT NULL,
    phone       TEXT    NOT NULL UNIQUE,
    created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS blood_stock (
    blood_group  TEXT PRIMARY KEY,
    quantity_ml  INTEGER NOT NULL DEFAULT 0 CHECK (quantity_ml >= 0),
    updated_at   TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS donation (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    donor_id      INTEGER NOT NULL REFERENCES donor(id),
    blood_group   TEXT    NOT NULL,
    quantity_ml   INTEGER NOT NULL CHECK (quantity_ml > 0),
    donation_date TEXT    NOT NULL,
    created_at    TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS blood_issue (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    blood_group TEXT    NOT NULL,
    quantity_ml INTEGER NOT NULL CHECK (quantity_ml > 0),
    recipient   TEXT,
    issued_at   TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK (
        role IN ('staff', 'recipient', 'management')
    ),
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
