import time
from datetime import date

import pytest

from app import _persistent_secret_key, create_app
from app.errors import ValidationError
from app.routes import auth
from app.services.report_service import donation_report
from tests.conftest import TEST_PASSWORD, TEST_USERNAME, VALID_DONOR


def test_five_failed_logins_block_account_until_lockout_expires(
    app, db, monkeypatch
):
    now = [1_800_000_000]
    monkeypatch.setattr(auth.time, "time", lambda: now[0])
    client = app.test_client()

    for _ in range(5):
        response = client.post(
            "/auth/login",
            data={
                "username": TEST_USERNAME,
                "password": "WrongPassword123!",
                "role": "staff",
            },
        )
        assert response.status_code == 401

    blocked = client.post(
        "/auth/login",
        data={
            "username": TEST_USERNAME,
            "password": TEST_PASSWORD,
            "role": "staff",
        },
    )
    assert blocked.status_code == 401

    now[0] += 15 * 60 + 1
    unlocked = client.post(
        "/auth/login",
        data={
            "username": TEST_USERNAME,
            "password": TEST_PASSWORD,
            "role": "staff",
        },
    )

    assert unlocked.status_code == 302
    assert db.execute("SELECT COUNT(*) FROM login_throttle").fetchone()[0] == 0


def test_session_ends_after_fifteen_minutes_of_inactivity(app, client):
    with client.session_transaction() as user_session:
        user_session["last_activity"] = time.time() - 15 * 60 - 1

    response = client.get("/")

    assert response.status_code == 302
    assert response.location.endswith("/auth/login")
    assert b"session expired due to inactivity" in client.get("/auth/login").data


def test_generated_secret_key_is_persistent_and_not_a_fixed_fallback(tmp_path):
    first_key = _persistent_secret_key(tmp_path)

    assert len(first_key) == 64
    assert _persistent_secret_key(tmp_path) == first_key
    assert (tmp_path / ".secret_key").read_text(encoding="utf-8") == first_key


def test_app_uses_persistent_key_when_configuration_is_empty(tmp_path):
    database = tmp_path / "bloodbank.db"
    first = create_app({"DATABASE": str(database), "SECRET_KEY": None})
    second = create_app({"DATABASE": str(database), "SECRET_KEY": None})

    assert first.secret_key
    assert first.secret_key != "dev-only-change-me"
    assert second.secret_key == first.secret_key
    assert (tmp_path / ".secret_key").read_text(encoding="utf-8") == first.secret_key


def test_underscored_age_huge_quantities_and_compact_dates_are_rejected(client):
    donor_response = client.post(
        "/donors/register",
        data={**VALID_DONOR, "age": "2_8"},
    )
    issue_response = client.post(
        "/issues/new",
        data={"blood_group": "O+", "quantity_ml": "999999999999999999999999"},
    )
    date_response = client.post(
        "/donations/new",
        data={
            "donor_id": "1",
            "blood_group": "O+",
            "quantity_ml": "100",
            "donation_date": "20260110",
        },
    )

    assert donor_response.status_code == 400
    assert b"Age must be a positive number" in donor_response.data
    assert issue_response.status_code == 400
    assert b"Quantity is too large" in issue_response.data
    assert date_response.status_code == 400
    assert b"Enter a valid donation date" in date_response.data


def test_oversized_donation_numbers_and_compact_report_dates_are_rejected(
    app, client, db
):
    response = client.post(
        "/donations/new",
        data={
            "donor_id": "999999999999999999999999",
            "blood_group": "O+",
            "quantity_ml": "999999999999999999999999",
            "donation_date": date.today().isoformat(),
        },
    )
    assert response.status_code == 400
    assert b"Quantity is too large" in response.data
    assert b"Donor not found" in response.data

    from werkzeug.security import generate_password_hash

    db.execute(
        "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
        ("test_manager", generate_password_hash("ManagerPassword123!"), "management"),
    )
    manager = app.test_client()
    manager.post(
        "/auth/login",
        data={
            "username": "test_manager",
            "password": "ManagerPassword123!",
            "role": "management",
        },
    )
    report_response = manager.post(
        "/reports",
        data={"report_type": "donation", "start_date": "20260110"},
    )
    assert report_response.status_code == 400
    assert b"Enter a valid date" in report_response.data

    with pytest.raises(ValidationError) as error:
        donation_report(db, {"start_date": "20260110"})
    assert "start_date" in error.value.errors


def test_audit_log_captures_sensitive_actions_without_passwords(app, client, db):
    donor_response = client.post("/donors/register", data=VALID_DONOR)
    assert donor_response.status_code == 302
    donor_id = db.execute(
        "SELECT id FROM donor WHERE phone = ?",
        (VALID_DONOR["phone"],),
    ).fetchone()["id"]
    db.execute(
        "INSERT INTO blood_stock (blood_group, quantity_ml) VALUES ('O+', 500)"
    )

    donation_response = client.post(
        "/donations/new",
        data={
            "donor_id": str(donor_id),
            "blood_group": "O+",
            "quantity_ml": "100",
            "donation_date": date.today().isoformat(),
        },
    )
    issue_response = client.post(
        "/issues/new",
        data={"blood_group": "O+", "quantity_ml": "50"},
    )
    assert donation_response.status_code == 302
    assert issue_response.status_code == 302

    from werkzeug.security import generate_password_hash

    db.execute(
        "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
        ("test_manager", generate_password_hash("ManagerPassword123!"), "management"),
    )
    manager = app.test_client()
    manager.post(
        "/auth/login",
        data={
            "username": "test_manager",
            "password": "ManagerPassword123!",
            "role": "management",
        },
    )
    report_response = manager.post("/reports", data={"report_type": "donation"})
    assert report_response.status_code == 200

    rows = db.execute(
        "SELECT user_id, actor_username, action, created_at FROM audit_log"
    ).fetchall()
    actions = {row["action"] for row in rows}

    assert {
        "login.succeeded",
        "donor.registered",
        "donation.recorded",
        "blood.issue_recorded",
        "report.generated",
    }.issubset(actions)
    assert all(row["created_at"] for row in rows)
    assert all(row["user_id"] is not None for row in rows)
    assert all(row["actor_username"] for row in rows)
    assert "ManagerPassword123!" not in str([dict(row) for row in rows])
    assert TEST_PASSWORD not in str([dict(row) for row in rows])


def test_failed_login_audit_does_not_store_password(app, db):
    client = app.test_client()
    secret_password = "NeverStoreThisPassword123!"
    response = client.post(
        "/auth/login",
        data={
            "username": TEST_USERNAME,
            "password": secret_password,
            "role": "staff",
        },
    )

    assert response.status_code == 401
    row = db.execute(
        """
        SELECT actor_username, action
        FROM audit_log
        WHERE action = 'login.failed'
        ORDER BY id DESC LIMIT 1
        """
    ).fetchone()
    assert row["actor_username"] == TEST_USERNAME
    assert row["action"] == "login.failed"
    assert secret_password not in str(dict(row))


def test_request_larger_than_limit_returns_readable_413(client):
    response = client.post(
        "/donors/register",
        data={"name": "x" * (17 * 1024)},
    )

    assert response.status_code == 413
    assert b"Request too large" in response.data
    assert b"Traceback" not in response.data


def test_management_account_changes_are_audited_without_temporary_passwords(
    app, db
):
    from werkzeug.security import generate_password_hash

    db.execute(
        "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
        ("test_manager", generate_password_hash("ManagerPassword123!"), "management"),
    )
    manager = app.test_client()
    manager.post(
        "/auth/login",
        data={
            "username": "test_manager",
            "password": "ManagerPassword123!",
            "role": "management",
        },
    )
    created = manager.post(
        "/users/create",
        data={"username": "managed_staff", "role": "staff"},
        follow_redirects=True,
    )
    target_id = db.execute(
        "SELECT id FROM users WHERE username = 'managed_staff'"
    ).fetchone()["id"]
    manager.post(f"/users/{target_id}/set-disabled", data={"disabled": "1"})
    manager.post(f"/users/{target_id}/set-disabled", data={"disabled": "0"})
    reset = manager.post(
        f"/users/{target_id}/reset-password",
        follow_redirects=True,
    )

    assert b"Temporary password for managed_staff" in created.data
    assert b"Temporary password for managed_staff" in reset.data
    actions = {
        row["action"]
        for row in db.execute(
            "SELECT action FROM audit_log WHERE actor_username = 'test_manager'"
        )
    }
    assert {
        "user.created",
        "user.disabled",
        "user.enabled",
        "user.password_reset",
    }.issubset(actions)
    audit_entries = db.execute(
        """
        SELECT user_id, actor_username, action, target_id, created_at
        FROM audit_log
        WHERE actor_username = 'test_manager'
        """
    ).fetchall()
    assert all(row["user_id"] is not None for row in audit_entries)
    assert all(row["created_at"] for row in audit_entries)
    assert "ManagerPassword123!" not in str([dict(row) for row in audit_entries])
