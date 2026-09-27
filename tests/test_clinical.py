"""TC-16..TC-20: e-prescription, labs, tasks, notifications, engagement."""
from datetime import datetime, timedelta

import pytest

from smartclinic.services import (booking, ehr, engagement, labs, notifications,
                                  prescriptions, tasks)
from conftest import TOMORROW


def test_tc16_prescription_blocked_on_allergy(conn, ids):
    ehr.upsert_record(conn, ids["pat"], ids["doc"], allergies="Penicillin")
    with pytest.raises(prescriptions.AllergyConflict):
        prescriptions.create(conn, ids["doc"], ids["pat"], "Penicillin V", "500mg")
    assert conn.execute("SELECT COUNT(*) FROM prescriptions").fetchone()[0] == 0


def test_tc17_prescription_override_is_audited(conn, ids):
    ehr.upsert_record(conn, ids["pat"], ids["doc"], allergies="Penicillin")
    rx = prescriptions.create(conn, ids["doc"], ids["pat"], "Penicillin V", "500mg",
                              "Harbour Street Pharmacy", override=True)
    act = conn.execute("SELECT action FROM audit_log WHERE entity='prescription' AND entity_id=?",
                       (rx,)).fetchone()["action"]
    assert act == "RX_OVERRIDE"


def test_tc18_lab_result_linked_and_critical_alert_raised(conn, ids):
    labs.record(conn, ids["pat"], "Potassium", "6.9 mmol/L", "CRITICAL", ids["nurse"],
                notify_doctor_id=ids["doc"])
    rec = ehr.full_record(conn, ids["pat"], ids["doc"])
    assert rec["labs"][0]["result"] == "6.9 mmol/L"
    alert = conn.execute("SELECT * FROM notifications WHERE user_id=?", (ids["doc"],)).fetchone()
    assert alert["channel"] == "SMS" and "Critical" in alert["subject"]


def test_tc19_task_lifecycle_and_ownership(conn, ids):
    t = tasks.assign(conn, "Vitals check", ids["nurse"], ids["doc"], ids["pat"])
    with pytest.raises(PermissionError):
        tasks.advance(conn, t, ids["rec"])
    assert tasks.advance(conn, t, ids["nurse"]) == "IN_PROGRESS"
    assert tasks.advance(conn, t, ids["nurse"]) == "DONE"
    with pytest.raises(ValueError):
        tasks.assign(conn, "x", ids["pat"], ids["doc"])  # patients cannot receive tasks


def test_tc20_reminders_dispatched_when_due(conn, ids):
    booking.book(conn, ids["pat"], ids["doc"], f"{TOMORROW} 16:00")
    email, sms = notifications.ConsoleChannel(), notifications.ConsoleChannel()
    chans = {"EMAIL": email, "SMS": sms}
    sent_now = notifications.dispatch_due(conn, chans)
    assert sent_now >= 1 and email.sent[0][1] == "Appointment confirmed"
    later = datetime.strptime(f"{TOMORROW} 16:00", "%Y-%m-%d %H:%M") - timedelta(hours=1)
    notifications.dispatch_due(conn, chans, now=later)
    assert any("Reminder" in m[2] for m in sms.sent)
    assert notifications.dispatch_due(conn, chans, now=later) == 0  # never sent twice


def test_cancel_removes_pending_reminders(conn, ids):
    a = booking.book(conn, ids["pat"], ids["doc"], f"{TOMORROW} 16:15")
    booking.cancel(conn, a, ids["pat"])
    pending = conn.execute("SELECT COUNT(*) FROM notifications WHERE sent_at IS NULL "
                           "AND body LIKE ?", (f"%#{a}%",)).fetchone()[0]
    assert pending == 0


def test_loyalty_points_and_package(conn, ids):
    for n in range(5):
        engagement.award_visit(conn, ids["pat"], n)
    assert engagement.balance(conn, ids["pat"]) == 50
    assert engagement.tier(50) == "Silver" and engagement.eligible_for_package(conn, ids["pat"])
