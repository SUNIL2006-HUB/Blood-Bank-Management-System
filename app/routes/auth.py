import sqlite3
from functools import wraps

from flask import (
    Blueprint,
    abort,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash

from ..db import get_db

bp = Blueprint("auth", __name__, url_prefix="/auth")

ALLOWED_ROLES = {"staff", "recipient", "management"}
ROLE_LANDING_ENDPOINTS = {
    "staff": "index",
    "recipient": "availability.view",
    "management": "reports.generate",
}

def _password_error(password):
    if len(password) < 8:
        return "Password must be at least 8 characters."
    return None


def login_required(view):
    """Require login before accessing a protected page."""

    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if session.get("user_id") is None:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("auth.login"))

        return view(*args, **kwargs)

    return wrapped_view


def roles_required(*allowed_roles):
    """Allow access only to users with specified roles."""

    if not allowed_roles or not set(allowed_roles).issubset(ALLOWED_ROLES):
        raise ValueError("Invalid or missing role configuration.")

    def decorator(view):
        @wraps(view)
        def wrapped_view(*args, **kwargs):
            if session.get("user_id") is None:
                flash("Please log in to access this page.", "warning")
                return redirect(url_for("auth.login"))

            if session.get("role") not in allowed_roles:
                abort(403)

            return view(*args, **kwargs)

        return wrapped_view

    return decorator


@bp.before_app_request
def validate_session_account():
    """Revalidate account status and role so account changes take effect."""
    user_id = session.get("user_id")
    if user_id is None:
        return None

    user = get_db().execute(
        "SELECT role, disabled, must_change_password FROM users WHERE id = ?",
        (user_id,),
    ).fetchone()
    if (
        user is None
        or user["disabled"]
        or user["role"] != session.get("role")
    ):
        session.clear()
        flash("Your account session has ended. Please log in again.", "warning")
        return redirect(url_for("auth.login"))

    if (
        user["must_change_password"]
        and request.endpoint not in {
            "auth.change_password",
            "auth.logout",
            "static",
        }
    ):
        return redirect(url_for("auth.change_password"))

    return None


@bp.route("/login", methods=("GET", "POST"))
def login():
    """Log in a user using their username and password."""

    if session.get("user_id") is not None:
        if session.get("must_change_password"):
            return redirect(url_for("auth.change_password"))
        return redirect(url_for(ROLE_LANDING_ENDPOINTS[session["role"]]))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        role = request.form.get("role", "")
        db = get_db()

        user = None
        if len(username) <= 80:
            user = db.execute(
                """
                SELECT id, username, password_hash, role, disabled,
                       must_change_password
                FROM users
                WHERE username = ?
                """,
                (username,),
            ).fetchone()

        if (
            user is None
            or len(username) > 80
            or not check_password_hash(user["password_hash"], password)
            or user["role"] not in ALLOWED_ROLES
            or user["disabled"]
            or user["role"] != role
        ):
            flash("Invalid username or password.", "error")
            return render_template(
                "auth/login.html",
                manager_exists=_manager_exists(),
                login_role=role,
            ), 401

        session.clear()
        session["user_id"] = user["id"]
        session["username"] = user["username"]
        session["role"] = user["role"]
        session["must_change_password"] = bool(user["must_change_password"])
        if user["must_change_password"]:
            return redirect(url_for("auth.change_password"))
        return redirect(url_for(ROLE_LANDING_ENDPOINTS[user["role"]]))

    return render_template(
        "auth/login.html",
        manager_exists=_manager_exists(),
        login_role=request.args.get("role", ""),
    )


def _manager_exists():
    return (
        get_db()
        .execute("SELECT 1 FROM users WHERE role = 'management' LIMIT 1")
        .fetchone()
        is not None
    )


@bp.route("/signup", methods=("GET", "POST"))
def signup():
    """Create a recipient account from the public signup form."""
    if session.get("user_id") is not None:
        return redirect(url_for(ROLE_LANDING_ENDPOINTS[session["role"]]))

    if request.method == "GET":
        return render_template(
            "auth/signup.html",
            username="",
            errors={},
        )

    username = request.form.get("signup_username", "").strip()
    password = request.form.get("password", "")
    confirmation = request.form.get("confirmation", "")
    errors = {}
    if not username or len(username) > 80:
        errors["username"] = "Enter a username of at most 80 characters."
    password_error = _password_error(password)
    if password_error:
        errors["password"] = password_error
    elif password != confirmation:
        errors["confirmation"] = "Passwords do not match."

    if errors:
        return render_template(
            "auth/signup.html",
            username=username,
            errors=errors,
        ), 400

    db = get_db()
    if db.execute("SELECT 1 FROM users WHERE username = ?", (username,)).fetchone():
        errors["username"] = "That username is already in use."
    if errors:
        return render_template(
            "auth/signup.html",
            username=username,
            errors=errors,
        ), 400
    try:
        db.execute(
            """
            INSERT INTO users (username, password_hash, role)
            VALUES (?, ?, 'recipient')
            """,
            (username, generate_password_hash(password)),
        )
    except sqlite3.IntegrityError:
        flash("That username is already in use.", "error")
        return render_template(
            "auth/signup.html",
            username=username,
            errors={},
        ), 400

    flash("User account created. You can now log in.", "success")
    return redirect(url_for("auth.login", role="recipient"))


@bp.route("/setup", methods=("GET", "POST"))
def setup():
    """Create the first management account exactly once."""
    db = get_db()
    if _manager_exists():
        abort(404)

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        error = _password_error(password)
        if not username or len(username) > 80:
            error = "Username is required and must be at most 80 characters."

        if error:
            flash(error, "error")
        elif db.execute(
            "SELECT 1 FROM users WHERE username = ?", (username,)
        ).fetchone():
            flash("That username is already in use.", "error")
        else:
            db.execute("BEGIN IMMEDIATE")
            try:
                exists = db.execute(
                    "SELECT 1 FROM users WHERE role = 'management' LIMIT 1"
                ).fetchone()
                if exists:
                    abort(404)
                db.execute(
                    """
                    INSERT INTO users (username, password_hash, role)
                    VALUES (?, ?, 'management')
                    """,
                    (username, generate_password_hash(password)),
                )
                db.execute("COMMIT")
            except sqlite3.IntegrityError:
                if db.in_transaction:
                    db.execute("ROLLBACK")
                flash("That username is already in use.", "error")
            except BaseException:
                if db.in_transaction:
                    db.execute("ROLLBACK")
                raise
            else:
                flash("Management account created. Please log in.", "success")
                return redirect(url_for("auth.login", role="management"))

    return render_template("auth/setup.html")


@bp.route("/change-password", methods=("GET", "POST"))
@login_required
def change_password():
    errors = []
    if request.method == "POST":
        password = request.form.get("password", "")
        confirmation = request.form.get("confirmation", "")
        error = _password_error(password)
        if error:
            errors.append(error)
        elif password != confirmation:
            errors.append("Passwords do not match.")

        if not errors:
            get_db().execute(
                """
                UPDATE users
                SET password_hash = ?, must_change_password = 0
                WHERE id = ?
                """,
                (generate_password_hash(password), session["user_id"]),
            )
            session["must_change_password"] = False
            flash("Password changed successfully.", "success")
            return redirect(url_for(ROLE_LANDING_ENDPOINTS[session["role"]]))

    return render_template("auth/change_password.html", errors=errors)


@bp.post("/logout")
def logout():
    """Log out the current user."""

    if session.get("user_id") is None:
        return redirect(url_for("auth.login"))

    session.clear()
    flash("You have been logged out.", "success")

    return redirect(url_for("auth.login"))