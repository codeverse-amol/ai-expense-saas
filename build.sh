#!/bin/bash
# Render build script - ensures database is configured before running migrations

set -e  # Exit on any error

echo "==> Installing dependencies..."
pip install -r requirements.txt

echo "==> Collecting static files..."
python manage.py collectstatic --noinput

echo "==> Build complete!"
