"""PBI-04 / UC5 + UC3 / FR-07 - maps to Test Plan UT_01-UT_04, IT_01-IT_03."""
import sqlite3
from datetime import date

import pytest

from app.repositories import stock_repository


def seed(client, db, group="O+", qty="350", phone="9876543210"):
    client.post("/donors/register", data={"name": "D", "age": "30", "blood_group": group, "phone": phone})
    did = db.execute("SELECT id FROM donor WHERE phone = ?", (phone,)).fetchone()[0]
    client.post("/donations/new", data={"donor_id": did, "blood_group": group,
                                        "quantity_ml": qty, "donation_date": date.today().isoformat()})


def issue(client, group="O+", qty="350", **kw):
    return client.post("/issues/new", data={"blood_group": group, "quantity_ml": qty, **kw})


def stock(db, group):
    row = stock_repository.get(db, group)
    return row["quantity_ml"] if row else None


def issues(db):
    return db.execute("SELECT COUNT(*) FROM blood_issue").fetchone()[0]


def test_ut01_issue_with_sufficient_stock(client, db):
    seed(client, db, qty="500")
    r = issue(client, qty="350")
    assert r.status_code == 302
    assert b"Blood issued: 350 ml of O+" in client.get(r.headers["Location"]).data
    assert issues(db) == 1


def test_ut02_insufficient_stock_cancels_issue(client, db):
    seed(client, db, "AB-", "200", "9000000001")
    r = issue(client, "AB-", "500")
    assert r.status_code == 400 and b"Insufficient stock available" in r.data
    assert issues(db) == 0 and stock(db, "AB-") == 200


def test_ut03_zero_or_negative_quantity(client, db):
    seed(client, db)
    for q in ("0", "-5", "abc"):
        r = issue(client, qty=q)
        assert r.status_code == 400 and b"Quantity must be greater than zero" in r.data
    assert issues(db) == 0 and stock(db, "O+") == 350


def test_ut04_no_stock_record(client, db):
    r = issue(client, "AB+", "100")
    assert r.status_code == 400 and b"No stock record found for this blood group" in r.data
    assert issues(db) == 0


def test_invalid_blood_group(client):
    r = issue(client, "XZ")
    assert r.status_code == 400 and b"Invalid blood group selected" in r.data


def test_it01_stock_decreases_by_issued_quantity(client, db):
    seed(client, db, qty="500")
    seed(client, db, qty="500", phone="9876543211")  # 1000 ml
    issue(client, qty="350")
    assert stock(db, "O+") == 650


def test_it02_issue_exact_stock_leaves_zero_and_search_shows_no_stock(client, db):
    seed(client, db, "AB-", "200", "9000000001")
    assert issue(client, "AB-", "200").status_code == 302
    assert stock(db, "AB-") == 0
    assert b"No stock available for AB-" in client.get("/availability?blood_group=AB-").data


def test_it03_save_failure_leaves_stock_unchanged(client, db, monkeypatch):
    seed(client, db)
    from app.repositories import issue_repository as ir

    def boom(*a, **k):
        raise sqlite3.OperationalError("disk full")

    monkeypatch.setattr(ir, "create", boom)
    r = issue(client)
    assert b"Could not issue the blood" in r.data and b"disk full" not in r.data
    assert issues(db) == 0 and stock(db, "O+") == 350


def test_stock_decrement_failure_rolls_back_issue_record(client, db, monkeypatch):
    seed(client, db)
    from app.repositories import stock_repository as sr

    def boom(*a, **k):
        raise sqlite3.OperationalError("boom")

    monkeypatch.setattr(sr, "remove", boom)
    issue(client)
    assert issues(db) == 0 and stock(db, "O+") == 350


def test_recipient_is_recorded_and_issue_reflected_in_availability(client, db):
    seed(client, db, qty="500")
    issue(client, qty="100", recipient="City Hospital")
    assert b"City Hospital" in client.get("/issues").data
    assert b"<td>400</td>" in client.get("/availability?blood_group=O%2B").data


def test_stock_can_never_go_negative_at_db_level(db):
    db.execute("INSERT INTO blood_stock (blood_group, quantity_ml) VALUES ('A+', 10)")
    with pytest.raises(sqlite3.IntegrityError):
        db.execute("UPDATE blood_stock SET quantity_ml = quantity_ml - 20 WHERE blood_group='A+'")
