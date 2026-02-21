web: gunicorn config.wsgi:application
release: bash -c 'if [ -z "$DATABASE_URL" ]; then echo "⚠ WARNING: DATABASE_URL not set - skipping migrations. Setup PostgreSQL on Render first!"; else python manage.py migrate --noinput 2>&1; python manage.py create_superuser 2>&1; fi'
