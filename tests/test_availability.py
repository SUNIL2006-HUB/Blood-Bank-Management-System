
"""PBI-03 / UC4 / FR-03, FR-05, FR-06 - maps to Test Plan UT_01-UT_04, IT_02, ST_01, ST_02."""

from datetime import date

from app.constants import BLOOD_GROUPS


def seed_donation(client, db, group="O+", qty="350", phone="9876543210"):
    client.post(
        "/donors/register",
        data={
            "name": "D",
            "age": "30",
            "blood_group": group,
            "phone": phone,
        },
    )

    donor = db.execute(
        "SELECT id FROM donor WHERE phone = ?", (phone,)
    ).fetchone()

    assert donor is not None, "Test donor registration failed."
    donor_id = donor["id"]

    response = client.post(
        "/donations/new",
        data={
            "donor_id": donor_id,
            "blood_group": group,
            "quantity_ml": qty,
            "donation_date": date.today().isoformat(),
        },
    )

    assert response.status_code == 302, "Test donation recording failed."


def test_ut01_no_filter_lists_every_group(client):
    response = client.get("/availability")
    assert response.status_code == 200

    page = response.data.decode()
    assert all(f"<td>{group}</td>" in page for group in BLOOD_GROUPS)


def test_ut02_search_valid_group_shows_only_that_group(client, db):
    seed_donation(client, db, "O+", "350")

    response = client.get("/availability?blood_group=O%2B")
    assert response.status_code == 200

    page = response.data.decode()
    assert "<td>O+</td><td>350</td>" in page
    assert "<td>A+</td>" not in page


def test_ut03_zero_stock_message(client):
    response = client.get("/availability?blood_group=AB-")

    assert response.status_code == 200
    assert b"No stock available for AB-" in response.data


def test_ut04_invalid_group_rejected(client):
    response = client.get("/availability?blood_group=Z%2B")

    assert response.status_code == 400
    assert b"Invalid blood group" in response.data


def test_it02_search_reflects_new_donation_immediately(client, db):
    seed_donation(client, db, "O+", "350")

    response = client.get("/availability?blood_group=O%2B")
    assert b"<td>350</td>" in response.data

    seed_donation(client, db, "O+", "100", phone="9876543211")

    response = client.get("/availability?blood_group=O%2B")
    assert b"<td>450</td>" in response.data


def test_st01_concurrent_readers_see_consistent_stock(client, app, db):
    seed_donation(client, db, "B+", "300")

    # Authenticate the second client as well.
    other = app.test_client()
    login_response = other.post(
        "/auth/login",
        data={
            "username": "test_staff",
            "password": "TestPassword123!",
        },
        follow_redirects=False,
    )

    assert login_response.status_code == 302

    first_response = client.get("/availability?blood_group=B%2B")
    second_response = other.get("/availability?blood_group=B%2B")

    # Fail with a clear message if either client was redirected to login.
    assert first_response.status_code == 200, first_response.data.decode()
    assert second_response.status_code == 200, second_response.data.decode()

    def table(page):
        start = page.index(b"<table")
        end = page.index(b"</table>") + len(b"</table>")
        return page[start:end]

    first_table = table(first_response.data)
    second_table = table(second_response.data)

    assert first_table == second_table
    assert b"<td>300</td>" in first_table


def test_st02_blank_criteria_returns_full_list(client):
    response = client.get("/availability?blood_group=")

    assert response.status_code == 200
    assert response.data.count(b"<tr><td>") == len(BLOOD_GROUPS)


def test_search_text_with_sql_is_just_invalid(client, db):
    response = client.get(
        "/availability?blood_group=' OR '1'='1"
    )

    assert response.status_code == 400
    assert b"Invalid blood group" in response.data
