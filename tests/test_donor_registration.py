"""PBI-01 / UC1 / FR-02 - maps to Test Plan UT_01-UT_06, IT_01, IT_02."""
import pytest


def post(client, data):
    return client.post("/donors/register", data=data)


def count(db):
    return db.execute("SELECT COUNT(*) FROM donor").fetchone()[0]


def test_ut01_valid_donor_registered(client, db, valid_donor):
    r = post(client, valid_donor)
    assert r.status_code == 302
    assert b"Donor registered successfully" in client.get("/donors").data
    assert count(db) == 1


@pytest.mark.parametrize(
    "change,message",
    [
        ({"name": ""}, "Name is required"),
        ({"blood_group": "XZ"}, "Invalid blood group selected"),
        ({"age": "-5"}, "Age must be a positive number"),
        ({"age": "abc"}, "Age must be a positive number"),
        ({"age": "16"}, "Donor must be at least 18 years old"),
        ({"phone": "12AB"}, "Enter a valid 10-digit phone number"),
    ],
)
def test_invalid_input_rejected_and_not_saved(client, db, valid_donor, change, message):
    r = post(client, {**valid_donor, **change})
    assert r.status_code == 400
    assert message.encode() in r.data
    assert count(db) == 0


def test_it01_registered_donor_is_listed(client, valid_donor):
    post(client, valid_donor)
    page = client.get("/donors").data
    assert b"Ramesh Kumar" in page and b"9876543210" in page


def test_st01_new_donor_is_selectable_for_donation(client, db, valid_donor):
    post(client, valid_donor)
    donor_id = db.execute(
        "SELECT id FROM donor WHERE phone = ?",
        (valid_donor["phone"],),
    ).fetchone()["id"]

    response = client.get("/donations/new")

    assert response.status_code == 200
    assert f'<option value="{donor_id}"'.encode() in response.data
    assert b"Ramesh Kumar (O+)" in response.data


def test_donation_form_has_searchable_donor_selector(client, db, valid_donor):
    post(client, valid_donor)

    response = client.get("/donations/new")

    assert response.status_code == 200
    assert b'id="donor_search" type="search"' in response.data
    assert b"Type a name, donor ID, blood group, or phone number" in response.data
    assert b'data-search="1 Ramesh Kumar O+ 9876543210"' in response.data
    assert b"donorOptions.forEach" in response.data
    assert b"donorSearchStatus.textContent" in response.data


def test_it02_duplicate_phone_rejected(client, db, valid_donor):
    post(client, valid_donor)
    r = post(client, {**valid_donor, "name": "Someone Else"})
    assert r.status_code == 400
    assert b"Donor with this phone number already exists" in r.data
    assert count(db) == 1


def test_sql_injection_text_is_stored_literally(client, db, valid_donor):
    post(client, {**valid_donor, "name": "Robert'); DROP TABLE donor;--"})
    assert count(db) == 1
