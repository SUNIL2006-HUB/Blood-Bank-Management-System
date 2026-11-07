import sqlite3

from werkzeug.security import check_password_hash

from app import create_app
from app.db import connect, init_db
from scripts.manage_db import backup_database, restore_database, seed_demo_data


def test_app_start_does_not_seed_demo_data_automatically(tmp_path):
    database_path = tmp_path / "bloodbank.db"
    create_app({"DATABASE": str(database_path), "SECRET_KEY": "test-key"})

    db = connect(database_path)
    try:
        assert db.execute("SELECT COUNT(*) FROM donor").fetchone()[0] == 0
        assert db.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0
        assert db.execute("SELECT COUNT(*) FROM demo_seed_state").fetchone()[0] == 0
    finally:
        db.close()


def test_existing_data_survives_app_restart_and_migrations(tmp_path):
    database_path = tmp_path / "bloodbank.db"
    first_app = create_app(
        {"DATABASE": str(database_path), "SECRET_KEY": "test-key"}
    )
    with first_app.app_context():
        db = connect(database_path)
        db.execute(
            """
            INSERT INTO donor (name, age, blood_group, phone)
            VALUES (?, ?, ?, ?)
            """,
            ("Persistent donor", 28, "O+", "9123456789"),
        )
        db.close()

    second_app = create_app(
        {"DATABASE": str(database_path), "SECRET_KEY": "test-key"}
    )
    with second_app.app_context():
        db = connect(database_path)
        donor = db.execute(
            "SELECT name FROM donor WHERE phone = ?",
            ("9123456789",),
        ).fetchone()
        versions = [
            row["version"]
            for row in db.execute(
                "SELECT version FROM schema_migrations ORDER BY version"
            )
        ]
        db.close()

    assert donor["name"] == "Persistent donor"
    assert versions == [1, 2, 3, 4]


def test_backup_restore_recovers_database_and_saves_pre_restore_copy(tmp_path):
    database_path = tmp_path / "bloodbank.db"
    app = create_app(
        {"DATABASE": str(database_path), "SECRET_KEY": "test-key"}
    )
    with app.app_context():
        db = connect(database_path)
        db.execute(
            """
            INSERT INTO donor (name, age, blood_group, phone)
            VALUES (?, ?, ?, ?)
            """,
            ("Backed-up donor", 31, "A-", "9123456780"),
        )
        db.close()

    backup_path = backup_database(database_path, tmp_path / "bloodbank.backup")
    db = sqlite3.connect(database_path)
    try:
        db.execute("DELETE FROM donor")
    finally:
        db.close()

    safety_backup = restore_database(backup_path, database_path, confirm=True)

    assert safety_backup is not None
    assert safety_backup.is_file()
    db = sqlite3.connect(database_path)
    try:
        restored = db.execute("SELECT name FROM donor").fetchone()
    finally:
        db.close()
    assert restored == ("Backed-up donor",)


def test_restore_refuses_existing_database_without_confirmation(tmp_path):
    database_path = tmp_path / "bloodbank.db"
    backup_path = tmp_path / "backup.db"
    create_app({"DATABASE": str(database_path), "SECRET_KEY": "test-key"})
    with sqlite3.connect(backup_path) as db:
        db.execute("CREATE TABLE sample (value TEXT)")
        db.execute("INSERT INTO sample VALUES ('backup')")

    try:
        restore_database(backup_path, database_path)
    except ValueError as error:
        assert "--yes" in str(error)
    else:
        raise AssertionError("restore replaced an existing database without confirmation")


def test_demo_seed_adds_complete_repeatable_dataset(tmp_path):
    database_path = tmp_path / "bloodbank.db"
    demo_password = "Pass1234"
    assert seed_demo_data(database_path, demo_password) is True

    with sqlite3.connect(database_path) as db:
        donor_count = db.execute("SELECT COUNT(*) FROM donor").fetchone()[0]
        donation_count = db.execute("SELECT COUNT(*) FROM donation").fetchone()[0]
        issue_count = db.execute("SELECT COUNT(*) FROM blood_issue").fetchone()[0]
        stock = dict(db.execute("SELECT blood_group, quantity_ml FROM blood_stock"))
        users = db.execute(
            """
            SELECT username, role, password_hash, must_change_password
            FROM users ORDER BY username
            """
        ).fetchall()
        seed_count = db.execute("SELECT COUNT(*) FROM demo_seed_state").fetchone()[0]

    assert donor_count == 25
    assert donation_count == 25
    assert issue_count == 8
    assert set(stock) == {"A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"}
    assert all(quantity > 0 for quantity in stock.values())
    assert [row[0] for row in users] == [
        "demo_manager",
        "demo_recipient",
        "demo_staff",
    ]
    assert all(check_password_hash(row[2], demo_password) for row in users)
    assert all(row[3] == 1 for row in users)
    assert seed_count == 1

    assert seed_demo_data(database_path, demo_password) is False
    with sqlite3.connect(database_path) as db:
        assert db.execute("SELECT COUNT(*) FROM donor").fetchone()[0] == 25
        assert db.execute("SELECT COUNT(*) FROM donation").fetchone()[0] == 25
        assert db.execute("SELECT COUNT(*) FROM blood_issue").fetchone()[0] == 8


def test_seeded_demo_manager_can_log_in_and_is_prompted_to_change_password(tmp_path):
    database_path = tmp_path / "bloodbank.db"
    password = "Pass1234"
    seed_demo_data(database_path, password)
    app = create_app(
        {"DATABASE": str(database_path), "SECRET_KEY": "test-key"}
    )

    response = app.test_client().post(
        "/auth/login",
        data={
            "username": "demo_manager",
            "password": password,
            "role": "management",
        },
    )

    assert response.status_code == 302
    assert response.location.endswith("/auth/change-password")


def test_demo_seed_rejects_password_shorter_than_eight_characters(tmp_path):
    database_path = tmp_path / "bloodbank.db"

    try:
        seed_demo_data(database_path, "Pass123")
    except ValueError as error:
        assert "at least 8 characters" in str(error)
    else:
        raise AssertionError("demo seed accepted a password shorter than eight characters")


def test_database_migrations_are_idempotent_and_reject_unknown_version(tmp_path):
    database_path = tmp_path / "bloodbank.db"
    init_db(database_path)
    init_db(database_path)
    db = connect(database_path)
    try:
        versions = [
            row["version"]
            for row in db.execute(
                "SELECT version FROM schema_migrations ORDER BY version"
            )
        ]
        db.execute("INSERT INTO schema_migrations (version) VALUES (999)")
    finally:
        db.close()

    try:
        init_db(database_path)
    except RuntimeError as error:
        assert "unsupported migration versions: 999" in str(error)
    else:
        raise AssertionError("unknown schema version was accepted")

    assert versions == [1, 2, 3, 4]
