"""TC-21..TC-22: operational dashboard and predictive insights (FR-10, FR-11)."""
from smartclinic.services import analytics


def _visit(conn, ids, slot, arrive, called):
    conn.execute("INSERT INTO appointments (patient_id, doctor_id, slot_start, status, "
                 "checked_in_at, called_at) VALUES (?,?,?,?,?,?)",
                 (ids["pat"], ids["doc"], slot, "COMPLETED", arrive, called))


def test_tc21_average_wait_and_utilisation(conn, ids):
    _visit(conn, ids, "2030-05-06 09:00", "2030-05-06 09:00", "2030-05-06 09:10")
    _visit(conn, ids, "2030-05-06 09:15", "2030-05-06 09:15", "2030-05-06 09:35")
    assert analytics.average_wait_minutes(conn) == 15.0
    util = analytics.doctor_utilisation(conn, "2030-05-06")[0]
    assert util["booked"] == 2 and util["capacity"] == 32 and util["utilisation"] == 6.2


def test_tc22_forecast_weights_recent_weeks(conn, ids):
    # Mondays: week 1 has 4 x 09:00 arrivals, week 2 has 2 -> smoothed (a=0.5) = 3
    for d, n in (("2030-05-06", 4), ("2030-05-13", 2)):
        for m in range(n):
            _visit(conn, ids, f"{d} 09:{m*15:02d}", f"{d} 09:00", f"{d} 09:05")
    fc = analytics.forecast_peak_hours(conn, weekday=0)
    assert fc[9] == 3.0
    assert analytics.staffing_recommendation(fc, patients_per_staff_hour=2)[9] == 2
