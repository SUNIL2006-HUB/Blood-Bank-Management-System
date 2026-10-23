import os
from pathlib import Path

from flask import Flask, render_template

from . import db


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-only-change-me"),
        DATABASE=os.environ.get("DATABASE_PATH", str(Path(app.instance_path) / "bloodbank.db")),
    )
    if test_config:
        app.config.update(test_config)

    Path(app.config["DATABASE"]).parent.mkdir(parents=True, exist_ok=True)
    db.init_db(app.config["DATABASE"])
    app.teardown_appcontext(db.close_db)

    from .routes import availability, donations, donors, issues

    app.register_blueprint(donors.bp)
    app.register_blueprint(donations.bp)
    app.register_blueprint(availability.bp)
    app.register_blueprint(issues.bp)

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.errorhandler(500)
    def server_error(_e):
        # generic message only - no stack traces or DB details (SEC-12)
        return render_template("error.html"), 500

    return app
