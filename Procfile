web: gunicorn config.wsgi:application
release: python manage.py migrate --noinput; python manage.py create_superuser
