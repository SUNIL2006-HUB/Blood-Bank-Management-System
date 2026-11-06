import os
import secrets
import time
from datetime import datetime, timedelta
from pathlib import Path

from flask import Flask, render_template

from . import db


def _persistent_secret_key(instance_path):
    key_path = Path(instance_path) / ".secret_key"
    key_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        descriptor = os.open(
            key_path,
            os.O_CREAT | os.O_EXCL | os.O_WRONLY,
            0o600,
        )
    except FileExistsError:
        pass
    else:
        with os.fdopen(descriptor, "w", encoding="utf-8") as key_file:
            key_file.write(secrets.token_hex(32))

    for _ in range(100):
        key = key_path.read_text(encoding="utf-8").strip()
        if key:
            return key
        time.sleep(0.01)
    raise RuntimeError(f"Could not load a persistent secret key from {key_path}")


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)

    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY"),
        PERMANENT_SESSION_LIFETIME=timedelta(minutes=15),
        MAX_CONTENT_LENGTH=16 * 1024,
        DATABASE=os.environ.get(
            "DATABASE_PATH",
            str(Path(app.instance_path) / "bloodbank.db"),
        ),
    )

    if test_config:
        app.config.update(test_config)

    if not app.config.get("SECRET_KEY"):
        app.config["SECRET_KEY"] = _persistent_secret_key(
            Path(app.config["DATABASE"]).parent
        )

    Path(app.config["DATABASE"]).parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    db.init_db(app.config["DATABASE"])
    app.teardown_appcontext(db.close_db)

    from .routes import auth, availability, donations, donors, issues, reports, users

    app.register_blueprint(donors.bp)
    app.register_blueprint(donations.bp)
    app.register_blueprint(availability.bp)
    app.register_blueprint(issues.bp)
    app.register_blueprint(auth.bp)
    app.register_blueprint(reports.bp)
    app.register_blueprint(users.bp)

    from .routes.auth import roles_required

    @app.get("/")
    @roles_required("staff")
    def index():
        return render_template("index.html")

    @app.context_processor
    def inject_operating_hours():
        from .constants import OPERATING_CLOSE, OPERATING_OPEN

        now = datetime.now().time()

        return {
            "is_open": OPERATING_OPEN <= now < OPERATING_CLOSE,
            "open_time": OPERATING_OPEN.strftime("%I:%M %p").lstrip("0"),
            "close_time": OPERATING_CLOSE.strftime("%I:%M %p").lstrip("0"),
        }

    @app.errorhandler(403)
    def access_denied(_e):
        return render_template("403.html"), 403

    @app.errorhandler(404)
    def not_found(_e):
        return render_template(
            "error.html",
            heading="Page not found",
            message="We could not find that page. Please use the menu above.",
        ), 404

    @app.errorhandler(413)
    def request_too_large(_e):
        return render_template(
            "error.html",
            heading="Request too large",
            message="The submitted information is too large. Please shorten it and try again.",
        ), 413

    @app.errorhandler(500)
    def server_error(_e):
        return render_template("error.html"), 500

    return app