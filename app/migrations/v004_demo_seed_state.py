def migrate(db):
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS demo_seed_state (
            seed_key TEXT PRIMARY KEY,
            seeded_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
        """
    )
