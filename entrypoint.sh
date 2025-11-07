#!/bin/bash
set -e

echo "Waiting for API config file..."
while [ ! -f /snid_api_runs/snid_template_options/subtypes.txt ]; do
    sleep 1
done

echo "Copying subtype options into static..."
mkdir -p /app/static/config
cp /snid_api_runs/snid_template_options/subtypes.txt /app/static/config/

echo "Running collectstatic..."
python manage.py collectstatic --noinput

echo "Starting Gunicorn..."
exec gunicorn tidestom.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 4 \
    --worker-class gevent \
    --log-level debug \
    --capture-output \
    --enable-stdio-inheritance

