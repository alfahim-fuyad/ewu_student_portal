#!/usr/bin/env bash
# Build script for Render.com
set -euo pipefail

echo "==> Installing dependencies"
pip install -r requirements.txt

echo "==> Running migrations"
python manage.py migrate --noinput

echo "==> Seeding demo data"
python manage.py seed_demo

echo "==> Collecting static files"
python manage.py collectstatic --noinput

echo "==> Build complete"