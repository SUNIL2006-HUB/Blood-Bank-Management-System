def record(db, action, actor_username, user_id=None, target_type=None, target_id=None):
    db.execute(
        """
        INSERT INTO audit_log
            (user_id, actor_username, action, target_type, target_id)
        VALUES (?, ?, ?, ?, ?)
        """,
        (user_id, actor_username, action, target_type, target_id),
    )
