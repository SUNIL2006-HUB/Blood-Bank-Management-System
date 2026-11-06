from flask import Blueprint, render_template, request, session

from ..db import get_db
from ..errors import ValidationError
from ..repositories import audit_repository
from ..services import report_service
from .auth import roles_required

bp = Blueprint("reports", __name__, url_prefix="/reports")


@bp.route("", methods=("GET", "POST"))
@roles_required("management")
def generate():
    report_type = (request.values.get("report_type") or "donation").strip()
    start_date = (request.values.get("start_date") or "").strip()
    end_date = (request.values.get("end_date") or "").strip()
    errors, report = {}, None
    if report_type not in {"donation", "availability"}:
        errors["report_type"] = "Choose a valid report type"
    elif request.method == "POST":
        try:
            report = (
                report_service.donation_report(get_db(), request.form)
                if report_type == "donation"
                else report_service.availability_report(get_db())
            )
        except ValidationError as exc:
            errors = exc.errors
        else:
            audit_repository.record(
                get_db(),
                "report.generated",
                session["username"],
                user_id=session["user_id"],
                target_type="report",
                target_id=None,
            )
    return render_template(
        "reports/generate.html",
        report_type=report_type,
        start_date=start_date,
        end_date=end_date,
        errors=errors,
        report=report,
    ), (400 if errors else 200)
