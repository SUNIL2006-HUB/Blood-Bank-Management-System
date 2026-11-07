from werkzeug.security import generate_password_hash


def test_management_pages_show_only_the_shared_logout_control(app, db):
    db.execute(
        "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
        ("logout_manager", generate_password_hash("ManagerPassword123!"), "management"),
    )
    manager = app.test_client()
    response = manager.post(
        "/auth/login",
        data={
            "username": "logout_manager",
            "password": "ManagerPassword123!",
            "role": "management",
        },
    )
    assert response.status_code == 302

    for path in ("/reports", "/users"):
        page = manager.get(path)

        assert page.status_code == 200
        assert page.data.count(b">Logout</button>") == 1
        assert b"Sign out" not in page.data
