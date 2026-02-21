import os
print("DJANGO_ENV:", os.environ.get("DJANGO_ENV"))
env = os.environ.get("DJANGO_ENV", "development")

if env == "production":
    from .production import *
else:
    from .development import *