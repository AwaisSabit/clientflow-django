"""Production settings: DEBUG off, secret key mandatory, secure cookies."""
import os

from .base import *  # noqa: F401,F403

DEBUG = False

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "")
if not SECRET_KEY:
    raise ValueError("DJANGO_SECRET_KEY must be set in production")
if len(SECRET_KEY) < 50:
    raise ValueError(
        "DJANGO_SECRET_KEY must be at least 50 characters long in "
        "production — a short key leaves Django's signed data exposed"
    )

ALLOWED_HOSTS = [
    h.strip()
    for h in os.environ.get("DJANGO_ALLOWED_HOSTS", "").split(",")
    if h.strip()
]
if not ALLOWED_HOSTS:
    raise ValueError("DJANGO_ALLOWED_HOSTS must be set in production")

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
# No JavaScript in this project reads the CSRF cookie (forms carry
# the token with {% csrf_token %}), so the cookie can be hidden from
# scripts as well.
CSRF_COOKIE_HTTPONLY = True
SECURE_SSL_REDIRECT = os.environ.get("DJANGO_SECURE_SSL_REDIRECT", "True").lower() in {
    "1",
    "true",
    "yes",
}

# Strict Transport Security: once a browser has seen the header it
# only talks to this site over HTTPS for a year, including subdomains.
# Preload is left off — joining the preload list is hard to undo.
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = False

# Refuse to guess a content type for responses, and do not send the
# full page address to other sites when following a link.
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
