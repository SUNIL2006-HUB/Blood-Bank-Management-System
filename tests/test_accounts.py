import re
import sqlite3

from werkzeug.security import generate_password_hash

from app.db import connect, init_db
from tests.conftest import TEST_PASSWORD, TEST_USERNAME


def create_account(db, username, role, password="PasswordForTest123!"):
    cursor = db.execute(
        """
        INSERT INTO users (username, password_hash, role)
        VALUES (?, ?, ?)
        """,
        (username, generate_password_hash(password), role),
    )
    return cursor.lastrowid


def login(client, username, role, password="PasswordForTest123!"):
    return client.post(
        "/auth/login",
        data={"username": username, "password": password, "role": role},
    )


def test_login_page_has_no_operational_menu_or_hours(anonymous_client):
    response = anonymous_client.get("/auth/login")
    page = response.data.decode()

    assert response.status_code == 200
    assert "name=\"role\"" in page
    assert 'value="recipient"' in page and ">User</option>" in page
    assert 'value="staff"' in page and ">Staff</option>" in page
    assert 'value="management"' in page and ">Management</option>" in page
    assert "Operating hours" not in page
    assert "Open now" not in page
    assert "Closed now" not in page
    assert "Register donor" not in page
    assert "Availability" not in page


def test_login_password_has_accessible_show_hide_control(anonymous_client):
    page = anonymous_client.get("/auth/login").data.decode()

    assert 'id="password"' in page
    assert 'type="password"' in page
    assert 'type="button"' in page
    assert 'class="password-toggle"' in page
    assert 'aria-controls="password"' in page
    assert 'aria-pressed="false"' in page
    assert 'passwordToggle.textContent = isVisible ? "Show" : "Hide"' in page


def test_login_offers_signup_link_for_user_role(anonymous_client):
    page = anonymous_client.get("/auth/login").data.decode()

    assert 'id="user-signup-link" hidden' in page
    assert 'href="/auth/signup">Sign up</a>' in page
    assert 'signupLink.hidden = roleSelect.value !== "recipient"' in page


def test_signup_page_loads(anonymous_client):
    response = anonymous_client.get("/auth/signup")

    assert response.status_code == 200
    assert b'name="signup_username"' in response.data
    assert b'name="password"' in response.data
    assert b'name="confirmation"' in response.data
    assert b'email' not in response.data.lower()


def test_login_requires_selected_role_to_match_account(anonymous_client):
    response = login(anonymous_client, TEST_USERNAME, "management", TEST_PASSWORD)

    assert response.status_code == 401
    assert b"Invalid username or password." in response.data
    assert b"test_staff" not in response.data


def test_users_redirect_to_role_specific_landing_page(app, db):
    create_account(db, "recipient_account", "recipient")
    create_account(db, "manager_account", "management")

    staff_response = login(app.test_client(), TEST_USERNAME, "staff", TEST_PASSWORD)
    user_response = login(app.test_client(), "recipient_account", "recipient")
    manager_response = login(app.test_client(), "manager_account", "management")

    assert staff_response.location.endswith("/")
    assert user_response.location.endswith("/availability")
    assert manager_response.location.endswith("/reports")


def test_role_routes_and_navigation_are_restricted(app, db):
    create_account(db, "recipient_account", "recipient")
    create_account(db, "manager_account", "management")

    recipient = app.test_client()
    login(recipient, "recipient_account", "recipient")
    availability = recipient.get("/availability")
    recipient_menu = availability.data.decode()
    assert availability.status_code == 200
    assert "Availability" in recipient_menu
    assert "Register donor" not in recipient_menu
    assert "Operating hours" not in recipient_menu
    assert recipient.get("/donors").status_code == 403
    assert recipient.get("/issues/new").status_code == 403
    assert recipient.get("/reports").status_code == 403

    staff = app.test_client()
    login(staff, TEST_USERNAME, "staff", TEST_PASSWORD)
    staff_home = staff.get("/")
    assert staff_home.status_code == 200
    assert b"Operating hours" not in staff_home.data
    assert b"Open now" not in staff_home.data
    assert b"Closed now" not in staff_home.data
    assert staff.get("/reports").status_code == 403
    assert staff.get("/users").status_code == 403
    assert staff.get("/donors").status_code == 200

    manager = app.test_client()
    login(manager, "manager_account", "management")
    manager_menu = manager.get("/users").data.decode()
    assert "Users" in manager_menu
    assert "Reports" in manager_menu
    assert "Availability" not in manager_menu
    assert manager.get("/donors").status_code == 403
    assert manager.get("/availability").status_code == 403
    assert manager.get("/reports").status_code == 200


def test_first_management_setup_can_only_be_used_once(anonymous_client, db):
    setup_response = anonymous_client.post(
        "/auth/setup",
        data={"username": "first_manager", "password": "SecurePassword123!"},
    )

    assert setup_response.status_code == 302
    assert anonymous_client.get("/auth/setup").status_code == 404
    assert anonymous_client.get("/reports/login").status_code == 404
    manager = db.execute(
        "SELECT role FROM users WHERE username = 'first_manager'"
    ).fetchone()
    assert manager["role"] == "management"


def test_first_manager_is_sent_to_management_login_and_can_sign_in(anonymous_client):
    setup_response = anonymous_client.post(
        "/auth/setup",
        data={"username": "first_manager", "password": "SecurePassword123!"},
    )

    assert setup_response.status_code == 302
    assert setup_response.location.endswith("/auth/login?role=management")

    login_page = anonymous_client.get(setup_response.location)
    page = login_page.data.decode()
    assert 'value="management" selected' in page

    login_response = anonymous_client.post(
        "/auth/login",
        data={
            "username": "first_manager",
            "password": "SecurePassword123!",
            "role": "management",
        },
    )

    assert login_response.status_code == 302
    assert login_response.location.endswith("/reports")


def test_login_requires_an_explicit_account_type(anonymous_client):
    page = anonymous_client.get("/auth/login").data.decode()

    assert '-- select account type --' in page
    assert 'value="" disabled selected' in page


def test_database_initialization_adds_account_fields_without_losing_users(tmp_path):
    database_path = tmp_path / "existing.db"
    old_db = sqlite3.connect(database_path)
    old_db.execute(
        """
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK (role IN ('staff', 'recipient', 'management')),
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
        """
    )
    old_db.execute(
        """
        CREATE TABLE donor (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            age INTEGER NOT NULL,
            blood_group TEXT NOT NULL,
            phone TEXT NOT NULL UNIQUE,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
        """
    )
    old_db.execute(
        """
        CREATE TABLE blood_stock (
            blood_group TEXT PRIMARY KEY,
            quantity_ml INTEGER NOT NULL DEFAULT 0,
            updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
        """
    )
    old_db.execute(
        "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
        ("existing_staff", generate_password_hash("ExistingPassword123!"), "staff"),
    )
    old_db.execute(
        "INSERT INTO donor (name, age, blood_group, phone) VALUES (?, ?, ?, ?)",
        ("Existing donor", 28, "O+", "9123456789"),
    )
    old_db.execute(
        "INSERT INTO blood_stock (blood_group, quantity_ml) VALUES (?, ?)",
        ("O+", 750),
    )
    old_db.commit()
    old_db.close()

    init_db(database_path)
    init_db(database_path)
    upgraded_db = connect(database_path)
    try:
        user = upgraded_db.execute(
            "SELECT username, role, disabled, must_change_password FROM users"
        ).fetchone()
        donor = upgraded_db.execute(
            "SELECT name FROM donor WHERE phone = ?",
            ("9123456789",),
        ).fetchone()
        stock = upgraded_db.execute(
            "SELECT quantity_ml FROM blood_stock WHERE blood_group = ?",
            ("O+",),
        ).fetchone()
        columns = {
            row["name"] for row in upgraded_db.execute("PRAGMA table_info(users)")
        }
        versions = [
            row["version"]
            for row in upgraded_db.execute(
                "SELECT version FROM schema_migrations ORDER BY version"
            )
        ]
    finally:
        upgraded_db.close()

    assert user["username"] == "existing_staff"
    assert user["role"] == "staff"
    assert user["disabled"] == 0
    assert user["must_change_password"] == 0
    assert donor["name"] == "Existing donor"
    assert stock["quantity_ml"] == 750
    assert {"disabled", "must_change_password"}.issubset(columns)
    assert versions == [1, 2, 3, 4]
    assert {"email", "email_verified"}.issubset(columns)


def test_user_signup_creates_account_and_allows_login(anonymous_client, db):
    response = anonymous_client.post(
        "/auth/signup",
        data={
            "signup_username": "hospital_user",
            "password": "Passw0rd",
            "confirmation": "Passw0rd",
        },
    )

    assert response.status_code == 302
    assert response.location.endswith("/auth/login?role=recipient")
    user = db.execute(
        "SELECT role, password_hash FROM users WHERE username = 'hospital_user'"
    ).fetchone()
    assert user["role"] == "recipient"
    assert user["password_hash"] != "Passw0rd"
    assert (
        login(
            anonymous_client,
            "hospital_user",
            "recipient",
            "Passw0rd",
        ).status_code
        == 302
    )


def test_signup_rejects_password_mismatch_without_creating_account(
    anonymous_client, db
):
    response = anonymous_client.post(
        "/auth/signup",
        data={
            "signup_username": "hospital_user",
            "password": "Passw0rd",
            "confirmation": "Different8",
        },
    )

    assert response.status_code == 400
    assert b"Passwords do not match." in response.data
    assert db.execute(
        "SELECT 1 FROM users WHERE username = 'hospital_user'"
    ).fetchone() is None


def test_signup_rejects_short_password(anonymous_client, db):
    response = anonymous_client.post(
        "/auth/signup",
        data={
            "signup_username": "hospital_user",
            "password": "short",
            "confirmation": "short",
        },
    )

    assert response.status_code == 400
    assert b"Password must be at least 8 characters." in response.data
    assert db.execute(
        "SELECT 1 FROM users WHERE username = 'hospital_user'"
    ).fetchone() is None


def test_signup_rejects_duplicate_username(anonymous_client, db):
    create_account(db, "hospital_user", "staff")

    response = anonymous_client.post(
        "/auth/signup",
        data={
            "signup_username": "hospital_user",
            "password": "Passw0rd",
            "confirmation": "Passw0rd",
        },
    )

    assert response.status_code == 400
    assert b"That username is already in use." in response.data


def test_temporary_password_requires_change_before_using_other_pages(app, db):
    create_account(db, "manager_account", "management")
    manager = app.test_client()
    login(manager, "manager_account", "management")
    create_response = manager.post(
        "/users/create",
        data={"username": "temporary_staff", "role": "staff"},
        follow_redirects=True,
    )
    match = re.search(
        rb"Temporary password for temporary_staff: ([A-Za-z0-9_-]+)",
        create_response.data,
    )

    assert create_response.status_code == 200
    assert match is not None
    temporary_password = match.group(1).decode()

    new_user = app.test_client()
    login_response = login(new_user, "temporary_staff", "staff", temporary_password)
    assert login_response.location.endswith("/auth/change-password")
    assert new_user.get("/").location.endswith("/auth/change-password")
    change_response = new_user.post(
        "/auth/change-password",
        data={
            "password": "NewPermanentPassword123!",
            "confirmation": "NewPermanentPassword123!",
        },
    )
    assert change_response.location.endswith("/")
    assert new_user.get("/").status_code == 200

def test_last_active_management_account_cannot_be_disabled(app, db):
    manager_id = create_account(db, "manager_account", "management")
    manager = app.test_client()
    login(manager, "manager_account", "management")

    response = manager.post(
        f"/users/{manager_id}/set-disabled",
        data={"disabled": "1"},
        follow_redirects=True,
    )

    assert b"last active management account cannot be disabled" in response.data
    manager_row = db.execute(
        "SELECT disabled FROM users WHERE id = ?", (manager_id,)
    ).fetchone()
    assert manager_row["disabled"] == 0


def test_reset_password_requires_a_change_and_rejects_old_password(app, db):
    create_account(db, "manager_account", "management")
    target_id = create_account(db, "target_staff", "staff")
    manager = app.test_client()
    login(manager, "manager_account", "management")
    reset_response = manager.post(
        f"/users/{target_id}/reset-password",
        follow_redirects=True,
    )
    match = re.search(
        rb"Temporary password for target_staff: ([A-Za-z0-9_-]+)",
        reset_response.data,
    )

    assert match is not None
    temporary_password = match.group(1).decode()
    user = app.test_client()
    assert login(user, "target_staff", "staff").status_code == 401
    response = login(user, "target_staff", "staff", temporary_password)
    assert response.location.endswith("/auth/change-password")
    assert db.execute(
        "SELECT must_change_password FROM users WHERE id = ?", (target_id,)
    ).fetchone()["must_change_password"] == 1


def test_role_change_or_disabling_ends_existing_session(app, db):
    session_client = app.test_client()
    login(session_client, TEST_USERNAME, "staff", TEST_PASSWORD)

    db.execute(
        "UPDATE users SET role = 'recipient' WHERE username = ?",
        (TEST_USERNAME,),
    )
    response = session_client.get("/availability")
    assert response.status_code == 302
    assert response.location.endswith("/auth/login")

    login(session_client, TEST_USERNAME, "recipient", TEST_PASSWORD)
    db.execute(
        "UPDATE users SET disabled = 1 WHERE username = ?",
        (TEST_USERNAME,),
    )
    response = session_client.get("/availability")
    assert response.status_code == 302
    assert response.location.endswith("/auth/login")
