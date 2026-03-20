#!/usr/bin/env sh
set -eu

mkdir -p "${CONPOT_LOG_DIR:-/data/logs}" "${CONPOT_CONFIG_DIR:-/data/configs}"
exec python /opt/conpot/app.py
