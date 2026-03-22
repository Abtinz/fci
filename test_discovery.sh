#!/usr/bin/env sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$SCRIPT_DIR"

exec python -m unittest tests.test_discovery tests.test_discovery_node tests.test_source_store "$@"
