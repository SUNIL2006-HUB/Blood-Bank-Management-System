import pytest

from app import create_app
from app.db import connect


@pytest.fixture
def app(tmp_path):
    return create_app({"TESTING": True, "DATABASE": str(tmp_path / "test.db")})


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def db(app):
    conn = connect(app.config["DATABASE"])
    yield conn
    conn.close()


VALID_DONOR = {"name": "Ramesh Kumar", "age": "28", "blood_group": "O+", "phone": "9876543210"}


@pytest.fixture
def valid_donor():
    return dict(VALID_DONOR)
