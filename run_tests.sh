#!/bin/bash
# Runs tests using uv's inline script metadata
exec uv run "$(dirname "$0")/run_tests.py" "$@"
