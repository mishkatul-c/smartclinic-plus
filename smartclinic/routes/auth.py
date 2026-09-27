from flask import Blueprint, flash, g, redirect, render_template, request, session, url_for

from ..db import get_db
from ..security import verify_password

bp = Blueprint("auth", __name__)

HOME = {"patient": "patient.dashboard", "doctor": "clinical.doctor_dashboard",
        "nurse": "clinical.tasks", "receptionist": "clinical.front_desk",
        "admin": "admin.analytics"}


@bp.route("/")
def index():
    if g.user:
        return redirect(url_for(HOME[g.user["role"]]))
    return redirect(url_for("auth.login"))


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = get_db().execute("SELECT * FROM users WHERE email=?",
                                (request.form.get("email", "").strip().lower(),)).fetchone()
        if user and verify_password(user["password_hash"], request.form.get("password", "")):
            session.clear()
            session["user_id"] = user["id"]
            return redirect(url_for(HOME[user["role"]]))
        flash("Email or password is incorrect.", "error")
    return render_template("login.html")


@bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("auth.login"))
