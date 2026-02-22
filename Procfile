web: gunicorn config.wsgi:application
release: DJANGO_SETTINGS_MODULE=config.settings.production python manage.py migrate --noinput
