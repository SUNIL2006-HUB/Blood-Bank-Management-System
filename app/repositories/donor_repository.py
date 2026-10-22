def create(db, name, age, blood_group, phone):
    cur = db.execute(
        "INSERT INTO donor (name, age, blood_group, phone) VALUES (?, ?, ?, ?)",
        (name, age, blood_group, phone),
    )
    return cur.lastrowid


def get(db, donor_id):
    return db.execute("SELECT * FROM donor WHERE id = ?", (donor_id,)).fetchone()


def get_by_phone(db, phone):
    return db.execute("SELECT * FROM donor WHERE phone = ?", (phone,)).fetchone()


def list_all(db):
    return db.execute("SELECT * FROM donor ORDER BY id").fetchall()
