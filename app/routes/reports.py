from functools import wraps
from hmac import compare_digest

from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from ..db import get_db
from ..errors import ValidationError
from ..services import report_service

bp = Blueprint("reports", __name__, url_prefix="/reports")


def management_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if session.get("role") != "management":
            abort(403)
        return view(*args, **kwargs)

    return wrapped


@bp.route("/login", methods=("GET", "POST"))
def login():
    form = request.form if request.method == "POST" else {}
    if request.method == "POST":
        username = current_app.config.get("MANAGEMENT_USERNAME")
        password = current_app.config.get("MANAGEMENT_PASSWORD")
        supplied_username = form.get("username", "")
        supplied_password = form.get("password", "")
        if (
            username
            and password
            and compare_digest(supplied_username, username)
            and compare_digest(supplied_password, password)
        ):
            session.clear()
            session["role"] = "management"
            flash("Signed in as blood bank management.", "success")
            return redirect(url_for("reports.generate"))
        flash("Invalid management credentials or management sign-in is not configured.", "error")
    return render_template("reports/login.html", form=form)


@bp.post("/logout")
def logout():
    session.clear()
    flash("You have been signed out.", "success")
    return redirect(url_for("index"))


@bp.route("", methods=("GET", "POST"))
@management_required
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
    return render_template(
        "reports/generate.html",
        report_type=report_type,
        start_date=start_date,
        end_date=end_date,
        errors=errors,
        report=report,
    ), (400 if errors else 200)
