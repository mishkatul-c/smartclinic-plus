"""TC-23..TC-25: end-to-end patient journey through the web layer (integration/system)."""
from smartclinic import create_app
from smartclinic.config import TestConfig
from smartclinic.services import ehr
from conftest import TOMORROW, login


def test_tc23_full_patient_journey(app, conn, ids):
    pat, rec, doc = app.test_client(), app.test_client(), app.test_client()
    login(pat, "pat"), login(rec, "rec"), login(doc, "doc")

    # 1 patient sees availability and books
    page = pat.get(f"/patient/?doctor={ids['doc']}&day={TOMORROW}")
    assert b"09:00" in page.data
    pat.post("/patient/book", data={"doctor_id": ids["doc"], "slot": f"{TOMORROW} 09:00",
                                    "reason": "Cough"})
    appt = conn.execute("SELECT id FROM appointments").fetchone()["id"]
    conn.execute("UPDATE appointments SET slot_start=substr(datetime('now','localtime'),1,10)"
                 " || ' 09:00' WHERE id=?", (appt,))

    # 2 reception checks the patient in as urgent
    rec.post("/front-desk", data={"appt_id": appt, "triage": 2})
    assert b"In queue" in rec.get("/front-desk").data

    # 3 doctor calls next and lands on the record
    r = doc.post("/doctor/call-next")
    assert f"/patients/{ids['pat']}" in r.headers["Location"]

    # 4 doctor writes consultation, prescribes, assigns a task
    base = f"/patients/{ids['pat']}"
    doc.post(f"{base}/consult", data={"diagnosis": "Bronchitis", "notes": "Rest", "appt": appt})
    doc.post(f"{base}/prescribe", data={"medication": "Amoxicillin", "dosage": "500mg tds"})
    doc.post(f"{base}/task", data={"title": "Spirometry", "nurse_id": ids["nurse"]})
    status = conn.execute("SELECT status FROM appointments WHERE id=?", (appt,)).fetchone()[0]
    assert status == "COMPLETED"
    assert ehr.full_record(conn, ids["pat"], ids["doc"])["consultations"][0]["diagnosis"] == "Bronchitis"

    # 5 nurse completes the task; patient earns loyalty points
    nurse = app.test_client()
    login(nurse, "nurse")
    task_id = conn.execute("SELECT id FROM tasks").fetchone()["id"]
    nurse.post("/tasks", data={"task_id": task_id})
    nurse.post("/tasks", data={"task_id": task_id})
    assert conn.execute("SELECT status FROM tasks").fetchone()[0] == "DONE"
    assert b"10" in pat.get("/patient/").data


def test_tc24_patient_cannot_cancel_someone_elses_booking(app, conn, ids):
    other = app.test_client()
    login(other, "pat2")
    owner = app.test_client()
    login(owner, "pat")
    owner.post("/patient/book", data={"doctor_id": ids["doc"], "slot": f"{TOMORROW} 10:00"})
    appt = conn.execute("SELECT id FROM appointments").fetchone()["id"]
    r = other.post(f"/patient/cancel/{appt}", follow_redirects=True)
    assert b"not yours" in r.data
    assert conn.execute("SELECT status FROM appointments").fetchone()[0] == "BOOKED"


def test_tc25_forms_without_csrf_token_rejected():
    app = create_app(TestConfig, TESTING=False, SECRET_KEY="x")
    r = app.test_client().post("/login", data={"email": "a", "password": "b"})
    assert r.status_code == 400


def test_allergy_warning_shown_in_ui(app, conn, ids):
    ehr.upsert_record(conn, ids["pat"], ids["doc"], allergies="Penicillin")
    doc = app.test_client()
    login(doc, "doc")
    r = doc.post(f"/patients/{ids['pat']}/prescribe",
                 data={"medication": "Penicillin V", "dosage": "1g"}, follow_redirects=True)
    assert b"recorded allergy" in r.data


def test_analytics_page_renders_forecast(app, conn, ids):
    admin = app.test_client()
    login(admin, "admin")
    assert b"Doctor utilisation" in admin.get("/admin/analytics").data
