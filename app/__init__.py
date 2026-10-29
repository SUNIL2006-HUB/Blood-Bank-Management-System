import os
from datetime import datetime
from pathlib import Path

from flask import Flask, render_template

from . import db


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-only-change-me"),
        DATABASE=os.environ.get("DATABASE_PATH", str(Path(app.instance_path) / "bloodbank.db")),
        MANAGEMENT_USERNAME=os.environ.get("MANAGEMENT_USERNAME"),
        MANAGEMENT_PASSWORD=os.environ.get("MANAGEMENT_PASSWORD"),
    )
    if test_config:
        app.config.update(test_config)

    Path(app.config["DATABASE"]).parent.mkdir(parents=True, exist_ok=True)
    db.init_db(app.config["DATABASE"])
    app.teardown_appcontext(db.close_db)

    from .routes import availability, donations, donors, issues, reports

    app.register_blueprint(donors.bp)
    app.register_blueprint(donations.bp)
    app.register_blueprint(availability.bp)
    app.register_blueprint(issues.bp)
    app.register_blueprint(reports.bp)

    @app.get("/")
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

    @app.errorhandler(404)
    def not_found(_e):
        return render_template(
            "error.html",
            heading="Page not found",
            message="We could not find that page. Please use the menu above.",
        ), 404

    @app.errorhandler(403)
    def forbidden(_e):
        return render_template(
            "error.html",
            heading="Access denied",
            message="Only blood bank management can generate reports. Sign in with a management account to continue.",
        ), 403

    @app.errorhandler(500)
    def server_error(_e):
        # generic message only - no stack traces or DB details (SEC-12)
        return render_template("error.html"), 500

    return app
