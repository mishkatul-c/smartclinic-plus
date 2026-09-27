"""Task assignment module (FR-06) for nurses and support staff."""
from ..db import audit, transaction

NEXT = {"TODO": "IN_PROGRESS", "IN_PROGRESS": "DONE"}


def assign(conn, title, assigned_to, created_by, patient_id=None, due_at=None):
    role = conn.execute("SELECT role FROM users WHERE id=?", (assigned_to,)).fetchone()
    if role is None or role["role"] not in ("nurse", "receptionist"):
        raise ValueError("Tasks can only be assigned to nurses or reception staff")
    with transaction(conn):
        cur = conn.execute(
            "INSERT INTO tasks (title, patient_id, assigned_to, created_by, due_at) "
            "VALUES (?,?,?,?,?)", (title, patient_id, assigned_to, created_by, due_at))
        audit(conn, created_by, "TASK_ASSIGN", "task", cur.lastrowid)
    return cur.lastrowid


def advance(conn, task_id, actor_id):
    t = conn.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
    if t is None or t["assigned_to"] != actor_id:
        raise PermissionError("You can only update tasks assigned to you")
    if t["status"] not in NEXT:
        raise ValueError("Task already complete")
    with transaction(conn):
        conn.execute("UPDATE tasks SET status=? WHERE id=?", (NEXT[t["status"]], task_id))
        audit(conn, actor_id, "TASK_" + NEXT[t["status"]], "task", task_id)
    return NEXT[t["status"]]


def for_user(conn, user_id):
    return conn.execute(
        "SELECT t.*, p.full_name AS patient_name FROM tasks t LEFT JOIN users p "
        "ON p.id=t.patient_id WHERE t.assigned_to=? ORDER BY t.status DESC, t.due_at",
        (user_id,)).fetchall()
