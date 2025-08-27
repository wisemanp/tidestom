#!/bin/bash
set -e

# Fix ownership of mounted volume
chown -R sniduser:snidgroup /snid_api_runs

# Execute the main container command (uvicorn)
exec "$@"

