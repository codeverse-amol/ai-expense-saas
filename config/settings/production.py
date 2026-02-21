from .base import *
import os

DEBUG = False

# --------------------------------------------------
# ALLOWED HOSTS & DOMAINS
# --------------------------------------------------
ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

# Ensure Render domain is included
render_domain = os.environ.get("RENDER_EXTERNAL_HOSTNAME", "")
if render_domain:
    ALLOWED_HOSTS.append(render_domain)

# --------------------------------------------------
# SECURITY HEADERS & HTTPS
# --------------------------------------------------
# 🔐 Required for Render (proxy SSL)
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_X_FORWARDED_HOST = True

# 🔐 Session & CSRF Security
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"

# Increase session timeout (default is 2 weeks)
SESSION_COOKIE_AGE = 1209600  # 2 weeks in seconds
SESSION_EXPIRE_AT_BROWSER_CLOSE = False

# 🔐 CSRF Trusted Origins for POST requests
CSRF_TRUSTED_ORIGINS = [
    "https://*.onrender.com",
    f"https://{render_domain}" if render_domain else "",
]
CSRF_TRUSTED_ORIGINS = [origin for origin in CSRF_TRUSTED_ORIGINS if origin]

# --------------------------------------------------
# SECURITY SETTINGS
# --------------------------------------------------
SECURE_SSL_REDIRECT = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# --------------------------------------------------
# AUTHENTICATION (OVERRIDE - Ensure it's set)
# --------------------------------------------------
AUTHENTICATION_BACKENDS = [
    "apps.users.backends.EmailAuthenticationBackend",
    "django.contrib.auth.backends.ModelBackend",  # Fallback
]
