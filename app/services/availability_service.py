from ..constants import BLOOD_GROUPS
from ..errors import ValidationError
from ..repositories import stock_repository


def get_availability(db, blood_group=None):
    """UC4: current stock per blood group, optionally filtered (FR-03, FR-05, FR-06).

    Blank criteria returns every group (zero for groups with no stock record).
    """
    blood_group = (blood_group or "").strip()
    if blood_group and blood_group not in BLOOD_GROUPS:
        raise ValidationError({"blood_group": "Invalid blood group"})

    stock = {r["blood_group"]: r["quantity_ml"] for r in stock_repository.list_all(db)}
    groups = [blood_group] if blood_group else BLOOD_GROUPS
    return [{"blood_group": g, "quantity_ml": stock.get(g, 0)} for g in groups]
