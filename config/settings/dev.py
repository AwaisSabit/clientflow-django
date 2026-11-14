"""Development settings: DEBUG on, localhost only, insecure defaults flagged."""
import os

from .base import *  # noqa: F401,F403

DEBUG = True
ALLOWED_HOSTS = ["127.0.0.1", "localhost"]
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "unsafe-dev-only-key")

# Print emails (such as password reset links) to the console in dev.
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
