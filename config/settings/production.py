from .base import *
import os

DEBUG = False

ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "").split(",")

# 🔐 Required for Render (proxy SSL)
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# 🔐 Session & CSRF Security
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"

# 🔐 Required for POST login on custom domains
CSRF_TRUSTED_ORIGINS = [
    "https://expense-manager-d7x5.onrender.com",
]

# ❗ Disable this temporarily (Render already forces HTTPS)
SECURE_SSL_REDIRECT = False