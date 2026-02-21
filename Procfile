web: gunicorn config.wsgi:application
release: python manage.py migrate --settings=config.settings.production --noinput && python manage.py create_superuser --settings=config.settings.production || true
