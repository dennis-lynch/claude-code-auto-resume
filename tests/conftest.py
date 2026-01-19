"""Pytest configuration and fixtures."""
import sys
from pathlib import Path
import importlib.util
import pytest

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def _load_rate_limit_module():
    """Load the rate-limit-sleep module (handles hyphenated filename)."""
    module_path = project_root / "rate-limit-sleep.py"
    spec = importlib.util.spec_from_file_location("rate_limit_sleep", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def rate_limit_sleep():
    """Fixture providing access to the rate-limit-sleep module."""
    return _load_rate_limit_module()
