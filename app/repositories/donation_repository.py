def create(db, donor_id, blood_group, quantity_ml, donation_date):
    cur = db.execute(
        """INSERT INTO donation (donor_id, blood_group, quantity_ml, donation_date)
           VALUES (?, ?, ?, ?)""",
        (donor_id, blood_group, quantity_ml, donation_date),
    )
    return cur.lastrowid


def list_recent(db, limit=20):
    return db.execute(
        """SELECT d.*, r.name AS donor_name FROM donation d
           JOIN donor r ON r.id = d.donor_id
           ORDER BY d.id DESC LIMIT ?""",
        (limit,),
    ).fetchall()
