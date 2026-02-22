from .base import *
import os

DEBUG = True

# Allow localhost and 127.0.0.1 for development
ALLOWED_HOSTS = ["*"] if DEBUG else []

# Only override HOST to localhost if DATABASE_URL is not set (i.e., local development)
if not os.environ.get("DATABASE_URL"):
    DATABASES["default"]["HOST"] = "localhost"