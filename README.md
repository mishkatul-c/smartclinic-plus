# SmartClinic+

An intelligent outpatient clinic management system: online booking with real-time availability and guaranteed
no double bookings, a smart triage-aware queue, encrypted electronic health records, e-prescriptions with an
allergy safety check, nurse task assignment, lab results, automated reminders, an operational dashboard with
peak-hour forecasting, and a patient loyalty scheme.

SENG205 Software Engineering, Kent Institute Australia, T2 2026 — Assessment 3 prototype.

## Quick start
```bash
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m smartclinic.seed        # creates smartclinic.db with six weeks of demo data
python run.py                     # http://127.0.0.1:5000
```
Password for every demo account: `Clinic#2026`

| Role | Email | Try this |
|---|---|---|
| Patient | olivia@mail.test | Book a slot, cancel it, see loyalty points |
| Doctor | dr.nguyen@smartclinic.test | Call next patient, prescribe Penicillin V to Olivia (allergy block) |
| Nurse | nurse.kim@smartclinic.test | Start and complete assigned tasks |
| Receptionist | reception@smartclinic.test | Check patients in as routine, urgent or emergency |
| Clinic manager | admin@smartclinic.test | Wait time, utilisation, tomorrow's staffing forecast |

## Tests and quality gates
```bash
flake8 smartclinic tests docs/tools
pytest --cov=smartclinic          # 47 tests, ~94% statement coverage
```
The CI workflow (`.github/workflows/ci.yml`) runs both on Python 3.11 and 3.12 for every pull request and fails
below 80% coverage. `tests/test_concurrency.py` fires 20 simultaneous bookings at one slot and asserts exactly one wins.

## Architecture
Layered: Flask blueprints (presentation) → services (business rules, one transaction per use case) → data layer.
Security is cross-cutting: a permission matrix enforced by `@requires(...)`, CSRF tokens, hashed passwords, and
Fernet field encryption for clinical free text. See `docs/diagrams/`.

The prototype runs on SQLite so it works anywhere with no setup; `docs/schema_postgresql.sql` is the production
schema. All SQL is isolated in the service layer and `db.py`, which is the only module that changes for PostgreSQL.

## Requirement traceability
| Requirement | Code | Tests |
|---|---|---|
| FR-01 Booking / reschedule / cancel | services/booking.py | test_booking.py |
| NFR-01/02 No double booking, transactions | booking.py, schema.sql (ux_active_slot) | test_concurrency.py |
| FR-02 Smart queue | services/queue.py | test_queue.py |
| FR-03 Notifications | services/notifications.py | test_clinical.py |
| FR-04 Doctor dashboard | routes/clinical.py | test_journey.py |
| FR-05 E-prescription | services/prescriptions.py | test_clinical.py |
| FR-06 Task assignment | services/tasks.py | test_clinical.py |
| FR-07 EHR, NFR-03 encryption | services/ehr.py, security.py | test_security.py |
| FR-08 Labs | services/labs.py | test_clinical.py |
| FR-09 Role-based access | security.py | test_security.py |
| FR-10/11 Dashboard, forecast | services/analytics.py | test_analytics.py |
| FR-12 Engagement | services/engagement.py | test_clinical.py |

## Project management
Backlog: `docs/product_backlog.csv` (import into GitHub Projects or Jira). Team roles and decision procedure:
`docs/team_charter.md`. Requirement prioritisation: `python docs/tools/ahp_prioritisation.py`.
How to publish with each member's own commits: `docs/TEAM_GIT_GUIDE.md`.

## Team
Mishkatul Abedin Chowdhury (K241095) · Humayra Nushrat (K241086) · Md Mahamudul Amin Maruf (K241071) · Md Muhi Uddin Mukit (K240999)
