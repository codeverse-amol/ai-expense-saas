from .base import *
import os

DEBUG = True

ALLOWED_HOSTS = []

# Only override HOST to localhost if DATABASE_URL is not set (i.e., local development)
if not os.environ.get("DATABASE_URL"):
    DATABASES["default"]["HOST"] = "localhost"