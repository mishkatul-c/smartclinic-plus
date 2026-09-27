"""TC-08: 20 simultaneous requests for one slot -> exactly one booking (NFR-01, NFR-02)."""
import threading

from smartclinic import create_app
from smartclinic.db import connect
from smartclinic.services import booking
from conftest import TOMORROW, make_users


def test_tc08_concurrent_bookings_single_winner(tmp_path):
    path = str(tmp_path / "race.db")
    app = create_app(DATABASE=path, SECRET_KEY="t")
    setup = connect(path)
    ids = make_users(setup)
    setup.close()

    results, barrier = [], threading.Barrier(20)

    def attempt():
        conn = connect(path)
        with app.app_context():
            barrier.wait()  # release all threads at once to maximise contention
            try:
                booking.book(conn, ids["pat"], ids["doc"], f"{TOMORROW} 09:00")
                results.append("ok")
            except booking.SlotTakenError:
                results.append("taken")
        conn.close()

    threads = [threading.Thread(target=attempt) for _ in range(20)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    check = connect(path)
    active = check.execute("SELECT COUNT(*) FROM appointments WHERE slot_start=?",
                           (f"{TOMORROW} 09:00",)).fetchone()[0]
    assert results.count("ok") == 1
    assert results.count("taken") == 19
    assert active == 1


def test_database_index_is_last_line_of_defence(tmp_path):
    """Even a raw INSERT that skips the service layer cannot create a double booking."""
    import sqlite3
    import pytest
    path = str(tmp_path / "idx.db")
    create_app(DATABASE=path, SECRET_KEY="t")
    conn = connect(path)
    ids = make_users(conn)
    sql = "INSERT INTO appointments (patient_id, doctor_id, slot_start) VALUES (?,?,?)"
    conn.execute(sql, (ids["pat"], ids["doc"], f"{TOMORROW} 10:00"))
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(sql, (ids["pat2"], ids["doc"], f"{TOMORROW} 10:00"))
