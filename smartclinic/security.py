"""Authentication, role-based access control (FR-09) and field encryption (NFR-03)."""
import secrets
from functools import wraps

from cryptography.fernet import Fernet, InvalidToken
from flask import abort, current_app, g, redirect, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

# Permission matrix: which roles may perform which action (least privilege).
PERMISSIONS = {
    "appointment:book":      {"patient", "receptionist"},
    "appointment:view_all":  {"doctor", "nurse", "receptionist", "admin"},
    "queue:manage":          {"nurse", "receptionist", "doctor"},
    "ehr:read":              {"doctor", "nurse"},
    "ehr:write":             {"doctor"},
    "prescription:create":   {"doctor"},
    "lab:record":            {"nurse", "doctor"},
    "task:assign":           {"doctor", "admin"},
    "task:update":           {"nurse", "receptionist"},
    "analytics:view":        {"admin"},
}


def can(role, permission):
    return role in PERMISSIONS.get(permission, set())


def hash_password(raw):
    return generate_password_hash(raw)


def verify_password(hashed, raw):
    return check_password_hash(hashed, raw)


def _fernet():
    return Fernet(current_app.config["ENCRYPTION_KEY"].encode())


def encrypt(value):
    if value is None:
        return None
    return _fernet().encrypt(value.encode()).decode()


def decrypt(token):
    if token is None:
        return None
    try:
        return _fernet().decrypt(token.encode()).decode()
    except InvalidToken:
        return "[unreadable]"


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if g.get("user") is None:
            return redirect(url_for("auth.login", next=request.path))
        return view(*args, **kwargs)
    return wrapped


def requires(permission):
    """Decorator enforcing the RBAC matrix on a route."""
    def decorator(view):
        @wraps(view)
        @login_required
        def wrapped(*args, **kwargs):
            if not can(g.user["role"], permission):
                abort(403)
            return view(*args, **kwargs)
        return wrapped
    return decorator


def csrf_token():
    if "_csrf" not in session:
        session["_csrf"] = secrets.token_urlsafe(32)
    return session["_csrf"]


def check_csrf():
    if request.method == "POST" and not current_app.config.get("TESTING"):
        expected = session.get("_csrf")
        if not expected or not secrets.compare_digest(request.form.get("_csrf", ""), expected):
            abort(400, "Invalid form token")
