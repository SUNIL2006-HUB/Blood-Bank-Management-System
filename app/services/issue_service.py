import sqlite3

from ..constants import BLOOD_GROUPS
from ..db import transaction
from ..errors import ServiceError, ValidationError
from ..repositories import issue_repository, stock_repository


def _validate(form):
    errors = {}
    blood_group = (form.get("blood_group") or "").strip()
    if blood_group not in BLOOD_GROUPS:
        errors["blood_group"] = "Invalid blood group selected"

    quantity = None
    try:
        quantity = int((form.get("quantity_ml") or "").strip())
        if quantity <= 0:
            errors["quantity_ml"] = "Quantity must be greater than zero"
    except ValueError:
        errors["quantity_ml"] = "Quantity must be greater than zero"

    recipient = (form.get("recipient") or "").strip() or None
    if recipient and len(recipient) > 100:
        errors["recipient"] = "Recipient / hospital must be at most 100 characters"

    if errors:
        raise ValidationError(errors)
    return blood_group, quantity, recipient


def issue_blood(db, form):
    """UC5: check stock, record the issue and (UC3, «include») decrease stock - atomically.

    Stock never goes below zero (SEC-08).
    """
    blood_group, quantity, recipient = _validate(form)
    try:
        with transaction(db):
            if stock_repository.get(db, blood_group) is None:
                raise ValidationError(
                    {"blood_group": "No stock record found for this blood group"}
                )
            issue_id = issue_repository.create(db, blood_group, quantity, recipient)
            remaining = stock_repository.remove(db, blood_group, quantity)
            if remaining is None:
                raise ValidationError({"quantity_ml": "Insufficient stock available"})
    except sqlite3.Error:
        raise ServiceError("Could not issue the blood. Please try again.") from None
    return {"id": issue_id, "blood_group": blood_group, "quantity_ml": quantity,
            "remaining_ml": remaining}


def list_recent(db):
    return issue_repository.list_recent(db)
