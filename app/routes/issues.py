from flask import Blueprint, flash, redirect, render_template, request, url_for

from ..constants import BLOOD_GROUPS
from ..db import get_db
from ..errors import ServiceError, ValidationError
from ..services import issue_service
from .auth import roles_required

bp = Blueprint("issues", __name__, url_prefix="/issues")


@bp.get("")
@roles_required("staff", "management")
def list_issues():
    return render_template(
        "issues/list.html",
        issues=issue_service.list_recent(get_db()),
    )


@bp.route("/new", methods=("GET", "POST"))
@roles_required("staff", "management")
def issue():
    form, errors = {}, {}

    if request.method == "POST":
        form = request.form

        try:
            result = issue_service.issue_blood(get_db(), form)
        except ValidationError as e:
            errors = e.errors
        except ServiceError as e:
            flash(str(e), "error")
        else:
            flash(
                f"Blood issued: {result['quantity_ml']} ml of "
                f"{result['blood_group']}. "
                f"Remaining stock {result['remaining_ml']} ml.",
                "success",
            )
            return redirect(url_for("issues.list_issues"))

    return render_template(
        "issues/issue.html",
        form=form,
        errors=errors,
        blood_groups=BLOOD_GROUPS,
    ), (400 if errors else 200)