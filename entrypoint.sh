#!/bin/sh
set -eu
if [ "$#" -gt 0 ]; then
  exec "$@"
fi
exec uvicorn jobpilot.api.main:app --host 0.0.0.0 --port "${PORT:-8080}"
