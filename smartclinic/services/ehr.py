"""Electronic Health Records (FR-07) with field-level encryption (NFR-03).

Clinical free text is encrypted before it reaches the database, so a stolen backup
or a mis-scoped SQL query exposes ciphertext only. Every read is audited.
"""
from ..db import audit, transaction
from ..security import decrypt, encrypt


def upsert_record(conn, patient_id, actor_id, dob=None, history=None, allergies=None):
    with transaction(conn):
        conn.execute(
            "INSERT INTO health_records (patient_id, date_of_birth, medical_history_enc, "
            "allergies_enc) VALUES (?,?,?,?) ON CONFLICT(patient_id) DO UPDATE SET "
            "date_of_birth=excluded.date_of_birth, medical_history_enc=excluded.medical_history_enc, "
            "allergies_enc=excluded.allergies_enc, updated_at=datetime('now')",
            (patient_id, dob, encrypt(history or ""), encrypt(allergies or "")))
        audit(conn, actor_id, "EHR_WRITE", "health_record", patient_id)


def allergies(conn, patient_id):
    row = conn.execute("SELECT allergies_enc FROM health_records WHERE patient_id=?",
                       (patient_id,)).fetchone()
    if row is None or not row["allergies_enc"]:
        return []
    return [a.strip().lower() for a in decrypt(row["allergies_enc"]).split(",") if a.strip()]


def add_consultation(conn, patient_id, doctor_id, diagnosis, notes, appointment_id=None):
    with transaction(conn):
        cur = conn.execute(
            "INSERT INTO consultations (appointment_id, patient_id, doctor_id, diagnosis_enc, "
            "notes_enc) VALUES (?,?,?,?,?)",
            (appointment_id, patient_id, doctor_id, encrypt(diagnosis), encrypt(notes)))
        if appointment_id:
            conn.execute("UPDATE appointments SET status='COMPLETED', completed_at=datetime('now') "
                         "WHERE id=? AND status IN ('IN_CONSULT','CHECKED_IN')", (appointment_id,))
        audit(conn, doctor_id, "CONSULT_WRITE", "consultation", cur.lastrowid)
    return cur.lastrowid


def full_record(conn, patient_id, actor_id):
    """Decrypted view of a patient's record for an authorised clinician."""
    audit(conn, actor_id, "EHR_READ", "health_record", patient_id)
    patient = conn.execute("SELECT id, full_name, email, phone FROM users WHERE id=?",
                           (patient_id,)).fetchone()
    hr = conn.execute("SELECT * FROM health_records WHERE patient_id=?", (patient_id,)).fetchone()
    consults = conn.execute(
        "SELECT c.*, u.full_name AS doctor_name FROM consultations c JOIN users u "
        "ON u.id=c.doctor_id WHERE c.patient_id=? ORDER BY c.created_at DESC",
        (patient_id,)).fetchall()
    labs = conn.execute("SELECT * FROM lab_results WHERE patient_id=? ORDER BY recorded_at DESC",
                        (patient_id,)).fetchall()
    rx = conn.execute("SELECT * FROM prescriptions WHERE patient_id=? ORDER BY created_at DESC",
                      (patient_id,)).fetchall()
    return {
        "patient": dict(patient) if patient else None,
        "dob": hr["date_of_birth"] if hr else None,
        "history": decrypt(hr["medical_history_enc"]) if hr else "",
        "allergies": decrypt(hr["allergies_enc"]) if hr else "",
        "consultations": [dict(c, diagnosis=decrypt(c["diagnosis_enc"]),
                               notes=decrypt(c["notes_enc"])) for c in consults],
        "labs": [dict(lab, result=decrypt(lab["result_enc"])) for lab in labs],
        "prescriptions": [dict(p) for p in rx],
    }
