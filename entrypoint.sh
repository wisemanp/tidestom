#!/bin/bash
set -e

if [[ ! -v LOCAL_MODE ]]; then
	echo "Waiting for API config file..."
	while [ ! -f /snid_api_runs/snid_template_options/subtypes.txt ]; do
		sleep 1
	done

	echo "Copying subtype options into static..."
	mkdir -p /app/static/config
	cp /snid_api_runs/snid_template_options/subtypes.txt /app/static/config/
fi

echo "Running collectstatic..."
python manage.py collectstatic --noinput


if [[ ! -v LOCAL_MODE ]]; then
	echo "Starting Gunicorn..."
	exec gunicorn tidestom.wsgi:application \
		--bind 0.0.0.0:8000 \
		--workers 4 \
		--worker-class gevent \
		--log-level debug \
		--capture-output \
		--enable-stdio-inheritance
fi
