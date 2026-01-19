#!/bin/bash
# Test runner for claude-code-auto-resume
# Uses uv for isolated environment management

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.test-venv"

echo "Running tests for claude-code-auto-resume..."
echo ""

# Check for uv
if ! command -v uv &> /dev/null; then
    echo "Error: 'uv' is not installed."
    echo "Install it with: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating test virtual environment..."
    uv venv "$VENV_DIR"
fi

# Activate virtual environment
source "$VENV_DIR/bin/activate"

# Install pytest if not present
if ! python -c "import pytest" 2>/dev/null; then
    echo "Installing pytest..."
    uv pip install pytest
fi

echo ""
echo "Running pytest..."
echo "========================================"

# Run tests with verbose output
cd "$SCRIPT_DIR"
python -m pytest tests/ -v "$@"

TEST_EXIT_CODE=$?

echo ""
echo "========================================"
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo "All tests passed!"
else
    echo "Some tests failed."
fi

exit $TEST_EXIT_CODE
