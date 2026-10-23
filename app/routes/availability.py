from flask import Blueprint, render_template, request

from ..constants import BLOOD_GROUPS
from ..db import get_db
from ..errors import ValidationError
from ..services import availability_service

bp = Blueprint("availability", __name__, url_prefix="/availability")


@bp.get("")
def view():
    selected = (request.args.get("blood_group") or "").strip()
    rows, errors = [], {}
    try:
        rows = availability_service.get_availability(get_db(), selected)
    except ValidationError as e:
        errors = e.errors
    no_stock = bool(selected) and not errors and rows and rows[0]["quantity_ml"] == 0
    return render_template(
        "availability/view.html",
        rows=rows,
        errors=errors,
        selected=selected,
        no_stock=no_stock,
        blood_groups=BLOOD_GROUPS,
    ), (400 if errors else 200)
