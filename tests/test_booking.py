"""TC-01..TC-07: appointment booking, rescheduling, cancellation (FR-01)."""
from datetime import datetime

import pytest

from smartclinic.services import booking
from conftest import TOMORROW


def test_tc01_book_valid_slot(conn, ids):
    appt = booking.book(conn, ids["pat"], ids["doc"], f"{TOMORROW} 09:00")
    row = conn.execute("SELECT status FROM appointments WHERE id=?", (appt,)).fetchone()
    assert row["status"] == "BOOKED"


def test_tc02_booked_slot_disappears_from_availability(conn, ids):
    before = booking.available_slots(conn, ids["doc"], TOMORROW)
    booking.book(conn, ids["pat"], ids["doc"], f"{TOMORROW} 09:15")
    after = booking.available_slots(conn, ids["doc"], TOMORROW)
    assert f"{TOMORROW} 09:15" in before and f"{TOMORROW} 09:15" not in after
    assert len(after) == len(before) - 1


def test_tc03_double_booking_rejected(conn, ids):
    booking.book(conn, ids["pat"], ids["doc"], f"{TOMORROW} 10:00")
    with pytest.raises(booking.SlotTakenError):
        booking.book(conn, ids["pat2"], ids["doc"], f"{TOMORROW} 10:00")


@pytest.mark.parametrize("slot,msg", [
    ("2020-01-01 09:00", "future"),
    (f"{TOMORROW} 07:00", "working hours"),
    (f"{TOMORROW} 09:07", "align"),
    ("not-a-date", "formatted"),
])
def test_tc04_invalid_slots_rejected(conn, ids, slot, msg):
    with pytest.raises(booking.BookingError, match=msg):
        booking.book(conn, ids["pat"], ids["doc"], slot)


def test_tc05_cancel_frees_slot(conn, ids):
    appt = booking.book(conn, ids["pat"], ids["doc"], f"{TOMORROW} 11:00")
    booking.cancel(conn, appt, ids["pat"])
    assert f"{TOMORROW} 11:00" in booking.available_slots(conn, ids["doc"], TOMORROW)
    booking.book(conn, ids["pat2"], ids["doc"], f"{TOMORROW} 11:00")  # rebookable


def test_tc06_reschedule_moves_appointment(conn, ids):
    appt = booking.book(conn, ids["pat"], ids["doc"], f"{TOMORROW} 12:00")
    booking.reschedule(conn, appt, f"{TOMORROW} 12:30", ids["pat"])
    row = conn.execute("SELECT slot_start, version FROM appointments WHERE id=?", (appt,)).fetchone()
    assert row["slot_start"] == f"{TOMORROW} 12:30" and row["version"] == 2


def test_tc07_reschedule_into_taken_slot_rejected(conn, ids):
    a = booking.book(conn, ids["pat"], ids["doc"], f"{TOMORROW} 13:00")
    booking.book(conn, ids["pat2"], ids["doc"], f"{TOMORROW} 13:15")
    with pytest.raises(booking.SlotTakenError):
        booking.reschedule(conn, a, f"{TOMORROW} 13:15", ids["pat"])


def test_booking_is_audited(conn, ids):
    appt = booking.book(conn, ids["pat"], ids["doc"], f"{TOMORROW} 14:00",
                        now=datetime.now())
    log = conn.execute("SELECT action FROM audit_log WHERE entity_id=?", (appt,)).fetchall()
    assert [r["action"] for r in log] == ["BOOK"]
