from datetime import date

from flask import Blueprint, abort, flash, g, redirect, render_template, request, url_for

from ..db import get_db
from ..security import requires
from ..services import ehr, labs, prescriptions, queue
from ..services import tasks as task_service

bp = Blueprint("clinical", __name__)


@bp.route("/doctor")
@requires("ehr:write")
def doctor_dashboard():
    conn = get_db()
    today = request.args.get("day", date.today().isoformat())
    schedule = conn.execute(
        "SELECT a.*, u.full_name AS patient_name FROM appointments a JOIN users u "
        "ON u.id=a.patient_id WHERE a.doctor_id=? AND a.slot_start LIKE ? "
        "AND a.status!='CANCELLED' ORDER BY a.slot_start", (g.user["id"], f"{today}%")).fetchall()
    return render_template("doctor_dashboard.html", schedule=schedule, day=today,
                           waiting=queue.current_queue(conn, g.user["id"]),
                           my_tasks=conn.execute(
                               "SELECT t.*, u.full_name AS nurse FROM tasks t JOIN users u "
                               "ON u.id=t.assigned_to WHERE created_by=? AND status!='DONE'",
                               (g.user["id"],)).fetchall())


@bp.route("/doctor/call-next", methods=["POST"])
@requires("ehr:write")
def call_next():
    nxt = queue.call_next(get_db(), g.user["id"], g.user["id"])
    if nxt:
        return redirect(url_for("clinical.patient_record", patient_id=nxt["patient_id"],
                                appt=nxt["id"]))
    flash("Nobody is waiting.", "ok")
    return redirect(url_for("clinical.doctor_dashboard"))


@bp.route("/patients/<int:patient_id>", methods=["GET"])
@requires("ehr:read")
def patient_record(patient_id):
    rec = ehr.full_record(get_db(), patient_id, g.user["id"])
    if rec["patient"] is None:
        abort(404)
    nurses = get_db().execute("SELECT id, full_name FROM users WHERE role='nurse'").fetchall()
    return render_template("patient_record.html", rec=rec, appt=request.args.get("appt"),
                           nurses=nurses)


@bp.route("/patients/<int:patient_id>/prescribe", methods=["POST"])
@requires("prescription:create")
def prescribe(patient_id):
    try:
        prescriptions.create(get_db(), g.user["id"], patient_id, request.form["medication"],
                             request.form["dosage"], request.form.get("pharmacy") or None,
                             override=bool(request.form.get("override")))
        flash("Prescription sent.", "ok")
    except prescriptions.AllergyConflict as exc:
        flash(str(exc) + ". Tick 'override' only if clinically justified.", "error")
    return redirect(url_for("clinical.patient_record", patient_id=patient_id))


@bp.route("/patients/<int:patient_id>/consult", methods=["POST"])
@requires("ehr:write")
def consult(patient_id):
    appt = request.form.get("appt") or None
    ehr.add_consultation(get_db(), patient_id, g.user["id"], request.form["diagnosis"],
                         request.form["notes"], int(appt) if appt else None)
    if appt:
        from ..services import engagement
        engagement.award_visit(get_db(), patient_id, int(appt))
    flash("Consultation saved.", "ok")
    return redirect(url_for("clinical.doctor_dashboard"))


@bp.route("/patients/<int:patient_id>/task", methods=["POST"])
@requires("task:assign")
def assign_task(patient_id):
    task_service.assign(get_db(), request.form["title"], int(request.form["nurse_id"]),
                        g.user["id"], patient_id, request.form.get("due_at") or None)
    flash("Task assigned.", "ok")
    return redirect(url_for("clinical.patient_record", patient_id=patient_id))


@bp.route("/patients/<int:patient_id>/lab", methods=["POST"])
@requires("lab:record")
def record_lab(patient_id):
    labs.record(get_db(), patient_id, request.form["test_name"], request.form["result"],
                request.form["flag"], g.user["id"])
    flash("Lab result recorded.", "ok")
    return redirect(request.referrer or url_for("clinical.tasks"))


@bp.route("/tasks", methods=["GET", "POST"])
@requires("task:update")
def tasks():
    conn = get_db()
    if request.method == "POST":
        try:
            task_service.advance(conn, int(request.form["task_id"]), g.user["id"])
        except (PermissionError, ValueError) as exc:
            flash(str(exc), "error")
        return redirect(url_for("clinical.tasks"))
    return render_template("tasks.html", tasks=task_service.for_user(conn, g.user["id"]))


@bp.route("/front-desk", methods=["GET", "POST"])
@requires("queue:manage")
def front_desk():
    conn = get_db()
    if request.method == "POST":
        appt_id = int(request.form["appt_id"])
        if request.form.get("action") == "emergency":
            queue.flag_emergency(conn, appt_id, g.user["id"])
        else:
            queue.check_in(conn, appt_id, g.user["id"],
                           triage_level=int(request.form.get("triage", 3)))
        return redirect(url_for("clinical.front_desk"))
    today = date.today().isoformat()
    booked = conn.execute(
        "SELECT a.*, p.full_name AS patient_name, d.full_name AS doctor_name FROM appointments a "
        "JOIN users p ON p.id=a.patient_id JOIN users d ON d.id=a.doctor_id "
        "WHERE a.slot_start LIKE ? AND a.status IN ('BOOKED','CHECKED_IN') ORDER BY a.slot_start",
        (f"{today}%",)).fetchall()
    doctors = conn.execute("SELECT u.id, u.full_name FROM users u WHERE role='doctor'").fetchall()
    queues = {d["full_name"]: queue.current_queue(conn, d["id"]) for d in doctors}
    return render_template("front_desk.html", booked=booked, queues=queues)
