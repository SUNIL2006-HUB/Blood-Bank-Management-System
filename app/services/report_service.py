from datetime import date

from ..errors import ValidationError
from ..repositories import report_repository
from .availability_service import get_availability


def _date(value, field):
    value = (value or "").strip()
    if not value:
        return None
    try:
        return date.fromisoformat(value).isoformat()
    except ValueError:
        raise ValidationError({field: "Enter a valid date"}) from None


def donation_report(db, form):
    start_date = _date(form.get("start_date"), "start_date")
    end_date = _date(form.get("end_date"), "end_date")
    if start_date and end_date and start_date > end_date:
        raise ValidationError({"end_date": "End date must be on or after start date"})
    rows = report_repository.donation_rows(db, start_date, end_date)
    return {
        "rows": rows,
        "count": len(rows),
        "quantity_ml": sum(row["quantity_ml"] for row in rows),
    }


def availability_report(db):
    return get_availability(db)
