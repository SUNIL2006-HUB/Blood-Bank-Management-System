import pytest

from app.errors import ValidationError
from app.services import donation_service, donor_service, issue_service


def donor_form(**changes):
    form = {"name": "Asha", "age": "30", "blood_group": "O+", "phone": "9876543210"}
    form.update(changes)
    return form


@pytest.mark.parametrize("phone", ["", "12345", "98765432101", "98765abcde", "\u0669" * 10])
def test_phone_must_be_10_ascii_digits(db, phone):
    with pytest.raises(ValidationError) as e:
        donor_service.register_donor(db, donor_form(phone=phone))
    assert "phone" in e.value.errors


@pytest.mark.parametrize("field", ["name", "age", "blood_group", "phone"])
def test_required_donor_fields_cannot_be_blank(db, field):
    with pytest.raises(ValidationError) as e:
        donor_service.register_donor(db, donor_form(**{field: ""}))
    assert field in e.value.errors


@pytest.mark.parametrize("age", ["0", "-5", "abc"])
def test_donor_age_must_be_positive_number(db, age):
    with pytest.raises(ValidationError) as e:
        donor_service.register_donor(db, donor_form(age=age))
    assert "age" in e.value.errors


def test_invalid_donor_is_not_saved(db):
    with pytest.raises(ValidationError):
        donor_service.register_donor(db, donor_form(phone="123"))
    assert len(donor_service.list_donors(db)) == 0


def test_donor_id_with_odd_characters_is_rejected_not_crashed(db):
    form = {"donor_id": "\u00b2", "blood_group": "O+", "quantity_ml": "100"}
    with pytest.raises(ValidationError) as e:
        donation_service.record_donation(db, form)
    assert "donor_id" in e.value.errors


def test_donation_date_cannot_be_in_the_future(db):
    from datetime import date, timedelta

    donor = donor_service.register_donor(db, donor_form())
    form = {
        "donor_id": str(donor["id"]),
        "blood_group": "O+",
        "quantity_ml": "100",
        "donation_date": (date.today() + timedelta(days=1)).isoformat(),
    }
    with pytest.raises(ValidationError) as e:
        donation_service.record_donation(db, form)
    assert "donation_date" in e.value.errors


@pytest.mark.parametrize("qty", ["0", "-1", "abc", ""])
def test_issue_quantity_must_be_greater_than_zero(db, qty):
    with pytest.raises(ValidationError) as e:
        issue_service.issue_blood(db, {"blood_group": "O+", "quantity_ml": qty})
    assert "quantity_ml" in e.value.errors