web: gunicorn config.wsgi:application
release: bash -c "DJANGO_SETTINGS_MODULE=config.settings.production python manage.py migrate --noinput; DJANGO_SETTINGS_MODULE=config.settings.production python manage.py create_superuser; DJANGO_SETTINGS_MODULE=config.settings.production python manage.py check_users"
