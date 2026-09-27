"""TC-12..TC-15: RBAC, encryption at rest, authentication, audit (FR-09, NFR-03, NFR-08)."""
import pytest

from smartclinic.security import PERMISSIONS, can
from smartclinic.services import ehr
from conftest import login


@pytest.mark.parametrize("key,path,expected", [
    ("pat", "/doctor", 403), ("pat", "/admin/analytics", 403), ("nurse", "/admin/analytics", 403),
    ("rec", "/patients/1", 403), ("doc", "/doctor", 200), ("admin", "/admin/analytics", 200),
    ("nurse", "/tasks", 200), ("rec", "/front-desk", 200), ("pat", "/patient/", 200),
])
def test_tc12_role_based_access(app, key, path, expected):
    client = app.test_client()
    login(client, key)
    assert client.get(path).status_code == expected


def test_tc13_anonymous_user_redirected_to_login(app):
    r = app.test_client().get("/doctor")
    assert r.status_code == 302 and "/login" in r.headers["Location"]


def test_tc14_clinical_text_encrypted_at_rest(conn, ids):
    ehr.upsert_record(conn, ids["pat"], ids["doc"], "1990-01-01", "Asthma", "Penicillin")
    raw = conn.execute("SELECT medical_history_enc, allergies_enc FROM health_records").fetchone()
    assert "Asthma" not in raw[0] and "Penicillin" not in raw[1]
    assert ehr.allergies(conn, ids["pat"]) == ["penicillin"]


def test_tc15_record_reads_are_audited(conn, ids):
    ehr.full_record(conn, ids["pat"], ids["doc"])
    row = conn.execute("SELECT * FROM audit_log WHERE action='EHR_READ'").fetchone()
    assert row["user_id"] == ids["doc"] and row["entity_id"] == ids["pat"]


def test_wrong_password_rejected(app):
    r = app.test_client().post("/login", data={"email": "doc@t.test", "password": "nope"})
    assert b"incorrect" in r.data


def test_passwords_are_hashed(conn):
    assert all(r[0].startswith(("scrypt:", "pbkdf2:"))
               for r in conn.execute("SELECT password_hash FROM users"))


def test_least_privilege_only_doctors_prescribe():
    assert PERMISSIONS["prescription:create"] == {"doctor"}
    assert not can("nurse", "prescription:create")


def test_security_headers_present(app):
    r = app.test_client().get("/login")
    assert r.headers["X-Frame-Options"] == "DENY"
