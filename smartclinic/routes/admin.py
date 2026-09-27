from datetime import date, timedelta

from flask import Blueprint, render_template, request

from ..db import get_db
from ..security import requires
from ..services import analytics

bp = Blueprint("admin", __name__, url_prefix="/admin")


@bp.route("/analytics", endpoint="analytics")
@requires("analytics:view")
def analytics_view():
    conn = get_db()
    day = request.args.get("day", date.today().isoformat())
    target = date.today() + timedelta(days=1)
    fc = analytics.forecast_peak_hours(conn, target.weekday())
    staff = analytics.staffing_recommendation(fc)
    peak = max(fc.values()) if fc else 1
    return render_template("analytics.html", day=day, avg_wait=analytics.average_wait_minutes(conn),
                           util=analytics.doctor_utilisation(conn, day), forecast=fc, staff=staff,
                           peak=peak, target=target.strftime("%A %d %b"))
