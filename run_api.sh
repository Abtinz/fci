#!/usr/bin/env sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$SCRIPT_DIR"

exec python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 "$@"
