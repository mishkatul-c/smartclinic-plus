"""Patient engagement (FR-12): loyalty points and health-check package eligibility."""
from ..db import transaction

POINTS_PER_VISIT = 10
PACKAGE_THRESHOLD = 50  # points needed for a discounted annual health check


def award_visit(conn, patient_id, appointment_id):
    with transaction(conn):
        conn.execute("INSERT INTO loyalty_ledger (patient_id, points, reason) VALUES (?,?,?)",
                     (patient_id, POINTS_PER_VISIT, f"Completed visit #{appointment_id}"))


def balance(conn, patient_id):
    return conn.execute("SELECT COALESCE(SUM(points),0) FROM loyalty_ledger WHERE patient_id=?",
                        (patient_id,)).fetchone()[0]


def tier(points):
    if points >= 100:
        return "Gold"
    if points >= PACKAGE_THRESHOLD:
        return "Silver"
    return "Standard"


def eligible_for_package(conn, patient_id):
    return balance(conn, patient_id) >= PACKAGE_THRESHOLD
