
import pytest
from werkzeug.security import generate_password_hash

from app import create_app
from app.db import connect

TEST_USERNAME = "test_staff"
TEST_PASSWORD = "TestPassword123!"


@pytest.fixture
def app(tmp_path):
    app = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-secret-key",
            "DATABASE": str(tmp_path / "test.db"),
        }
    )

    # Create a staff account for the functional tests.
    with app.app_context():
        db = connect(app.config["DATABASE"])
        try:
            db.execute(
                """
                INSERT INTO users (username, password_hash, role)
                VALUES (?, ?, ?)
                """,
                (
                    TEST_USERNAME,
                    generate_password_hash(TEST_PASSWORD),
                    "staff",
                ),
            )
            db.commit()
        finally:
            db.close()

    return app


@pytest.fixture
def anonymous_client(app):
    """A client that has not logged in."""
    return app.test_client()


@pytest.fixture
def client(app):
    """An authenticated staff client for existing functional tests."""
    test_client = app.test_client()

    response = test_client.post(
        "/auth/login",
        data={
            "username": TEST_USERNAME,
            "password": TEST_PASSWORD,
        },
        follow_redirects=False,
    )

    assert response.status_code == 302, (
        "Test staff login failed. Check the login route and database setup."
    )

    return test_client


@pytest.fixture
def authenticated_client(client):
    """Alias for tests that explicitly request an authenticated client."""
    return client


@pytest.fixture
def db(app):
    conn = connect(app.config["DATABASE"])
    try:
        yield conn
    finally:
        conn.close()


VALID_DONOR = {
    "name": "Ramesh Kumar",
    "age": "28",
    "blood_group": "O+",
    "phone": "9876543210",
}


@pytest.fixture
def valid_donor():
    return dict(VALID_DONOR)
