#!/bin/sh
set -e

echo "→ Running database migrations…"
flask --app app db upgrade

echo "→ Starting: $*"
exec "$@"
