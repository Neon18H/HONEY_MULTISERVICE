#!/usr/bin/env sh
set -eu

mkdir -p "${MAILONEY_LOG_DIR:-/data/logs}"
exec python /opt/mailoney/app.py
