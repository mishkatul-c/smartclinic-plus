"""Load realistic demo data. Usage: python -m smartclinic.seed  (password for all: Clinic#2026)"""
import random
from datetime import date, datetime, timedelta

from . import create_app
from .db import get_db
from .security import hash_password
from .services import ehr, engagement, labs, tasks

PW = "Clinic#2026"
FMT = "%Y-%m-%d %H:%M"


def seed(conn):
    random.seed(7)
    pw = hash_password(PW)

    def user(email, name, role, phone):
        cur = conn.execute("INSERT INTO users (email, full_name, role, phone, password_hash) "
                           "VALUES (?,?,?,?,?)", (email, name, role, phone, pw))
        return cur.lastrowid

    docs = [user("dr.nguyen@smartclinic.test", "Dr Linh Nguyen", "doctor", "0400 111 201"),
            user("dr.patel@smartclinic.test", "Dr Arjun Patel", "doctor", "0400 111 202"),
            user("dr.okafor@smartclinic.test", "Dr Grace Okafor", "doctor", "0400 111 203")]
    for d, sp in zip(docs, ["General Practice", "Cardiology", "Paediatrics"]):
        conn.execute("INSERT INTO doctors (user_id, specialty) VALUES (?,?)", (d, sp))
    nurse = user("nurse.kim@smartclinic.test", "Hana Kim", "nurse", "0400 111 301")
    user("nurse.brown@smartclinic.test", "Liam Brown", "nurse", "0400 111 302")
    user("reception@smartclinic.test", "Sofia Rossi", "receptionist", "0400 111 401")
    admin = user("admin@smartclinic.test", "Clinic Manager", "admin", "0400 111 501")
    names = ["Olivia Smith", "Noah Williams", "Ava Jones", "Jack Taylor", "Mia Wilson",
             "Ethan Martin", "Chloe Lee", "Lucas White", "Zara Ahmed", "Ben Clarke"]
    pats = [user(f"{n.split()[0].lower()}@mail.test", n, "patient", f"0412 000 {100+i}")
            for i, n in enumerate(names)]

    # six weeks of history -> analytics has something to learn from
    today = date.today()
    for back in range(42, 0, -1):
        d = today - timedelta(days=back)
        if d.weekday() >= 5:
            continue
        for doc in docs:
            for hour in range(9, 17):
                busy = 0.85 if hour in (9, 10, 16) else 0.45
                for minute in (0, 15, 30, 45):
                    if random.random() < busy:
                        slot = datetime(d.year, d.month, d.day, hour, minute)
                        arrive = slot - timedelta(minutes=random.randint(-5, 10))
                        called = arrive + timedelta(minutes=random.randint(4, 28))
                        conn.execute(
                            "INSERT INTO appointments (patient_id, doctor_id, slot_start, status, "
                            "checked_in_at, called_at, completed_at) VALUES (?,?,?,?,?,?,?)",
                            (random.choice(pats), doc, slot.strftime(FMT), "COMPLETED",
                             arrive.strftime(FMT), called.strftime(FMT),
                             (called + timedelta(minutes=14)).strftime(FMT)))

    # today's clinic for Dr Nguyen and Dr Patel
    t = today.isoformat()
    now = datetime.now()
    plan = [(pats[0], docs[0], "09:00"), (pats[1], docs[0], "09:15"), (pats[2], docs[0], "09:30"),
            (pats[3], docs[0], "09:45"), (pats[4], docs[0], "10:00"), (pats[5], docs[0], "10:15"),
            (pats[6], docs[1], "09:00"), (pats[7], docs[1], "09:30"), (pats[8], docs[0], "11:00"),
            (pats[9], docs[0], "11:15")]
    for i, (p, d, hm) in enumerate(plan):
        status, ci, tri = "BOOKED", None, 3
        if i < 5 or i == 6:
            status, ci = "CHECKED_IN", f"{t} {hm}"
        if i == 3:
            tri = 1
        if i == 1:
            ci = f"{t} 09:40"  # late arrival
        conn.execute("INSERT INTO appointments (patient_id, doctor_id, slot_start, status, "
                     "checked_in_at, triage_level) VALUES (?,?,?,?,?,?)",
                     (p, d, f"{t} {hm}", status, ci, tri))
    conn.execute("UPDATE doctors SET running_delay = 10 WHERE user_id = ?", (docs[0],))
    tomorrow = (today + timedelta(days=1)).isoformat()
    conn.execute("INSERT INTO appointments (patient_id, doctor_id, slot_start) VALUES (?,?,?)",
                 (pats[0], docs[1], f"{tomorrow} 14:30"))
    _ = now

    ehr.upsert_record(conn, pats[0], docs[0], "1988-04-12",
                      "Type 2 diabetes (diet controlled). Appendectomy 2009.", "Penicillin, Latex")
    ehr.upsert_record(conn, pats[1], docs[0], "1975-09-30", "Hypertension.", "")
    ehr.add_consultation(conn, pats[0], docs[0], "Upper respiratory tract infection",
                         "Viral. Fluids and rest; review if fever persists beyond 5 days.")
    labs.record(conn, pats[0], "HbA1c", "6.4 %", "ABNORMAL", nurse)
    labs.record(conn, pats[0], "Full blood count", "Within reference range", "NORMAL", nurse)
    tasks.assign(conn, "Vitals check before consult", nurse, docs[0], pats[0], f"{t} 09:05")
    tasks.assign(conn, "Prepare fasting blood test kit", nurse, docs[0], pats[1], f"{t} 10:00")
    tasks.assign(conn, "ECG setup", nurse, docs[1], pats[6], f"{t} 09:20")
    for n in range(4):
        engagement.award_visit(conn, pats[0], 1000 + n)
    _ = admin


if __name__ == "__main__":
    import os
    path = os.environ.get("SMARTCLINIC_DATABASE", "smartclinic.db")
    if os.path.exists(path):
        os.remove(path)
    app = create_app()
    with app.app_context():
        seed(get_db())
    print(f"Seeded {path}. Log in with any *@smartclinic.test account, password {PW}")
