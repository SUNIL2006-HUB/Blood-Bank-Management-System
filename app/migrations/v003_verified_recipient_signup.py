def migrate(db):
    columns = {row["name"] for row in db.execute("PRAGMA table_info(users)")}
    if "email" not in columns:
        db.execute("ALTER TABLE users ADD COLUMN email TEXT")
    if "email_verified" not in columns:
        db.execute(
            "ALTER TABLE users ADD COLUMN email_verified "
            "INTEGER NOT NULL DEFAULT 0"
        )
    db.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS users_email_unique
        ON users(email COLLATE NOCASE)
        WHERE email IS NOT NULL
        """
    )
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS pending_user_signups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL UNIQUE COLLATE NOCASE,
            otp_hash TEXT NOT NULL,
            expires_at INTEGER NOT NULL,
            attempts INTEGER NOT NULL DEFAULT 0,
            verified_at INTEGER
        )
        """
    )
