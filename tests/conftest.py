"""Pytest configuration and fixtures."""
import sys
from pathlib import Path
import importlib.util

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def load_rate_limit_module():
    """Load the rate-limit-sleep module (handles hyphenated filename)."""
    module_path = project_root / "rate-limit-sleep.py"
    spec = importlib.util.spec_from_file_location("rate_limit_sleep", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# Load the module once for all tests
rate_limit_sleep = load_rate_limit_module()
