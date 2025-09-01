#!/bin/sh
set -e

host="$1"
shift

until pg_isready -h "$host" -U "$POSTGRES_USER" -d "$POSTGRES_DB"; do
  >&2 echo "Postgres is unavailable - sleeping"
  sleep 2
done

>&2 echo "Postgres is up - executing command"
exec "$@"

