web: gunicorn config.wsgi:application
release: DJANGO_SETTINGS_MODULE=config.settings.production python manage.py migrate --noinput 2>&1 ; DJANGO_SETTINGS_MODULE=config.settings.production python manage.py create_superuser 2>&1 ; true
