def donation_rows(db, start_date=None, end_date=None):
    conditions, params = [], []
    if start_date:
        conditions.append("d.donation_date >= ?")
        params.append(start_date)
    if end_date:
        conditions.append("d.donation_date <= ?")
        params.append(end_date)
    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    return db.execute(
        f"""SELECT d.id, d.donation_date, d.blood_group, d.quantity_ml,
                   r.name AS donor_name
            FROM donation d JOIN donor r ON r.id = d.donor_id
            {where}
            ORDER BY d.donation_date, d.id""",
        params,
    ).fetchall()
