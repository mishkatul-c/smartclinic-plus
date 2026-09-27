"""Smart queue (FR-02): a dynamic waiting list driven by check-ins, delays and triage.

Ordering rule, applied every time the queue is read:
  1. triage level (1 = emergency, 2 = urgent, 3 = routine)
  2. on-time patients before late arrivals (checked in > grace minutes after slot)
  3. scheduled slot time, then check-in time
Estimated wait = patients ahead x slot length + the doctor's running delay.
"""
from datetime import datetime

from ..db import audit, transaction

FMT = "%Y-%m-%d %H:%M"


def check_in(conn, appt_id, actor_id, now=None, triage_level=3):
    now = (now or datetime.now()).strftime(FMT)
    with transaction(conn):
        cur = conn.execute(
            "UPDATE appointments SET status='CHECKED_IN', checked_in_at=?, triage_level=? "
            "WHERE id=? AND status='BOOKED'", (now, triage_level, appt_id))
        if cur.rowcount != 1:
            raise ValueError("Appointment is not awaiting check-in")
        audit(conn, actor_id, "CHECK_IN", "appointment", appt_id)


def flag_emergency(conn, appt_id, actor_id):
    with transaction(conn):
        conn.execute("UPDATE appointments SET triage_level = 1 WHERE id = ?", (appt_id,))
        audit(conn, actor_id, "TRIAGE_EMERGENCY", "appointment", appt_id)


def set_delay(conn, doctor_id, minutes):
    conn.execute("UPDATE doctors SET running_delay = ? WHERE user_id = ?",
                 (max(0, int(minutes)), doctor_id))


def _sort_key(row, grace):
    slot = datetime.strptime(row["slot_start"], FMT)
    arrived = datetime.strptime(row["checked_in_at"], FMT)
    late = (arrived - slot).total_seconds() / 60 > grace
    return (row["triage_level"], late, slot, arrived)


def current_queue(conn, doctor_id, grace_minutes=15):
    doc = conn.execute("SELECT slot_minutes, running_delay FROM doctors WHERE user_id=?",
                       (doctor_id,)).fetchone()
    rows = conn.execute(
        "SELECT a.*, u.full_name AS patient_name FROM appointments a "
        "JOIN users u ON u.id = a.patient_id "
        "WHERE a.doctor_id = ? AND a.status = 'CHECKED_IN'", (doctor_id,)).fetchall()
    ordered = sorted(rows, key=lambda r: _sort_key(r, grace_minutes))
    result = []
    for pos, r in enumerate(ordered):
        item = dict(r)
        item["position"] = pos + 1
        item["est_wait_min"] = pos * doc["slot_minutes"] + doc["running_delay"]
        result.append(item)
    return result


def call_next(conn, doctor_id, actor_id, now=None):
    q = current_queue(conn, doctor_id)
    if not q:
        return None
    nxt = q[0]
    now = (now or datetime.now()).strftime(FMT)
    with transaction(conn):
        conn.execute("UPDATE appointments SET status='IN_CONSULT', called_at=? WHERE id=?",
                     (now, nxt["id"]))
        audit(conn, actor_id, "CALL", "appointment", nxt["id"])
    return nxt
