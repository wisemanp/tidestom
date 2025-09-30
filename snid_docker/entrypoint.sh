#!/bin/bash
set -ex  # <- print commands

echo "ENTRYPOINT START: user=$(whoami), args=$@"
chown -R sniduser:snidgroup /snid_api_runs
mkdir -p /media/snid_template_options
chown -R sniduser:snidgroup /media/snid_template_options

if [ "$#" -eq 0 ]; then
  echo "No command provided, falling back to uvicorn"
  exec uvicorn run_snid:app --host 0.0.0.0 --port 8000
else
  echo "Executing command: $@"
  exec "$@"
fi
