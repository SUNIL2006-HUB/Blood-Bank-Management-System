from datetime import date, timedelta

from werkzeug.security import generate_password_hash


def create_manager(app, db):
    db.execute(
        "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
        ("report_manager", generate_password_hash("ReportManager123!"), "management"),
    )
    manager = app.test_client()
    response = manager.post(
        "/auth/login",
        data={
            "username": "report_manager",
            "password": "ReportManager123!",
            "role": "management",
        },
    )
    assert response.status_code == 302
    return manager


def create_activity(staff, db, donation_date=None):
    phone = "9123456780"
    donor_response = staff.post(
        "/donors/register",
        data={
            "name": "Report Donor",
            "age": "30",
            "blood_group": "O+",
            "phone": phone,
        },
    )
    assert donor_response.status_code == 302
    donor_id = db.execute(
        "SELECT id FROM donor WHERE phone = ?",
        (phone,),
    ).fetchone()["id"]
    donation_response = staff.post(
        "/donations/new",
        data={
            "donor_id": str(donor_id),
            "blood_group": "O+",
            "quantity_ml": "100",
            "donation_date": donation_date or date.today().isoformat(),
        },
    )
    assert donation_response.status_code == 302
    issue_response = staff.post(
        "/issues/new",
        data={"blood_group": "O+", "quantity_ml": "40"},
    )
    assert issue_response.status_code == 302


def test_issue_and_combined_reports_include_issued_transaction(app, client, db):
    create_activity(client, db)
    manager = create_manager(app, db)

    donation_response = manager.post(
        "/reports",
        data={"report_type": "donation"},
    )
    assert donation_response.status_code == 200
    assert b"Donation report" in donation_response.data
    assert b"<td>100</td>" in donation_response.data

    issue_response = manager.post("/reports", data={"report_type": "issue"})
    assert issue_response.status_code == 200
    assert b"Issue report" in issue_response.data
    assert b"<td>40</td>" in issue_response.data

    combined_response = manager.post(
        "/reports",
        data={"report_type": "combined"},
    )
    assert combined_response.status_code == 200
    assert b"Combined activity report" in combined_response.data
    assert b"Donations" in combined_response.data
    assert b"Issues" in combined_response.data
    assert b"2 transactions" in combined_response.data
    assert b"140 ml total activity" in combined_response.data
    assert b"9123456780" not in combined_response.data


def test_donation_report_filters_inclusive_date_range(app, client, db):
    target_date = date.today() - timedelta(days=1)
    create_activity(client, db, donation_date=target_date.isoformat())
    manager = create_manager(app, db)

    response = manager.post(
        "/reports",
        data={
            "report_type": "donation",
            "start_date": target_date.isoformat(),
            "end_date": date.today().isoformat(),
        },
    )

    assert response.status_code == 200
    assert b"Donation report" in response.data
    assert b"1 donation" in response.data
    assert b"<td>100</td>" in response.data


def test_issue_report_filters_by_inclusive_date_range(app, client, db):
    create_activity(client, db)
    manager = create_manager(app, db)
    today = date.today()

    response = manager.post(
        "/reports",
        data={
            "report_type": "issue",
            "start_date": (today - timedelta(days=1)).isoformat(),
            "end_date": (today + timedelta(days=1)).isoformat(),
        },
    )

    assert response.status_code == 200
    assert b"Issue report" in response.data
    assert b"<td>40</td>" in response.data


def test_availability_report_shows_current_stock_snapshot(app, client, db):
    create_activity(client, db)
    manager = create_manager(app, db)

    response = manager.post("/reports", data={"report_type": "availability"})

    assert response.status_code == 200
    assert b"Current availability report" in response.data
    assert b"<td>O+</td><td>60</td>" in response.data


def test_equal_or_reversed_date_ranges_show_required_message(app, db):
    manager = create_manager(app, db)
    for start_date, end_date in (
        ("2026-01-10", "2026-01-10"),
        ("2026-01-11", "2026-01-10"),
    ):
        response = manager.post(
            "/reports",
            data={
                "report_type": "combined",
                "start_date": start_date,
                "end_date": end_date,
            },
        )
        assert response.status_code == 400
        assert (
            b"Invalid date range: &#39;From&#39; date must be before &#39;To&#39; date"
            in response.data
        )


def test_empty_donation_issue_and_combined_reports_show_required_message(app, db):
    manager = create_manager(app, db)

    for report_type in ("donation", "issue", "combined"):
        response = manager.post("/reports", data={"report_type": report_type})
        assert response.status_code == 200
        assert b"No records found for the selected period" in response.data


def test_report_type_is_restricted_to_valid_options(app, db):
    manager = create_manager(app, db)

    response = manager.post("/reports", data={"report_type": "users"})

    assert response.status_code == 400
    assert b"Choose a valid report type" in response.data


def test_only_management_can_generate_reports(app, client):
    response = client.post("/reports", data={"report_type": "combined"})

    assert response.status_code == 403


def test_recipient_cannot_generate_reports(app, db):
    db.execute(
        "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
        ("report_recipient", generate_password_hash("RecipientPassword123!"), "recipient"),
    )
    recipient = app.test_client()
    recipient.post(
        "/auth/login",
        data={
            "username": "report_recipient",
            "password": "RecipientPassword123!",
            "role": "recipient",
        },
    )

    response = recipient.post("/reports", data={"report_type": "combined"})

    assert response.status_code == 403


def test_csv_download_exports_selected_activity_without_contact_details(
    app, client, db
):
    create_activity(client, db)
    manager = create_manager(app, db)

    issue_csv = manager.post(
        "/reports",
        data={"report_type": "issue", "format": "csv"},
    )
    assert issue_csv.status_code == 200
    assert issue_csv.mimetype == "text/csv"
    assert "attachment;" in issue_csv.headers["Content-Disposition"]
    assert b"id,date,blood_group,quantity_ml" in issue_csv.data
    assert b"O+,40" in issue_csv.data
    assert b"9123456780" not in issue_csv.data

    combined_csv = manager.post(
        "/reports",
        data={"report_type": "combined", "format": "csv"},
    )
    assert combined_csv.status_code == 200
    assert b"donation," in combined_csv.data
    assert b"issue," in combined_csv.data
    assert b"9123456780" not in combined_csv.data

    donation_csv = manager.post(
        "/reports",
        data={"report_type": "donation", "format": "csv"},
    )
    assert donation_csv.status_code == 200
    assert b"id,date,blood_group,quantity_ml" in donation_csv.data
    assert b"9123456780" not in donation_csv.data

    availability_csv = manager.post(
        "/reports",
        data={"report_type": "availability", "format": "csv"},
    )
    assert availability_csv.status_code == 200
    assert b"blood_group,available_ml" in availability_csv.data


def test_csv_download_rejects_invalid_date_range(app, db):
    manager = create_manager(app, db)

    response = manager.post(
        "/reports",
        data={
            "report_type": "combined",
            "start_date": "2026-01-10",
            "end_date": "2026-01-10",
            "format": "csv",
        },
    )

    assert response.status_code == 400
    assert response.mimetype == "text/html"
    assert b"Invalid date range" in response.data
