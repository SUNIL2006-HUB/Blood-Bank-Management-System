import sqlite3
from datetime import date

from ..constants import BLOOD_GROUPS, MAX_DONATION_ML
from ..db import transaction
from ..errors import ServiceError, ValidationError
from ..repositories import donation_repository, donor_repository, stock_repository


def _validate(db, form):
    errors, donor = {}, None

    raw_id = (form.get("donor_id") or "").strip()
    if not raw_id.isdigit():
        errors["donor_id"] = "Donor not found"
    else:
        donor = donor_repository.get(db, int(raw_id))
        if donor is None:
            errors["donor_id"] = "Donor not found"

    blood_group = (form.get("blood_group") or "").strip()
    if blood_group not in BLOOD_GROUPS:
        errors["blood_group"] = "Invalid blood group selected"
    elif donor is not None and donor["blood_group"] != blood_group:
        errors["blood_group"] = (
            f"Blood group does not match the donor's registered group ({donor['blood_group']})"
        )

    quantity = None
    try:
        quantity = int((form.get("quantity_ml") or "").strip())
        if quantity <= 0:
            errors["quantity_ml"] = "Quantity must be greater than zero"
        elif quantity > MAX_DONATION_ML:
            errors["quantity_ml"] = "Quantity exceeds maximum permissible donation limit"
    except ValueError:
        errors["quantity_ml"] = "Quantity must be greater than zero"

    donation_date = (form.get("donation_date") or "").strip() or date.today().isoformat()
    try:
        parsed = date.fromisoformat(donation_date)
        if parsed > date.today():
            errors["donation_date"] = "Donation date cannot be in the future"
    except ValueError:
        errors["donation_date"] = "Enter a valid donation date"

    if errors:
        raise ValidationError(errors)
    return donor, blood_group, quantity, donation_date


def record_donation(db, form):
    """UC2: save the donation and (UC3, «include») increase stock - atomically (SEC-08)."""
    donor, blood_group, quantity, donation_date = _validate(db, form)
    try:
        with transaction(db):
            donation_id = donation_repository.create(
                db, donor["id"], blood_group, quantity, donation_date
            )
            new_stock = stock_repository.add(db, blood_group, quantity)
    except sqlite3.Error:
        raise ServiceError("Could not record the donation. Please try again.") from None
    return {"id": donation_id, "blood_group": blood_group, "quantity_ml": quantity,
            "new_stock_ml": new_stock}


def list_recent(db):
    return donation_repository.list_recent(db)
