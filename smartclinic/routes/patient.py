from datetime import date, timedelta

from flask import Blueprint, flash, g, redirect, render_template, request, url_for

from ..db import get_db
from ..security import requires
from ..services import booking, engagement

bp = Blueprint("patient", __name__, url_prefix="/patient")


@bp.route("/")
@requires("appointment:book")
def dashboard():
    conn = get_db()
    doctors = conn.execute("SELECT d.user_id, u.full_name, d.specialty FROM doctors d "
                           "JOIN users u ON u.id=d.user_id ORDER BY u.full_name").fetchall()
    doctor_id = int(request.args.get("doctor", doctors[0]["user_id"] if doctors else 0))
    day = request.args.get("day", (date.today() + timedelta(days=1)).isoformat())
    slots = booking.available_slots(conn, doctor_id, day) if doctors else []
    pts = engagement.balance(conn, g.user["id"])
    return render_template("patient_dashboard.html", doctors=doctors, doctor_id=doctor_id,
                           day=day, slots=slots,
                           appts=booking.upcoming_for_patient(conn, g.user["id"]),
                           points=pts, tier=engagement.tier(pts),
                           package=pts >= engagement.PACKAGE_THRESHOLD)


@bp.route("/book", methods=["POST"])
@requires("appointment:book")
def book():
    try:
        booking.book(get_db(), g.user["id"], int(request.form["doctor_id"]),
                     request.form["slot"], request.form.get("reason", ""))
        flash("Appointment booked. A confirmation has been sent to your email.", "ok")
    except booking.BookingError as exc:
        flash(str(exc), "error")
    return redirect(url_for("patient.dashboard", doctor=request.form["doctor_id"],
                            day=request.form["slot"][:10]))


@bp.route("/cancel/<int:appt_id>", methods=["POST"])
@requires("appointment:book")
def cancel(appt_id):
    conn = get_db()
    owner = conn.execute("SELECT patient_id FROM appointments WHERE id=?", (appt_id,)).fetchone()
    if owner is None or owner["patient_id"] != g.user["id"]:
        flash("That appointment is not yours to cancel.", "error")
    else:
        booking.cancel(conn, appt_id, g.user["id"])
        flash("Appointment cancelled.", "ok")
    return redirect(url_for("patient.dashboard"))
