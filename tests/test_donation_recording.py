"""PBI-02 / UC2 + UC3 / FR-01, FR-04 - maps to Test Plan UT_01-UT_05, IT_01-IT_03, ST_01."""
from datetime import date, timedelta

import pytest

from app.repositories import stock_repository


@pytest.fixture
def donor_id(client, db, valid_donor):
    client.post("/donors/register", data=valid_donor)
    return db.execute("SELECT id FROM donor").fetchone()[0]


def donate(client, donor_id, **kw):
    data = {"donor_id": str(donor_id), "blood_group": "O+", "quantity_ml": "350",
            "donation_date": date.today().isoformat()}
    data.update(kw)
    return client.post("/donations/new", data=data)


def stock(db, group):
    row = stock_repository.get(db, group)
    return row["quantity_ml"] if row else None


def rows(db, table):
    return db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]


def test_ut01_valid_donation_recorded(client, db, donor_id):
    r = donate(client, donor_id)
    assert r.status_code == 302
    assert rows(db, "donation") == 1


def test_confirmation_message_shown(client, donor_id):
    r = donate(client, donor_id)
    page = client.get(r.headers["Location"]).data
    assert b"Donation recorded: 350 ml of O+" in page


def test_ut02_unknown_donor(client, db):
    r = donate(client, 9999)
    assert r.status_code == 400 and b"Donor not found" in r.data
    assert rows(db, "donation") == 0


def test_unknown_donor_offers_registration_link(client):
    r = donate(client, 9999)
    assert b"Donor not found" in r.data and b'href="/donors/register"' in r.data


@pytest.mark.parametrize(
    "change,message",
    [
        ({"quantity_ml": "0"}, "Quantity must be greater than zero"),
        ({"quantity_ml": "-10"}, "Quantity must be greater than zero"),
        ({"quantity_ml": "600"}, "Quantity exceeds maximum permissible donation limit"),
        ({"donation_date": (date.today() + timedelta(days=1)).isoformat()},
         "Donation date cannot be in the future"),
        ({"blood_group": "A+"}, "does not match the donor"),
        ({"blood_group": "XZ"}, "Invalid blood group selected"),
    ],
)
def test_invalid_input_rejected_and_stock_untouched(client, db, donor_id, change, message):
    r = donate(client, donor_id, **change)
    assert r.status_code == 400 and message.encode() in r.data
    assert rows(db, "donation") == 0 and stock(db, "O+") is None


def test_it01_stock_increases_by_donated_quantity(client, db, donor_id):
    donate(client, donor_id)
    donate(client, donor_id, quantity_ml="200")
    assert stock(db, "O+") == 550


def test_it02_new_stock_record_created_for_new_group(client, db, valid_donor):
    client.post("/donors/register", data={**valid_donor, "blood_group": "AB-", "phone": "9000000001"})
    did = db.execute("SELECT id FROM donor").fetchone()[0]
    assert stock(db, "AB-") is None
    donate(client, did, blood_group="AB-")
    assert stock(db, "AB-") == 350


def test_it03_save_failure_rolls_back_donation_and_stock(client, db, donor_id, monkeypatch):
    import sqlite3

    from app.repositories import stock_repository as sr

    def boom(*a, **k):
        raise sqlite3.OperationalError("disk full")

    monkeypatch.setattr(sr, "add", boom)
    r = donate(client, donor_id)
    assert b"Could not record the donation" in r.data and b"disk full" not in r.data
    assert rows(db, "donation") == 0 and stock(db, "O+") is None


def test_st01_register_donate_then_stock_visible(client, db, donor_id):
    donate(client, donor_id)
    assert stock(db, "O+") == 350
    assert b"350" in client.get("/donations").data
