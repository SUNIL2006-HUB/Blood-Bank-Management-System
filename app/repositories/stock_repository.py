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
