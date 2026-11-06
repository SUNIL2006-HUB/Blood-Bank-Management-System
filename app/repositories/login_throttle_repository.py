import hashlib

from ..db import transaction

ATTEMPT_LIMIT = 5
WINDOW_SECONDS = 15 * 60
LOCKOUT_SECONDS = 15 * 60


def _key(username):
    return hashlib.sha256(username.strip().casefold().encode("utf-8")).hexdigest()


def is_blocked(db, username, remote_addr, now):
    row = db.execute(
        """
        SELECT blocked_until
        FROM login_throttle
        WHERE username_key = ? AND remote_addr = ?
        """,
        (_key(username), remote_addr),
    ).fetchone()
    return (
        row is not None
        and row["blocked_until"] is not None
        and row["blocked_until"] > now
    )


def record_failure(db, username, remote_addr, now):
    username_key = _key(username)
    with transaction(db):
        db.execute(
            "DELETE FROM login_throttle WHERE window_started_at < ?",
            (now - 24 * 60 * 60,),
        )
        row = db.execute(
            """
            SELECT failed_attempts, window_started_at
            FROM login_throttle
            WHERE username_key = ? AND remote_addr = ?
            """,
            (username_key, remote_addr),
        ).fetchone()

        if row is None or now - row["window_started_at"] >= WINDOW_SECONDS:
            attempts, window_started_at = 1, now
        else:
            attempts = row["failed_attempts"] + 1
            window_started_at = row["window_started_at"]

        blocked_until = now + LOCKOUT_SECONDS if attempts >= ATTEMPT_LIMIT else None
        db.execute(
            """
            INSERT INTO login_throttle
                (username_key, remote_addr, failed_attempts, window_started_at, blocked_until)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT (username_key, remote_addr) DO UPDATE SET
                failed_attempts = excluded.failed_attempts,
                window_started_at = excluded.window_started_at,
                blocked_until = excluded.blocked_until
            """,
            (username_key, remote_addr, attempts, window_started_at, blocked_until),
        )
    return attempts >= ATTEMPT_LIMIT


def clear_failures(db, username, remote_addr):
    db.execute(
        "DELETE FROM login_throttle WHERE username_key = ? AND remote_addr = ?",
        (_key(username), remote_addr),
    )
