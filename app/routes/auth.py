from functools import wraps
from urllib.parse import urlsplit

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
from werkzeug.security import check_password_hash

from ..db import get_db

bp = Blueprint("auth", __name__, url_prefix="/auth")

ALLOWED_ROLES = {"staff", "recipient", "management"}


def login_required(view):
    """Require login before accessing a protected page."""

    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if session.get("user_id") is None:
            flash("Please log in to access this page.", "warning")
            return redirect(
                url_for("auth.login", next=request.path)
            )

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
                return redirect(
                    url_for("auth.login", next=request.path)
                )

            if session.get("role") not in allowed_roles:
                abort(403)

            return view(*args, **kwargs)

        return wrapped_view

    return decorator


def _safe_next_url(target):
    """Allow only local paths for post-login redirects."""

    if not target:
        return url_for("index")

    parsed = urlsplit(target)

    if (
        parsed.scheme
        or parsed.netloc
        or not target.startswith("/")
        or target.startswith("//")
        or "\\" in target
    ):
        return url_for("index")

    return target


@bp.route("/login", methods=("GET", "POST"))
def login():
    """Log in a user using their username and password."""

    if session.get("user_id") is not None:
        return redirect(url_for("index"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = get_db().execute(
            """
            SELECT id, username, password_hash, role
            FROM users
            WHERE username = ?
            """,
            (username,),
        ).fetchone()

        if (
            user is None
            or not check_password_hash(user["password_hash"], password)
            or user["role"] not in ALLOWED_ROLES
        ):
            flash("Invalid username or password.", "error")
            return render_template("auth/login.html"), 401

        session.clear()
        session["user_id"] = user["id"]
        session["username"] = user["username"]
        session["role"] = user["role"]

        next_url = _safe_next_url(
            request.form.get("next", request.args.get("next", ""))
        )

        return redirect(next_url)

    return render_template("auth/login.html")


@bp.post("/logout")
def logout():
    """Log out the current user."""

    if session.get("user_id") is None:
        return redirect(url_for("auth.login"))

    session.clear()
    flash("You have been logged out.", "success")

    return redirect(url_for("auth.login"))