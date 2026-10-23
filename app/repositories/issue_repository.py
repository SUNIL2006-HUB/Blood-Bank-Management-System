def create(db, blood_group, quantity_ml, recipient):
    cur = db.execute(
        "INSERT INTO blood_issue (blood_group, quantity_ml, recipient) VALUES (?, ?, ?)",
        (blood_group, quantity_ml, recipient),
    )
    return cur.lastrowid


def list_recent(db, limit=20):
    return db.execute(
        "SELECT * FROM blood_issue ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
