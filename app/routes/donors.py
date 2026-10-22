from flask import Blueprint, flash, redirect, render_template, request, url_for

from ..constants import BLOOD_GROUPS
from ..db import get_db
from ..errors import ServiceError, ValidationError
from ..services import donor_service

bp = Blueprint("donors", __name__, url_prefix="/donors")


@bp.get("")
def list_donors():
    return render_template("donors/list.html", donors=donor_service.list_donors(get_db()))


@bp.route("/register", methods=("GET", "POST"))
def register():
    form, errors = {}, {}
    if request.method == "POST":
        form = request.form
        try:
            donor = donor_service.register_donor(get_db(), form)
        except ValidationError as e:
            errors = e.errors
        except ServiceError as e:
            flash(str(e), "error")
        else:
            flash(f"Donor registered successfully (ID {donor['id']})", "success")
            return redirect(url_for("donors.list_donors"))
    status = 400 if errors else 200
    return render_template(
        "donors/register.html", form=form, errors=errors, blood_groups=BLOOD_GROUPS
    ), status
