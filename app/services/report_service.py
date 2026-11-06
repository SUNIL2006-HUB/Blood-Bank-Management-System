import re
from datetime import date

from ..errors import ValidationError
from ..repositories import report_repository
from .availability_service import get_availability


def _date(value, field):
    value = (value or "").strip()
    if not value:
        return None
    try:
        if re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value) is None:
            raise ValueError
        return date.fromisoformat(value).isoformat()
    except ValueError:
        raise ValidationError({field: "Enter a valid date"}) from None


def donation_report(db, form):
    start_date = _date(form.get("start_date"), "start_date")
    end_date = _date(form.get("end_date"), "end_date")
    _validate_date_range(start_date, end_date)
    rows = report_repository.donation_rows(db, start_date, end_date)
    return {
        "rows": rows,
        "count": len(rows),
        "quantity_ml": sum(row["quantity_ml"] for row in rows),
    }


def issue_report(db, form):
    start_date = _date(form.get("start_date"), "start_date")
    end_date = _date(form.get("end_date"), "end_date")
    _validate_date_range(start_date, end_date)
    rows = report_repository.issue_rows(db, start_date, end_date)
    return {
        "rows": rows,
        "count": len(rows),
        "quantity_ml": sum(row["quantity_ml"] for row in rows),
    }


def combined_report(db, form):
    donations = donation_report(db, form)
    issues = issue_report(db, form)
    return {
        "donations": donations,
        "issues": issues,
        "count": donations["count"] + issues["count"],
        "quantity_ml": donations["quantity_ml"] + issues["quantity_ml"],
    }


def availability_report(db):
    return get_availability(db)


def _validate_date_range(start_date, end_date):
    if start_date and end_date and start_date >= end_date:
        raise ValidationError(
            {"end_date": "Invalid date range: 'From' date must be before 'To' date"}
        )
