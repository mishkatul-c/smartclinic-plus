"""TC-09..TC-11: smart queue ordering and wait estimates (FR-02)."""
from smartclinic.services import queue

DAY = "2030-05-06"


def _appt(conn, ids, hm, arrived, triage=3, patient="pat"):
    cur = conn.execute(
        "INSERT INTO appointments (patient_id, doctor_id, slot_start, status, checked_in_at, "
        "triage_level) VALUES (?,?,?,?,?,?)",
        (ids[patient], ids["doc"], f"{DAY} {hm}", "CHECKED_IN", f"{DAY} {arrived}", triage))
    return cur.lastrowid


def test_tc09_emergency_jumps_queue(conn, ids):
    a = _appt(conn, ids, "09:00", "08:55")
    b = _appt(conn, ids, "09:30", "09:28", triage=1, patient="pat2")
    order = [e["id"] for e in queue.current_queue(conn, ids["doc"])]
    assert order == [b, a]


def test_tc10_late_arrival_goes_behind_on_time_patients(conn, ids):
    late = _appt(conn, ids, "09:00", "09:40")           # 40 min late
    on_time = _appt(conn, ids, "09:15", "09:10", patient="pat2")
    order = [e["id"] for e in queue.current_queue(conn, ids["doc"], grace_minutes=15)]
    assert order == [on_time, late]


def test_tc11_wait_estimate_includes_running_delay(conn, ids):
    _appt(conn, ids, "09:00", "08:55")
    _appt(conn, ids, "09:15", "09:10", patient="pat2")
    queue.set_delay(conn, ids["doc"], 20)
    waits = [e["est_wait_min"] for e in queue.current_queue(conn, ids["doc"])]
    assert waits == [20, 35]  # 0 x 15 + 20, 1 x 15 + 20


def test_call_next_moves_patient_into_consult(conn, ids):
    a = _appt(conn, ids, "09:00", "08:55")
    called = queue.call_next(conn, ids["doc"], ids["doc"])
    assert called["id"] == a
    assert queue.current_queue(conn, ids["doc"]) == []
