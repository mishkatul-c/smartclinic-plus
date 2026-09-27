"""E-prescription (FR-05) with an allergy safety check before anything is sent."""
from ..db import audit, transaction
from . import ehr, notifications


class AllergyConflict(Exception):
    pass


def create(conn, doctor_id, patient_id, medication, dosage, pharmacy=None, override=False):
    known = ehr.allergies(conn, patient_id)
    med = medication.strip().lower()
    hits = [a for a in known if a and (a in med or med in a)]
    if hits and not override:
        raise AllergyConflict(f"Patient has a recorded allergy to: {', '.join(hits)}")
    with transaction(conn):
        cur = conn.execute(
            "INSERT INTO prescriptions (patient_id, doctor_id, medication, dosage, pharmacy) "
            "VALUES (?,?,?,?,?)", (patient_id, doctor_id, medication.strip(), dosage, pharmacy))
        rx_id = cur.lastrowid
        audit(conn, doctor_id, "RX_OVERRIDE" if hits else "RX_CREATE", "prescription", rx_id)
        notifications.queue(conn, patient_id, "New e-prescription",
                            f"Prescription #{rx_id}: {medication} ({dosage})"
                            + (f" sent to {pharmacy}." if pharmacy else "."),
                            "0000-00-00 00:00")
    return rx_id
