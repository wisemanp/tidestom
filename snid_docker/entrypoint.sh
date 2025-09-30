#!/bin/bash
set -e

# Fix ownership of mounted volume
chown -R sniduser:snidgroup /snid_api_runs
mkdir -p /media/snid_template_options
chown -R sniduser:snidgroup /media/snid_template_options

# Execute the main container command (uvicorn)
# exec su -s /bin/bash sniduser -c "$@"
exec "$@"

