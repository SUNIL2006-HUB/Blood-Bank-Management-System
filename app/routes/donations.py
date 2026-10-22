from datetime import date

from flask import Blueprint, flash, redirect, render_template, request, url_for

from ..db import get_db
from ..errors import ServiceError, ValidationError
from ..services import donation_service, donor_service

bp = Blueprint("donations", __name__, url_prefix="/donations")


@bp.get("")
def list_donations():
    return render_template("donations/list.html", donations=donation_service.list_recent(get_db()))


@bp.route("/new", methods=("GET", "POST"))
def record():
    db = get_db()
    form, errors = {}, {}
    if request.method == "POST":
        form = request.form
        try:
            result = donation_service.record_donation(db, form)
        except ValidationError as e:
            errors = e.errors
        except ServiceError as e:
            flash(str(e), "error")
        else:
            flash(
                f"Donation recorded: {result['quantity_ml']} ml of {result['blood_group']}. "
                f"Stock is now {result['new_stock_ml']} ml.",
                "success",
            )
            return redirect(url_for("donations.list_donations"))
    return render_template(
        "donations/record.html",
        form=form,
        errors=errors,
        donors=donor_service.list_donors(db),
        today=date.today().isoformat(),
    ), (400 if errors else 200)
