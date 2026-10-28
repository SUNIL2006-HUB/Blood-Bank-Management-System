import re
import sqlite3

from ..constants import BLOOD_GROUPS, MAX_DONOR_AGE, MIN_DONOR_AGE
from ..errors import ServiceError, ValidationError
from ..repositories import donor_repository

PHONE_RE = re.compile(r"[0-9]{10}")


def validate_donor(form):
    """Server-side validation (SEC-06). Returns (clean_values, errors)."""
    errors = {}
    name = (form.get("name") or "").strip()
    blood_group = (form.get("blood_group") or "").strip()
    phone = (form.get("phone") or "").strip()
    age = None

    if not name:
        errors["name"] = "Name is required"
    elif len(name) > 100:
        errors["name"] = "Name must be at most 100 characters"

    try:
        age = int((form.get("age") or "").strip())
        if age <= 0:
            errors["age"] = "Age must be a positive number"
        elif age < MIN_DONOR_AGE:
            errors["age"] = f"Donor must be at least {MIN_DONOR_AGE} years old"
        elif age > MAX_DONOR_AGE:
            errors["age"] = f"Donor must be at most {MAX_DONOR_AGE} years old"
    except ValueError:
        errors["age"] = "Age must be a positive number"

    if blood_group not in BLOOD_GROUPS:
        errors["blood_group"] = "Invalid blood group selected"

    if not PHONE_RE.fullmatch(phone):
        errors["phone"] = "Enter a valid 10-digit phone number"

    return {"name": name, "age": age, "blood_group": blood_group, "phone": phone}, errors


def register_donor(db, form):
    values, errors = validate_donor(form)
    if errors:
        raise ValidationError(errors)
    if donor_repository.get_by_phone(db, values["phone"]):
        raise ValidationError({"phone": "Donor with this phone number already exists"}) from None
    try:
        donor_id = donor_repository.create(db, **values)
    except sqlite3.IntegrityError:  # race on the UNIQUE phone constraint
        raise ValidationError({"phone": "Donor with this phone number already exists"}) from None
    except sqlite3.Error:
        raise ServiceError("Could not save the donor. Please try again.") from None
    return donor_repository.get(db, donor_id)


def list_donors(db):
    return donor_repository.list_all(db)
