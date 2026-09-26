#!/usr/bin/env bash
# Build script for Render.com
set -euo pipefail

echo "==> Installing dependencies"
pip install -r requirements.txt

echo "==> Collecting static files"
python manage.py collectstatic --noinput

echo "==> Running migrations"
python manage.py migrate --noinput

# Optionally seed demo data on first deploy
if [ "${SEED_DEMO:-0}" = "1" ]; then
  echo "==> Seeding demo data"
  python manage.py seed_demo || true
fi

echo "==> Build complete"
