import sqlite3
from contextlib import contextmanager
from pathlib import Path

from flask import current_app, g

from .migrations import MIGRATIONS

SCHEMA = Path(__file__).with_name("schema.sql")


def connect(path):
    # autocommit mode: transactions are explicit via transaction() below
    conn = sqlite3.connect(path, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def get_db():
    if "db" not in g:
        g.db = connect(current_app.config["DATABASE"])
    return g.db


def close_db(_exc=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db(path):
    conn = connect(path)
    try:
        conn.executescript(SCHEMA.read_text(encoding="utf-8"))
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version INTEGER PRIMARY KEY,
                applied_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
            """
        )
        applied = {
            row["version"]
            for row in conn.execute("SELECT version FROM schema_migrations")
        }
        supported_versions = {version for version, _migration in MIGRATIONS}
        unknown_versions = applied - supported_versions
        if unknown_versions:
            versions = ", ".join(str(version) for version in sorted(unknown_versions))
            raise RuntimeError(f"Database has unsupported migration versions: {versions}")

        for version, migration in MIGRATIONS:
            if version in applied:
                continue
            conn.execute("BEGIN IMMEDIATE")
            try:
                migration(conn)
                conn.execute(
                    "INSERT INTO schema_migrations (version) VALUES (?)",
                    (version,),
                )
                conn.execute("COMMIT")
            except BaseException:
                if conn.in_transaction:
                    conn.execute("ROLLBACK")
                raise
    finally:
        conn.close()


@contextmanager
def transaction(db):
    """All-or-nothing unit of work (SEC-08)."""
    db.execute("BEGIN IMMEDIATE")
    try:
        yield db
    except BaseException:
        db.execute("ROLLBACK")
        raise
    else:
        db.execute("COMMIT")
