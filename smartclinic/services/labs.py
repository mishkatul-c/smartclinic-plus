"""Lab and test integration (FR-08): results are linked to the patient profile."""
from ..db import audit, transaction
from ..security import encrypt
from . import notifications

FLAGS = ("NORMAL", "ABNORMAL", "CRITICAL")


def record(conn, patient_id, test_name, result, flag, recorded_by, notify_doctor_id=None):
    if flag not in FLAGS:
        raise ValueError("Unknown flag")
    with transaction(conn):
        cur = conn.execute(
            "INSERT INTO lab_results (patient_id, test_name, result_enc, flag, recorded_by) "
            "VALUES (?,?,?,?,?)", (patient_id, test_name, encrypt(result), flag, recorded_by))
        audit(conn, recorded_by, "LAB_RECORD", "lab_result", cur.lastrowid)
        if flag == "CRITICAL" and notify_doctor_id:
            notifications.queue(conn, notify_doctor_id, "Critical lab result",
                                f"Critical {test_name} result recorded for patient {patient_id}.",
                                "0000-00-00 00:00", channels=("SMS",))
    return cur.lastrowid
