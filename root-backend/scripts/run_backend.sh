#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
flask --app bootstrap:create_app run --host "${APP_HOST:-0.0.0.0}" --port "${APP_PORT:-4001}"
