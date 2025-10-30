#!/usr/bin/env bash
set -e

echo "Creating logs directory..."
mkdir -p /tmp/logs

echo "Starting QC Tool..."
exec gunicorn --bind 0.0.0.0:$PORT --timeout 600 --workers 2 --log-level info 'src.backend.app:create_app()'
