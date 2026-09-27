"""Online appointment booking, rescheduling and cancellation (FR-01; NFR-01).

Double booking is prevented at two levels: an application check inside an
IMMEDIATE transaction, and the partial unique index ux_active_slot in the database,
which remains the final guarantee even if two requests race past the check.
"""
import sqlite3
from datetime import datetime, timedelta

from ..db import audit, transaction
from . import notifications

ACTIVE = ("BOOKED", "CHECKED_IN", "IN_CONSULT")
FMT = "%Y-%m-%d %H:%M"


class BookingError(Exception):
    """Raised when a booking request cannot be honoured."""


class SlotTakenError(BookingError):
    pass


def _parse(ts):
    return datetime.strptime(ts, FMT)


def available_slots(conn, doctor_id, day):
    """Return free slot start times for a doctor on a given date (YYYY-MM-DD)."""
    doc = conn.execute("SELECT * FROM doctors WHERE user_id = ?", (doctor_id,)).fetchone()
    if doc is None:
        raise BookingError("Unknown doctor")
    start = _parse(f"{day} {doc['day_start']}")
    end = _parse(f"{day} {doc['day_end']}")
    taken = {
        r["slot_start"]
        for r in conn.execute(
            "SELECT slot_start FROM appointments WHERE doctor_id = ? AND slot_start LIKE ? "
            "AND status IN (?,?,?)",
            (doctor_id, f"{day}%", *ACTIVE),
        )
    }
    slots, t = [], start
    while t < end:
        s = t.strftime(FMT)
        if s not in taken:
            slots.append(s)
        t += timedelta(minutes=doc["slot_minutes"])
    return slots


def _validate_slot(conn, doctor_id, slot_start, now):
    doc = conn.execute("SELECT * FROM doctors WHERE user_id = ?", (doctor_id,)).fetchone()
    if doc is None:
        raise BookingError("Unknown doctor")
    try:
        when = _parse(slot_start)
    except ValueError as exc:
        raise BookingError("Slot must be formatted YYYY-MM-DD HH:MM") from exc
    if when <= now:
        raise BookingError("Appointments must be booked in the future")
    day = when.strftime("%Y-%m-%d")
    if not (_parse(f"{day} {doc['day_start']}") <= when < _parse(f"{day} {doc['day_end']}")):
        raise BookingError("Slot is outside the doctor's working hours")
    minutes_from_start = (when - _parse(f"{day} {doc['day_start']}")).seconds // 60
    if minutes_from_start % doc["slot_minutes"]:
        raise BookingError("Slot does not align with the doctor's schedule")


def book(conn, patient_id, doctor_id, slot_start, reason="", now=None, actor_id=None):
    now = now or datetime.now()
    _validate_slot(conn, doctor_id, slot_start, now)
    try:
        with transaction(conn):
            clash = conn.execute(
                "SELECT 1 FROM appointments WHERE doctor_id = ? AND slot_start = ? "
                "AND status IN (?,?,?)",
                (doctor_id, slot_start, *ACTIVE),
            ).fetchone()
            if clash:
                raise SlotTakenError("That slot has just been taken. Please choose another.")
            cur = conn.execute(
                "INSERT INTO appointments (patient_id, doctor_id, slot_start, reason) "
                "VALUES (?,?,?,?)",
                (patient_id, doctor_id, slot_start, reason),
            )
            appt_id = cur.lastrowid
            audit(conn, actor_id or patient_id, "BOOK", "appointment", appt_id)
            notifications.queue_appointment_messages(conn, appt_id)
    except sqlite3.IntegrityError as exc:  # the database-level guard fired
        raise SlotTakenError("That slot has just been taken. Please choose another.") from exc
    return appt_id


def reschedule(conn, appt_id, new_slot, actor_id, now=None):
    now = now or datetime.now()
    appt = conn.execute("SELECT * FROM appointments WHERE id = ?", (appt_id,)).fetchone()
    if appt is None or appt["status"] != "BOOKED":
        raise BookingError("Only booked appointments can be rescheduled")
    _validate_slot(conn, appt["doctor_id"], new_slot, now)
    try:
        with transaction(conn):
            # optimistic concurrency: the row must still be at the version we read
            cur = conn.execute(
                "UPDATE appointments SET slot_start = ?, version = version + 1 "
                "WHERE id = ? AND version = ? AND status = 'BOOKED'",
                (new_slot, appt_id, appt["version"]),
            )
            if cur.rowcount != 1:
                raise BookingError("Appointment was changed by someone else; please retry")
            audit(conn, actor_id, "RESCHEDULE", "appointment", appt_id)
            conn.execute("DELETE FROM notifications WHERE sent_at IS NULL AND body LIKE ?",
                         (f"%#{appt_id}%",))
            notifications.queue_appointment_messages(conn, appt_id)
    except sqlite3.IntegrityError as exc:
        raise SlotTakenError("That slot has just been taken. Please choose another.") from exc


def cancel(conn, appt_id, actor_id):
    with transaction(conn):
        cur = conn.execute(
            "UPDATE appointments SET status = 'CANCELLED', version = version + 1 "
            "WHERE id = ? AND status = 'BOOKED'", (appt_id,))
        if cur.rowcount != 1:
            raise BookingError("Only booked appointments can be cancelled")
        conn.execute("DELETE FROM notifications WHERE sent_at IS NULL AND body LIKE ?",
                     (f"%#{appt_id}%",))
        audit(conn, actor_id, "CANCEL", "appointment", appt_id)


def upcoming_for_patient(conn, patient_id):
    return conn.execute(
        "SELECT a.*, u.full_name AS doctor_name, d.specialty FROM appointments a "
        "JOIN users u ON u.id = a.doctor_id JOIN doctors d ON d.user_id = a.doctor_id "
        "WHERE a.patient_id = ? AND a.status IN ('BOOKED','CHECKED_IN') "
        "ORDER BY a.slot_start", (patient_id,)).fetchall()
