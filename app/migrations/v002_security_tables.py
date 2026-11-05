def migrate(db):
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS login_throttle (
            username_key TEXT NOT NULL,
            remote_addr TEXT NOT NULL,
            failed_attempts INTEGER NOT NULL,
            window_started_at INTEGER NOT NULL,
            blocked_until INTEGER,
            PRIMARY KEY (username_key, remote_addr)
        )
        """
    )
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
            actor_username TEXT NOT NULL,
            action TEXT NOT NULL,
            target_type TEXT,
            target_id INTEGER,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
        """
    )
