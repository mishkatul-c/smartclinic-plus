"""Application configuration. Secrets are read from the environment in production."""
import os


class Config:
    SECRET_KEY = os.environ.get("SMARTCLINIC_SECRET_KEY", "dev-only-change-me")
    DATABASE = os.environ.get("SMARTCLINIC_DATABASE", "smartclinic.db")
    # Fernet key used for field-level encryption of clinical data (AES-128-CBC + HMAC-SHA256).
    ENCRYPTION_KEY = os.environ.get(
        "SMARTCLINIC_ENCRYPTION_KEY", "q2m3Gd0bM7Qk3o4dQ2xHq5b3yqRr6rj3v1xB9wz8Q0M="
    )
    REMINDER_HOURS_BEFORE = 24
    LATE_ARRIVAL_GRACE_MIN = 15
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    TESTING = False


class TestConfig(Config):
    TESTING = True
    DATABASE = ":memory:"
