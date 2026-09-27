from datetime import datetime, timedelta

import pytest

from smartclinic import create_app
from smartclinic.config import TestConfig
from smartclinic.db import get_db
from smartclinic.security import hash_password

TOMORROW = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")


def make_users(conn):
    pw = hash_password("pw")
    ids = {}
    for key, role in [("pat", "patient"), ("pat2", "patient"), ("doc", "doctor"),
                      ("nurse", "nurse"), ("rec", "receptionist"), ("admin", "admin")]:
        cur = conn.execute("INSERT INTO users (email, full_name, role, phone, password_hash) "
                           "VALUES (?,?,?,?,?)", (f"{key}@t.test", key.title(), role, "0400", pw))
        ids[key] = cur.lastrowid
    conn.execute("INSERT INTO doctors (user_id, specialty) VALUES (?, 'GP')", (ids["doc"],))
    return ids


@pytest.fixture
def app():
    app = create_app(TestConfig, SECRET_KEY="test")
    with app.app_context():
        app.ids = make_users(get_db())
        yield app


@pytest.fixture
def conn(app):
    return get_db()


@pytest.fixture
def ids(app):
    return app.ids


def login(client, key):
    return client.post("/login", data={"email": f"{key}@t.test", "password": "pw"})
