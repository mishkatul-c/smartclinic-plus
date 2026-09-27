-- SmartClinic+ production schema for PostgreSQL 16 (mirrors smartclinic/schema.sql)
CREATE EXTENSION IF NOT EXISTS citext;
-- application connects as a least-privilege role
CREATE ROLE smartclinic_app LOGIN;
CREATE TYPE user_role AS ENUM ('patient','doctor','nurse','receptionist','admin');
CREATE TYPE appt_status AS ENUM ('BOOKED','CHECKED_IN','IN_CONSULT','COMPLETED','CANCELLED','NO_SHOW');

CREATE TABLE users (
  id            BIGSERIAL PRIMARY KEY,
  email         CITEXT NOT NULL UNIQUE,
  full_name     TEXT NOT NULL,
  phone         TEXT,
  role          user_role NOT NULL,
  password_hash TEXT NOT NULL,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE doctors (
  user_id       BIGINT PRIMARY KEY REFERENCES users(id),
  specialty     TEXT NOT NULL,
  slot_minutes  SMALLINT NOT NULL DEFAULT 15 CHECK (slot_minutes IN (10,15,20,30)),
  day_start     TIME NOT NULL DEFAULT '09:00',
  day_end       TIME NOT NULL DEFAULT '17:00',
  running_delay SMALLINT NOT NULL DEFAULT 0
);

CREATE TABLE appointments (
  id            BIGSERIAL PRIMARY KEY,
  patient_id    BIGINT NOT NULL REFERENCES users(id),
  doctor_id     BIGINT NOT NULL REFERENCES doctors(user_id),
  slot_start    TIMESTAMPTZ NOT NULL,
  status        appt_status NOT NULL DEFAULT 'BOOKED',
  reason        TEXT,
  triage_level  SMALLINT NOT NULL DEFAULT 3 CHECK (triage_level BETWEEN 1 AND 3),
  checked_in_at TIMESTAMPTZ,
  called_at     TIMESTAMPTZ,
  completed_at  TIMESTAMPTZ,
  version       INTEGER NOT NULL DEFAULT 1,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);
-- The double-booking guarantee (NFR-01): at most one active appointment per doctor per slot.
CREATE UNIQUE INDEX ux_active_slot ON appointments (doctor_id, slot_start)
  WHERE status IN ('BOOKED','CHECKED_IN','IN_CONSULT');
CREATE INDEX ix_appt_patient ON appointments (patient_id, slot_start);

CREATE TABLE health_records (
  patient_id          BIGINT PRIMARY KEY REFERENCES users(id),
  date_of_birth       DATE,
  medical_history_enc TEXT,   -- Fernet ciphertext (application-level encryption)
  allergies_enc       TEXT,
  updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE consultations (
  id             BIGSERIAL PRIMARY KEY,
  appointment_id BIGINT REFERENCES appointments(id),
  patient_id     BIGINT NOT NULL REFERENCES users(id),
  doctor_id      BIGINT NOT NULL REFERENCES users(id),
  diagnosis_enc  TEXT,
  notes_enc      TEXT,
  created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE prescriptions (
  id         BIGSERIAL PRIMARY KEY,
  patient_id BIGINT NOT NULL REFERENCES users(id),
  doctor_id  BIGINT NOT NULL REFERENCES users(id),
  medication TEXT NOT NULL,
  dosage     TEXT NOT NULL,
  pharmacy   TEXT,
  status     TEXT NOT NULL DEFAULT 'SENT' CHECK (status IN ('SENT','DISPENSED','CANCELLED')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE lab_results (
  id          BIGSERIAL PRIMARY KEY,
  patient_id  BIGINT NOT NULL REFERENCES users(id),
  test_name   TEXT NOT NULL,
  result_enc  TEXT NOT NULL,
  flag        TEXT NOT NULL DEFAULT 'NORMAL' CHECK (flag IN ('NORMAL','ABNORMAL','CRITICAL')),
  recorded_by BIGINT REFERENCES users(id),
  recorded_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE tasks (
  id          BIGSERIAL PRIMARY KEY,
  title       TEXT NOT NULL,
  patient_id  BIGINT REFERENCES users(id),
  assigned_to BIGINT NOT NULL REFERENCES users(id),
  created_by  BIGINT NOT NULL REFERENCES users(id),
  status      TEXT NOT NULL DEFAULT 'TODO' CHECK (status IN ('TODO','IN_PROGRESS','DONE')),
  due_at      TIMESTAMPTZ,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE notifications (
  id         BIGSERIAL PRIMARY KEY,
  user_id    BIGINT NOT NULL REFERENCES users(id),
  channel    TEXT NOT NULL CHECK (channel IN ('EMAIL','SMS')),
  subject    TEXT NOT NULL,
  body       TEXT NOT NULL,
  send_after TIMESTAMPTZ NOT NULL,
  sent_at    TIMESTAMPTZ
);
CREATE INDEX ix_outbox_due ON notifications (send_after) WHERE sent_at IS NULL;

CREATE TABLE loyalty_ledger (
  id         BIGSERIAL PRIMARY KEY,
  patient_id BIGINT NOT NULL REFERENCES users(id),
  points     INTEGER NOT NULL,
  reason     TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE audit_log (
  id        BIGSERIAL PRIMARY KEY,
  user_id   BIGINT,
  action    TEXT NOT NULL,
  entity    TEXT NOT NULL,
  entity_id BIGINT,
  at        TIMESTAMPTZ NOT NULL DEFAULT now()
);
-- audit rows are append-only for the application role
REVOKE UPDATE, DELETE ON audit_log FROM smartclinic_app;
