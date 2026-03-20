#!/bin/sh
set -eu

mkdir -p /data/logs
chmod 0777 /data/logs || true
exec "$@"
