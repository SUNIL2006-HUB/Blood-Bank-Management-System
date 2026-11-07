import argparse
import getpass
import os
import secrets
import sqlite3
import sys
from datetime import UTC, datetime
from pathlib import Path

from werkzeug.security import generate_password_hash

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

BLOOD_GROUPS = ("A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-")
DEMO_SEED_KEY = "demo-data-v1"
DEMO_USERS = (
    ("demo_manager", "management"),
    ("demo_staff", "staff"),
    ("demo_recipient", "recipient"),
)
DONOR_NAMES = (
    "Demo Donor 01", "Demo Donor 02", "Demo Donor 03", "Demo Donor 04",
    "Demo Donor 05", "Demo Donor 06", "Demo Donor 07", "Demo Donor 08",
    "Demo Donor 09", "Demo Donor 10", "Demo Donor 11", "Demo Donor 12",
    "Demo Donor 13", "Demo Donor 14", "Demo Donor 15", "Demo Donor 16",
    "Demo Donor 17", "Demo Donor 18", "Demo Donor 19", "Demo Donor 20",
    "Demo Donor 21", "Demo Donor 22", "Demo Donor 23", "Demo Donor 24",
    "Demo Donor 25",
)


def _database_path():
    return Path(os.environ.get("DATABASE_PATH", PROJECT_ROOT / "instance" / "bloodbank.db"))


def _integrity_check(path):
    connection = sqlite3.connect(path)
    try:
        result = connection.execute("PRAGMA integrity_check").fetchone()
    finally:
        connection.close()
    if result is None or result[0] != "ok":
        raise ValueError(f"SQLite integrity check failed for {path}")


def _copy_database(source, destination):
    source_connection = sqlite3.connect(source)
    try:
        destination_connection = sqlite3.connect(destination)
        try:
            source_connection.backup(destination_connection)
        finally:
            destination_connection.close()
    finally:
        source_connection.close()
    os.chmod(destination, 0o600)


def backup_database(source, destination=None):
    source = Path(source).resolve()
    if not source.is_file():
        raise ValueError(f"Database does not exist: {source}")

    if destination is None:
        timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        destination = source.with_name(f"{source.name}.{timestamp}.backup")
    destination = Path(destination).resolve()

    if source == destination:
        raise ValueError("Backup destination must differ from the database path")
    if destination.exists():
        raise ValueError(f"Backup already exists; refusing to overwrite: {destination}")

    destination.parent.mkdir(parents=True, exist_ok=True)
    _integrity_check(source)
    _copy_database(source, destination)
    _integrity_check(destination)
    return destination


def restore_database(source, destination, confirm=False):
    source = Path(source).resolve()
    destination = Path(destination).resolve()
    if not source.is_file():
        raise ValueError(f"Backup does not exist: {source}")
    if source == destination:
        raise ValueError("Restore source and database destination must differ")
    if destination.exists() and not confirm:
        raise ValueError(
            "The database already exists; rerun with --yes after stopping the app"
        )

    _integrity_check(source)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(f".{destination.name}.restore.tmp")
    if temporary.exists():
        raise ValueError(f"Temporary restore file already exists: {temporary}")

    safety_backup = None
    try:
        _copy_database(source, temporary)
        _integrity_check(temporary)
        if destination.exists():
            timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
            safety_backup = destination.with_name(
                f"{destination.name}.{timestamp}-{secrets.token_hex(4)}.pre-restore"
            )
            _copy_database(destination, safety_backup)
            _integrity_check(safety_backup)
        os.replace(temporary, destination)
    finally:
        if temporary.exists():
            temporary.unlink()

    return safety_backup


def seed_demo_data(database_path, password):
    if len(password) < 8:
        raise ValueError("Demo-account password must contain at least 8 characters")

    from app import create_app
    from app.db import get_db, transaction
    from app.repositories import issue_repository, stock_repository

    app = create_app({"DATABASE": str(database_path)})
    password_hash = generate_password_hash(password)

    with app.app_context():
        connection = get_db()
        with transaction(connection):
            seeded = connection.execute(
                "SELECT 1 FROM demo_seed_state WHERE seed_key = ?",
                (DEMO_SEED_KEY,),
            ).fetchone()
            if seeded:
                return False

            existing_users = connection.execute(
                "SELECT username FROM users WHERE username IN (?, ?, ?)",
                tuple(username for username, _role in DEMO_USERS),
            ).fetchall()
            if existing_users:
                names = ", ".join(row["username"] for row in existing_users)
                raise ValueError(
                    f"Demo usernames already exist without a completed seed: {names}"
                )

            phones = tuple(str(9000000000 + index) for index in range(len(DONOR_NAMES)))
            placeholders = ",".join("?" for _ in phones)
            existing_donors = connection.execute(
                f"SELECT phone FROM donor WHERE phone IN ({placeholders})",
                phones,
            ).fetchall()
            if existing_donors:
                raise ValueError(
                    "One or more reserved demo donor phone numbers already exist"
                )

            connection.executemany(
                """
                INSERT INTO users (username, password_hash, role, must_change_password)
                VALUES (?, ?, ?, 1)
                """,
                (
                    (username, password_hash, role)
                    for username, role in DEMO_USERS
                ),
            )

            donor_ids = []
            for index, name in enumerate(DONOR_NAMES):
                blood_group = BLOOD_GROUPS[index % len(BLOOD_GROUPS)]
                cursor = connection.execute(
                    """
                    INSERT INTO donor (name, age, blood_group, phone)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        name,
                        20 + index % 36,
                        blood_group,
                        str(9000000000 + index),
                    ),
                )
                donor_ids.append((cursor.lastrowid, blood_group))

            for index, (donor_id, blood_group) in enumerate(donor_ids):
                quantity = 300 + (index % 4) * 50
                connection.execute(
                    """
                    INSERT INTO donation (donor_id, blood_group, quantity_ml, donation_date)
                    VALUES (?, ?, ?, date('now', ?))
                    """,
                    (donor_id, blood_group, quantity, f"-{index + 1} days"),
                )
                stock_repository.add(connection, blood_group, quantity)

            for blood_group in BLOOD_GROUPS:
                issue_repository.create(
                    connection,
                    blood_group,
                    100,
                    f"Demo Hospital {blood_group}",
                )
                stock_repository.remove(connection, blood_group, 100)

            connection.execute(
                "INSERT INTO demo_seed_state (seed_key) VALUES (?)",
                (DEMO_SEED_KEY,),
            )
    return True


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Back up, restore, or explicitly seed the Blood Bank database."
    )
    commands = parser.add_subparsers(dest="command", required=True)

    backup_parser = commands.add_parser("backup", help="Create a verified SQLite backup")
    backup_parser.add_argument("destination", nargs="?")

    restore_parser = commands.add_parser("restore", help="Restore a verified SQLite backup")
    restore_parser.add_argument("source")
    restore_parser.add_argument("--yes", action="store_true")

    commands.add_parser("seed-demo", help="Insert the repeatable demonstration dataset")

    args = parser.parse_args(argv)
    try:
        database_path = _database_path()
        if args.command == "backup":
            destination = backup_database(database_path, args.destination)
            print(f"Verified backup created: {destination}")
        elif args.command == "restore":
            safety_backup = restore_database(
                args.source,
                database_path,
                confirm=args.yes,
            )
            if safety_backup:
                print(f"Pre-restore safety backup created: {safety_backup}")
            print(f"Database restored from: {Path(args.source).resolve()}")
        else:
            password = getpass.getpass("Set demo-account password (at least 8 characters): ")
            confirmation = getpass.getpass("Confirm demo-account password: ")
            if password != confirmation:
                raise ValueError("Demo-account passwords do not match")
            if seed_demo_data(database_path, password):
                print("Demo data seeded: 25 donors, activity, all blood groups, and 3 users.")
            else:
                print("Demo data is already present; no changes made.")
    except (EOFError, OSError, sqlite3.Error, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
