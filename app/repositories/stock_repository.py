def get(db, blood_group):
    return db.execute(
        "SELECT * FROM blood_stock WHERE blood_group = ?", (blood_group,)
    ).fetchone()


def add(db, blood_group, quantity_ml):
    """Increase stock (creates the record if missing). Returns the new quantity."""
    db.execute(
        """INSERT INTO blood_stock (blood_group, quantity_ml) VALUES (?, ?)
           ON CONFLICT(blood_group) DO UPDATE
           SET quantity_ml = quantity_ml + excluded.quantity_ml,
               updated_at = datetime('now')""",
        (blood_group, quantity_ml),
    )
    return get(db, blood_group)["quantity_ml"]


def list_all(db):
    return db.execute("SELECT * FROM blood_stock ORDER BY blood_group").fetchall()


def remove(db, blood_group, quantity_ml):
    """Decrease stock only if enough exists. Returns new quantity, or None if insufficient."""
    cur = db.execute(
        """UPDATE blood_stock
           SET quantity_ml = quantity_ml - ?, updated_at = datetime('now')
           WHERE blood_group = ? AND quantity_ml >= ?""",
        (quantity_ml, blood_group, quantity_ml),
    )
    if cur.rowcount == 0:
        return None
    return get(db, blood_group)["quantity_ml"]
