"""PBI-05 / UC6 / FR-08 - report access, filtering and empty results."""

from datetime import date


def management_login(client, username="manager", password="test-password"):
    client.application.config.update(
        MANAGEMENT_USERNAME="manager",
        MANAGEMENT_PASSWORD="test-password",
    )
    return client.post("/reports/login", data={"username": username, "password": password})


def record_donation(client, db, *, donation_date, phone, quantity="350", group="O+"):
    response = client.post(
        "/donors/register",
        data={"name": "Report Donor", "age": "30", "blood_group": group, "phone": phone},
    )
    assert response.status_code == 302
    donor_id = db.execute("SELECT id FROM donor WHERE phone = ?", (phone,)).fetchone()["id"]
    return client.post(
        "/donations/new",
        data={
            "donor_id": str(donor_id),
            "blood_group": group,
            "quantity_ml": quantity,
            "donation_date": donation_date,
        },
    )


def test_report_requires_management_login(client):
    response = client.get("/reports")
    assert response.status_code == 403
    assert b"Access denied" in response.data


def test_management_login_rejects_invalid_credentials(client):
    response = management_login(client, password="wrong-password")
    assert response.status_code == 200
    assert b"Invalid management credentials" in response.data
    assert client.get("/reports").status_code == 403


def test_management_login_allows_report_access(client):
    response = management_login(client)
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/reports")
    assert client.get("/reports").status_code == 200


def test_donation_report_filters_inclusive_date_range(client, db):
    management_login(client)
    record_donation(client, db, donation_date="2025-01-01", phone="9000000001")
    record_donation(client, db, donation_date="2025-01-02", phone="9000000002", quantity="200")
    record_donation(client, db, donation_date="2025-01-03", phone="9000000003", quantity="100")

    response = client.post(
        "/reports",
        data={"report_type": "donation", "start_date": "2025-01-02", "end_date": "2025-01-02"},
    )
    assert response.status_code == 200
    assert b"1 donation" in response.data
    assert b"200 ml total" in response.data
    assert b"2025-01-02" in response.data
    assert b"2025-01-01" not in response.data and b"2025-01-03" not in response.data


def test_donation_report_blank_dates_includes_all_records(client, db):
    management_login(client)
    record_donation(client, db, donation_date="2025-01-01", phone="9000000004")
    record_donation(client, db, donation_date="2025-01-02", phone="9000000005", quantity="200")

    response = client.post("/reports", data={"report_type": "donation"})
    assert response.status_code == 200
    assert b"2 donations" in response.data
    assert b"550 ml total" in response.data


def test_donation_report_shows_empty_message_when_no_records_match(client):
    management_login(client)
    response = client.post(
        "/reports",
        data={"report_type": "donation", "start_date": "2025-01-01", "end_date": "2025-01-31"},
    )
    assert response.status_code == 200
    assert b"No donations match the selected date range" in response.data


def test_donation_report_rejects_invalid_or_reversed_dates(client):
    management_login(client)
    invalid = client.post(
        "/reports", data={"report_type": "donation", "start_date": "not-a-date"}
    )
    reversed_range = client.post(
        "/reports",
        data={"report_type": "donation", "start_date": "2025-02-01", "end_date": "2025-01-01"},
    )
    assert invalid.status_code == 400 and b"Enter a valid date" in invalid.data
    assert reversed_range.status_code == 400 and b"End date must be on or after start date" in reversed_range.data


def test_availability_report_shows_current_stock_snapshot(client, db):
    management_login(client)
    record_donation(client, db, donation_date=date.today().isoformat(), phone="9000000006")

    response = client.post("/reports", data={"report_type": "availability"})
    assert response.status_code == 200
    assert b"Current availability report" in response.data
    assert b"<td>O+</td><td>350</td>" in response.data
    assert b"<td>A+</td><td>0</td>" in response.data
