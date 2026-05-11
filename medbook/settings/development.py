"""
MedBook — development settings.

Uses SQLite by default so the app runs without a MySQL server.
Console email backend prints emails to stdout.
"""

from .base import *  # noqa: F401, F403

DEBUG = True

# ──────────────────────────────────────────────
# Database — SQLite for local dev (zero config)
# ──────────────────────────────────────────────
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# ──────────────────────────────────────────────
# Email — console backend (prints to stdout)
# ──────────────────────────────────────────────
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
