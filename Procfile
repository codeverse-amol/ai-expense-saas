web: gunicorn config.wsgi:application
release: python manage.py migrate --settings=config.settings.production --noinput || true
