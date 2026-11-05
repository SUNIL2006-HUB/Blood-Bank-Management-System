def migrate(db):
    columns = {row["name"] for row in db.execute("PRAGMA table_info(users)")}
    if "disabled" not in columns:
        db.execute(
            "ALTER TABLE users ADD COLUMN disabled INTEGER NOT NULL DEFAULT 0"
        )
    if "must_change_password" not in columns:
        db.execute(
            "ALTER TABLE users ADD COLUMN must_change_password "
            "INTEGER NOT NULL DEFAULT 0"
        )
