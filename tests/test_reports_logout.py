from werkzeug.security import generate_password_hash


def test_reports_page_has_one_logout_control(app, db):
    db.execute(
        "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
        ("report_manager", generate_password_hash("ReportManager123!"), "management"),
    )
    manager = app.test_client()
    manager.post(
        "/auth/login",
        data={
            "username": "report_manager",
            "password": "ReportManager123!",
            "role": "management",
        },
    )

    response = manager.get("/reports")

    assert response.status_code == 200
    assert response.data.count(b">Logout</button>") == 1
    assert b"Sign out" not in response.data
