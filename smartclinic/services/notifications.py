"""Automated SMS / e-mail notifications (FR-03).

Messages are written to an outbox table and dispatched by a scheduler, so a slow
SMS gateway can never block or roll back a booking. Channel adapters are pluggable.
"""
from datetime import datetime, timedelta

FMT = "%Y-%m-%d %H:%M"


class ConsoleChannel:
    """Development adapter. Production swaps in e.g. an SMS gateway or SMTP adapter."""
    def __init__(self):
        self.sent = []

    def send(self, to, subject, body):
        self.sent.append((to, subject, body))


def queue(conn, user_id, subject, body, send_after, channels=("EMAIL", "SMS")):
    for ch in channels:
        conn.execute(
            "INSERT INTO notifications (user_id, channel, subject, body, send_after) "
            "VALUES (?,?,?,?,?)", (user_id, ch, subject, body, send_after))


def queue_appointment_messages(conn, appt_id, hours_before=24):
    a = conn.execute(
        "SELECT a.*, u.full_name AS doctor_name FROM appointments a "
        "JOIN users u ON u.id = a.doctor_id WHERE a.id = ?", (appt_id,)).fetchone()
    when = datetime.strptime(a["slot_start"], FMT)
    now = datetime.now().strftime(FMT)
    queue(conn, a["patient_id"], "Appointment confirmed",
          f"Booking #{appt_id} with {a['doctor_name']} at {a['slot_start']}.", now,
          channels=("EMAIL",))
    reminder_at = (when - timedelta(hours=hours_before)).strftime(FMT)
    queue(conn, a["patient_id"], "Appointment reminder",
          f"Reminder: booking #{appt_id} with {a['doctor_name']} at {a['slot_start']}.",
          max(reminder_at, now))


def dispatch_due(conn, channels, now=None):
    """Send every unsent message whose send_after has passed. Returns count sent."""
    now = (now or datetime.now()).strftime(FMT)
    due = conn.execute(
        "SELECT n.*, u.email, u.phone FROM notifications n JOIN users u ON u.id = n.user_id "
        "WHERE n.sent_at IS NULL AND n.send_after <= ?", (now,)).fetchall()
    for n in due:
        to = n["email"] if n["channel"] == "EMAIL" else n["phone"]
        channels[n["channel"]].send(to, n["subject"], n["body"])
        conn.execute("UPDATE notifications SET sent_at = ? WHERE id = ?", (now, n["id"]))
    return len(due)
