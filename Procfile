web: gunicorn config.wsgi:application
release: python manage.py migrate --noinput 2>&1 | head -20; python manage.py create_superuser 2>&1 | head -20; echo "Release completed"
