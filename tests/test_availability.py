"""PBI-03 / UC4 / FR-03, FR-05, FR-06 - maps to Test Plan UT_01-UT_04, IT_02, ST_01, ST_02."""
from datetime import date

from app.constants import BLOOD_GROUPS


def seed_donation(client, db, group="O+", qty="350", phone="9876543210"):
    client.post("/donors/register", data={"name": "D", "age": "30", "blood_group": group, "phone": phone})
    did = db.execute("SELECT id FROM donor WHERE phone = ?", (phone,)).fetchone()[0]
    client.post("/donations/new", data={"donor_id": did, "blood_group": group,
                                        "quantity_ml": qty, "donation_date": date.today().isoformat()})


def test_ut01_no_filter_lists_every_group(client):
    page = client.get("/availability").data.decode()
    assert all(f"<td>{g}</td>" in page for g in BLOOD_GROUPS)


def test_ut02_search_valid_group_shows_only_that_group(client, db):
    seed_donation(client, db, "O+", "350")
    page = client.get("/availability?blood_group=O%2B").data.decode()
    assert "<td>O+</td><td>350</td>" in page
    assert "<td>A+</td>" not in page


def test_ut03_zero_stock_message(client):
    page = client.get("/availability?blood_group=AB-").data
    assert b"No stock available for AB-" in page


def test_ut04_invalid_group_rejected(client):
    r = client.get("/availability?blood_group=Z%2B")
    assert r.status_code == 400 and b"Invalid blood group" in r.data


def test_it02_search_reflects_new_donation_immediately(client, db):
    seed_donation(client, db, "O+", "350")
    assert b"<td>350</td>" in client.get("/availability?blood_group=O%2B").data
    seed_donation(client, db, "O+", "100", phone="9876543211")
    assert b"<td>450</td>" in client.get("/availability?blood_group=O%2B").data


def test_st01_concurrent_readers_see_consistent_stock(client, app, db):
    seed_donation(client, db, "B+", "300")
    other = app.test_client()
    a = client.get("/availability?blood_group=B%2B").data
    b = other.get("/availability?blood_group=B%2B").data

    def table(page):
        return page[page.index(b"<table"):page.index(b"</table>")]

    assert table(a) == table(b) and b"<td>300</td>" in a


def test_st02_blank_criteria_returns_full_list(client):
    r = client.get("/availability?blood_group=")
    assert r.status_code == 200 and r.data.count(b"<tr><td>") == len(BLOOD_GROUPS)


def test_search_text_with_sql_is_just_invalid(client, db):
    r = client.get("/availability?blood_group=' OR '1'='1")
    assert r.status_code == 400
