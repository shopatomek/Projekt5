#!/bin/sh
set -e

# tworzy bazę tylko jeśli jeszcze nie istnieje
if ! psql -U "$POSTGRES_USER" -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='metabase_app'" | grep -q 1; then
  createdb -U "$POSTGRES_USER" metabase_app
fi

psql -U "$POSTGRES_USER" -d postgres -c "GRANT ALL PRIVILEGES ON DATABASE metabase_app TO \"$POSTGRES_USER\";"