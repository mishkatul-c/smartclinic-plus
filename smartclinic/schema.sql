-- SmartClinic+ schema (SQLite dialect for local dev/test; see docs/schema_postgresql.sql for production)
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    email         TEXT NOT NULL UNIQUE,
    full_name     TEXT NOT NULL,
    phone         TEXT,
    role          TEXT NOT NULL CHECK (role IN ('patient','doctor','nurse','receptionist','admin')),
    password_hash TEXT NOT NULL,
    created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS doctors (
    user_id        INTEGER PRIMARY KEY REFERENCES users(id),
    specialty      TEXT NOT NULL,
    slot_minutes   INTEGER NOT NULL DEFAULT 15,
    day_start      TEXT NOT NULL DEFAULT '09:00',
    day_end        TEXT NOT NULL DEFAULT '17:00',
    running_delay  INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS appointments (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id   INTEGER NOT NULL REFERENCES users(id),
    doctor_id    INTEGER NOT NULL REFERENCES doctors(user_id),
    slot_start   TEXT NOT NULL,
    status       TEXT NOT NULL DEFAULT 'BOOKED'
                 CHECK (status IN ('BOOKED','CHECKED_IN','IN_CONSULT','COMPLETED','CANCELLED','NO_SHOW')),
    reason       TEXT,
    triage_level INTEGER NOT NULL DEFAULT 3 CHECK (triage_level BETWEEN 1 AND 3),
    checked_in_at TEXT,
    called_at     TEXT,
    completed_at  TEXT,
    version      INTEGER NOT NULL DEFAULT 1,
    created_at   TEXT NOT NULL DEFAULT (datetime('now'))
);
-- Core concurrency guarantee: one active appointment per doctor per slot.
CREATE UNIQUE INDEX IF NOT EXISTS ux_active_slot
    ON appointments (doctor_id, slot_start)
    WHERE status IN ('BOOKED','CHECKED_IN','IN_CONSULT');

CREATE TABLE IF NOT EXISTS health_records (
    patient_id         INTEGER PRIMARY KEY REFERENCES users(id),
    date_of_birth      TEXT,
    medical_history_enc TEXT,
    allergies_enc       TEXT,
    updated_at         TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS consultations (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    appointment_id INTEGER REFERENCES appointments(id),
    patient_id     INTEGER NOT NULL REFERENCES users(id),
    doctor_id      INTEGER NOT NULL REFERENCES users(id),
    diagnosis_enc  TEXT,
    notes_enc      TEXT,
    created_at     TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS prescriptions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id  INTEGER NOT NULL REFERENCES users(id),
    doctor_id   INTEGER NOT NULL REFERENCES users(id),
    medication  TEXT NOT NULL,
    dosage      TEXT NOT NULL,
    pharmacy    TEXT,
    status      TEXT NOT NULL DEFAULT 'SENT' CHECK (status IN ('SENT','DISPENSED','CANCELLED')),
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS lab_results (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id  INTEGER NOT NULL REFERENCES users(id),
    test_name   TEXT NOT NULL,
    result_enc  TEXT NOT NULL,
    flag        TEXT NOT NULL DEFAULT 'NORMAL' CHECK (flag IN ('NORMAL','ABNORMAL','CRITICAL')),
    recorded_by INTEGER REFERENCES users(id),
    recorded_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS tasks (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    title       TEXT NOT NULL,
    patient_id  INTEGER REFERENCES users(id),
    assigned_to INTEGER NOT NULL REFERENCES users(id),
    created_by  INTEGER NOT NULL REFERENCES users(id),
    status      TEXT NOT NULL DEFAULT 'TODO' CHECK (status IN ('TODO','IN_PROGRESS','DONE')),
    due_at      TEXT,
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS notifications (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL REFERENCES users(id),
    channel     TEXT NOT NULL CHECK (channel IN ('EMAIL','SMS')),
    subject     TEXT NOT NULL,
    body        TEXT NOT NULL,
    send_after  TEXT NOT NULL,
    sent_at     TEXT
);

CREATE TABLE IF NOT EXISTS loyalty_ledger (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id  INTEGER NOT NULL REFERENCES users(id),
    points      INTEGER NOT NULL,
    reason      TEXT NOT NULL,
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS audit_log (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER,
    action     TEXT NOT NULL,
    entity     TEXT NOT NULL,
    entity_id  INTEGER,
    at         TEXT NOT NULL DEFAULT (datetime('now'))
);
