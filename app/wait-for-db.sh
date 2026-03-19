#!/bin/bash

set -e

host="$1"
port="$2"
shift 2
cmd="$@"

echo "Waiting for database at $host:$port..."

until PGPASSWORD=$DB_PASSWORD psql -h "$host" -p "$port" -U "$DB_USER" -d "$DB_NAME" -c '\q' 2>/dev/null; do
  >&2 echo "Database is unavailable - sleeping"
  sleep 1
done

>&2 echo "Database is up - executing command"
exec $cmd
