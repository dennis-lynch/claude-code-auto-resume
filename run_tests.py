#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.9"
# dependencies = [
#     "pytest",
# ]
# ///
"""Test runner using uv inline script metadata."""
import subprocess
import sys
from pathlib import Path

script_dir = Path(__file__).parent
sys.exit(subprocess.call(
    [sys.executable, "-m", "pytest", "tests/", "-v"] + sys.argv[1:],
    cwd=script_dir
))
