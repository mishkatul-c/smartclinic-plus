"""Operational dashboard and predictive insights (FR-10, FR-11)."""
import math
from collections import defaultdict
from datetime import datetime

FMT = "%Y-%m-%d %H:%M"


def average_wait_minutes(conn):
    rows = conn.execute("SELECT checked_in_at, called_at FROM appointments "
                        "WHERE checked_in_at IS NOT NULL AND called_at IS NOT NULL").fetchall()
    if not rows:
        return 0.0
    waits = [(datetime.strptime(r["called_at"], FMT) - datetime.strptime(r["checked_in_at"], FMT))
             .total_seconds() / 60 for r in rows]
    return round(sum(waits) / len(waits), 1)


def doctor_utilisation(conn, day):
    """Share of each doctor's bookable minutes that were booked on a given day."""
    out = []
    for d in conn.execute("SELECT d.*, u.full_name FROM doctors d JOIN users u ON u.id=d.user_id"):
        h0, m0 = map(int, d["day_start"].split(":"))
        h1, m1 = map(int, d["day_end"].split(":"))
        capacity = ((h1 * 60 + m1) - (h0 * 60 + m0)) // d["slot_minutes"]
        booked = conn.execute(
            "SELECT COUNT(*) FROM appointments WHERE doctor_id=? AND slot_start LIKE ? "
            "AND status NOT IN ('CANCELLED')", (d["user_id"], f"{day}%")).fetchone()[0]
        out.append({"doctor": d["full_name"], "booked": booked, "capacity": capacity,
                    "utilisation": round(100 * booked / capacity, 1) if capacity else 0.0})
    return out


def forecast_peak_hours(conn, weekday, alpha=0.5):
    """Exponentially smoothed forecast of arrivals per hour for a weekday (0 = Monday).

    Each past week's hourly count is blended into the forecast, so recent weeks weigh
    more than old ones. Returns {hour: expected_patients}.
    """
    weekly = defaultdict(lambda: defaultdict(int))
    for r in conn.execute("SELECT slot_start FROM appointments WHERE status != 'CANCELLED'"):
        t = datetime.strptime(r["slot_start"], FMT)
        if t.weekday() == weekday:
            weekly[t.isocalendar()[:2]][t.hour] += 1
    forecast = {}
    for week in sorted(weekly):
        for hour in range(7, 20):
            obs = weekly[week].get(hour, 0)
            forecast[hour] = obs if hour not in forecast else alpha * obs + (1 - alpha) * forecast[hour]
    return {h: round(v, 2) for h, v in forecast.items() if v > 0}


def staffing_recommendation(forecast, patients_per_staff_hour=4):
    return {h: max(1, math.ceil(v / patients_per_staff_hour)) for h, v in forecast.items()}
