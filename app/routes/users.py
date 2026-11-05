import secrets
import sqlite3

from flask import (
    Blueprint,
    abort,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from werkzeug.security import generate_password_hash

from ..db import get_db
from .auth import ALLOWED_ROLES, roles_required

bp = Blueprint("users", __name__, url_prefix="/users")


def _temporary_password():
    return secrets.token_urlsafe(15)


@bp.get("")
@roles_required("management")
def list_users():
    users = get_db().execute(
        """
        SELECT id, username, role, disabled, must_change_password, created_at
        FROM users
        ORDER BY username
        """
    ).fetchall()
    return render_template("users/list.html", users=users, roles=sorted(ALLOWED_ROLES))


@bp.post("/create")
@roles_required("management")
def create_user():
    username = request.form.get("username", "").strip()
    role = request.form.get("role", "")
    if not username or len(username) > 80 or role not in ALLOWED_ROLES:
        flash("Enter a valid username and role.", "error")
        return redirect(url_for("users.list_users"))

    db = get_db()
    if db.execute("SELECT 1 FROM users WHERE username = ?", (username,)).fetchone():
        flash("That username is already in use.", "error")
        return redirect(url_for("users.list_users"))

    password = _temporary_password()
    try:
        db.execute(
            """
            INSERT INTO users (username, password_hash, role, must_change_password)
            VALUES (?, ?, ?, 1)
            """,
            (username, generate_password_hash(password), role),
        )
    except sqlite3.IntegrityError:
        flash("That username is already in use.", "error")
        return redirect(url_for("users.list_users"))
    flash(
        f"Account created. Temporary password for {username}: {password}",
        "success",
    )
    return redirect(url_for("users.list_users"))


@bp.post("/<int:user_id>/set-disabled")
@roles_required("management")
def set_disabled(user_id):
    db = get_db()
    disabled = request.form.get("disabled") == "1"
    db.execute("BEGIN IMMEDIATE")
    try:
        user = db.execute(
            "SELECT id, role, disabled FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
        if user is None:
            abort(404)

        if disabled and user["role"] == "management" and not user["disabled"]:
            active_managers = db.execute(
                """
                SELECT COUNT(*) AS count
                FROM users
                WHERE role = 'management' AND disabled = 0
                """
            ).fetchone()["count"]
            if active_managers <= 1:
                db.execute("ROLLBACK")
                flash(
                    "The last active management account cannot be disabled.",
                    "error",
                )
                return redirect(url_for("users.list_users"))

        db.execute(
            "UPDATE users SET disabled = ? WHERE id = ?",
            (int(disabled), user_id),
        )
        db.execute("COMMIT")
    except BaseException:
        if db.in_transaction:
            db.execute("ROLLBACK")
        raise

    flash("Account disabled." if disabled else "Account enabled.", "success")
    return redirect(url_for("users.list_users"))


@bp.post("/<int:user_id>/reset-password")
@roles_required("management")
def reset_password(user_id):
    db = get_db()
    if db.execute("SELECT 1 FROM users WHERE id = ?", (user_id,)).fetchone() is None:
        abort(404)

    password = _temporary_password()
    db.execute(
        """
        UPDATE users
        SET password_hash = ?, must_change_password = 1
        WHERE id = ?
        """,
        (generate_password_hash(password), user_id),
    )
    target = db.execute(
        "SELECT username FROM users WHERE id = ?", (user_id,)
    ).fetchone()
    flash(f"Temporary password for {target['username']}: {password}", "success")
    return redirect(url_for("users.list_users"))
