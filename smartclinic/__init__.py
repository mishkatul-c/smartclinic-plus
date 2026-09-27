"""SmartClinic+ — intelligent outpatient clinic management system."""
from flask import Flask, g, session

from . import db as dbmod
from .config import Config
from .security import check_csrf, csrf_token


def create_app(config_object=Config, **overrides):
    app = Flask(__name__)
    app.config.from_object(config_object)
    app.config.update(overrides)

    if app.config["DATABASE"] == ":memory:":
        # a single shared connection keeps the in-memory database alive for tests
        conn = dbmod.connect(":memory:")
        dbmod.init_schema(conn)
        app.config["_SHARED_CONN"] = conn
    else:
        conn = dbmod.connect(app.config["DATABASE"])
        dbmod.init_schema(conn)
        conn.close()

    app.teardown_appcontext(dbmod.close_db)

    @app.before_request
    def load_user():
        check_csrf()
        uid = session.get("user_id")
        g.user = None
        if uid is not None:
            g.user = dbmod.get_db().execute(
                "SELECT id, full_name, email, role FROM users WHERE id=?", (uid,)).fetchone()

    @app.context_processor
    def inject():
        return {"csrf_token": csrf_token, "current_user": g.get("user")}

    @app.after_request
    def security_headers(resp):
        resp.headers["X-Content-Type-Options"] = "nosniff"
        resp.headers["X-Frame-Options"] = "DENY"
        resp.headers["Referrer-Policy"] = "same-origin"
        return resp

    from .routes import auth, clinical, patient, admin
    app.register_blueprint(auth.bp)
    app.register_blueprint(patient.bp)
    app.register_blueprint(clinical.bp)
    app.register_blueprint(admin.bp)
    return app
