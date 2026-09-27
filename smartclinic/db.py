"""Database access layer: connections, schema bootstrap and explicit transactions.

SQLite is used for local development and automated tests. The same SQL (plus the
PostgreSQL DDL in docs/schema_postgresql.sql) targets PostgreSQL in production, where
the partial unique index and SERIALIZABLE/IMMEDIATE transactions give the same
double-booking guarantee.
"""
import sqlite3
from contextlib import contextmanager
from importlib import resources

from flask import current_app, g


def connect(path):
    conn = sqlite3.connect(path, timeout=10, isolation_level=None,
                           check_same_thread=False, detect_types=0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    if path != ":memory:":
        conn.execute("PRAGMA journal_mode = WAL")
    return conn


def get_db():
    if "db" not in g:
        shared = current_app.config.get("_SHARED_CONN")
        g.db = shared if shared is not None else connect(current_app.config["DATABASE"])
    return g.db


def close_db(_exc=None):
    db = g.pop("db", None)
    if db is not None and current_app.config.get("_SHARED_CONN") is None:
        db.close()


def init_schema(conn):
    sql = resources.files("smartclinic").joinpath("schema.sql").read_text()
    conn.executescript(sql)


@contextmanager
def transaction(conn):
    """Run a block inside BEGIN IMMEDIATE ... COMMIT, rolling back on any error.

    BEGIN IMMEDIATE takes the write lock up front, so two concurrent bookings are
    serialised rather than both reading 'slot free' and both writing.
    """
    conn.execute("BEGIN IMMEDIATE")
    try:
        yield conn
    except Exception:
        conn.execute("ROLLBACK")
        raise
    else:
        conn.execute("COMMIT")


def audit(conn, user_id, action, entity, entity_id=None):
    conn.execute(
        "INSERT INTO audit_log (user_id, action, entity, entity_id) VALUES (?,?,?,?)",
        (user_id, action, entity, entity_id),
    )
