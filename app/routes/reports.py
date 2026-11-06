import csv
from io import StringIO

from flask import Blueprint, Response, render_template, request, session

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
    if report_type not in {"donation", "issue", "combined", "availability"}:
        errors["report_type"] = "Choose a valid report type"
    elif request.method == "POST":
        try:
            report = _generate_report(report_type, request.form)
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
            if request.form.get("format") == "csv":
                return _csv_response(report_type, report)
    return render_template(
        "reports/generate.html",
        report_type=report_type,
        start_date=start_date,
        end_date=end_date,
        errors=errors,
        report=report,
    ), (400 if errors else 200)


def _generate_report(report_type, form):
    db = get_db()
    if report_type == "donation":
        return report_service.donation_report(db, form)
    if report_type == "issue":
        return report_service.issue_report(db, form)
    if report_type == "combined":
        return report_service.combined_report(db, form)
    return report_service.availability_report(db)


def _csv_response(report_type, report):
    output = StringIO(newline="")
    writer = csv.writer(output)
    if report_type == "availability":
        writer.writerow(("blood_group", "available_ml"))
        writer.writerows(
            (row["blood_group"], row["quantity_ml"]) for row in report
        )
    elif report_type == "combined":
        writer.writerow(("activity", "id", "date", "blood_group", "quantity_ml"))
        writer.writerows(
            ("donation", row["id"], row["donation_date"], row["blood_group"], row["quantity_ml"])
            for row in report["donations"]["rows"]
        )
        writer.writerows(
            ("issue", row["id"], row["issue_date"], row["blood_group"], row["quantity_ml"])
            for row in report["issues"]["rows"]
        )
    else:
        date_key = "donation_date" if report_type == "donation" else "issue_date"
        writer.writerow(("id", "date", "blood_group", "quantity_ml"))
        writer.writerows(
            (row["id"], row[date_key], row["blood_group"], row["quantity_ml"])
            for row in report["rows"]
        )

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={report_type}-report.csv"},
    )
