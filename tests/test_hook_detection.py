"""Tests for rate limit detection patterns."""
import pytest
import json
import re

from conftest import rate_limit_sleep


def check_rate_limit_detection(message: str) -> bool:
    """Helper to check if a message would be detected as rate limit."""
    rate_limit_indicators = [
        r"hit your limit",
        r"usage limit",
        r"stop\s+and\s+wait\s+for\s+(?:limit|rate)",
        r"rate\s*limit",
    ]
    return any(re.search(p, message, re.IGNORECASE) for p in rate_limit_indicators)


def extract_time_and_tz(message: str) -> tuple:
    """Helper to extract time and timezone from a message."""
    time_pattern = r"(\d{1,2}(?::\d{2})?\s*(?:am|pm))\s*\(([^)]+)\)"
    match = re.search(time_pattern, message, re.IGNORECASE)
    if match:
        return match.group(1), match.group(2)
    return None, None


class TestRateLimitPatterns:
    """Test rate limit message detection."""

    def test_hit_your_limit(self):
        """Test 'hit your limit' pattern."""
        msg = "hit your limit resets 4am (America/Los_Angeles)"
        assert check_rate_limit_detection(msg)

    def test_usage_limit(self):
        """Test 'usage limit' pattern."""
        msg = "usage limit reached, resets 4am (America/Los_Angeles)"
        assert check_rate_limit_detection(msg)

    def test_stop_and_wait_for_limit(self):
        """Test 'stop and wait for limit' menu option pattern."""
        msg = "Stop and wait for limit to reset 4am (America/Los_Angeles)"
        assert check_rate_limit_detection(msg)

    def test_stop_and_wait_for_rate(self):
        """Test 'stop and wait for rate' pattern."""
        msg = "Stop and wait for rate to reset 4am (UTC)"
        assert check_rate_limit_detection(msg)

    def test_rate_limit_pattern(self):
        """Test 'rate limit' pattern."""
        msg = "rate limit exceeded, try again at 4am (UTC)"
        assert check_rate_limit_detection(msg)

    def test_ratelimit_no_space(self):
        """Test 'ratelimit' without space."""
        msg = "ratelimit exceeded at 4am (UTC)"
        assert check_rate_limit_detection(msg)

    def test_case_insensitive(self):
        """Test that detection is case insensitive."""
        msg = "HIT YOUR LIMIT resets 4am (UTC)"
        assert check_rate_limit_detection(msg)


class TestNonRateLimitPatterns:
    """Test that non-rate-limit messages are not detected."""

    def test_user_requested_stop(self):
        """Test user requested stop is not detected."""
        msg = "user requested"
        assert not check_rate_limit_detection(msg)

    def test_normal_completion(self):
        """Test normal completion is not detected."""
        msg = "task completed successfully"
        assert not check_rate_limit_detection(msg)

    def test_error_stop(self):
        """Test error stop is not detected."""
        msg = "error occurred during execution"
        assert not check_rate_limit_detection(msg)

    def test_empty_message(self):
        """Test empty message is not detected."""
        msg = ""
        assert not check_rate_limit_detection(msg)


class TestTimeExtraction:
    """Test time and timezone extraction from messages."""

    def test_simple_extraction(self):
        """Test extraction from standard message."""
        msg = "hit your limit resets 4am (America/Los_Angeles)"
        time_str, tz_str = extract_time_and_tz(msg)
        assert time_str == "4am"
        assert tz_str == "America/Los_Angeles"

    def test_extraction_with_colon_time(self):
        """Test extraction with colon format time."""
        msg = "limit resets 11:30pm (Europe/London)"
        time_str, tz_str = extract_time_and_tz(msg)
        assert time_str == "11:30pm"
        assert tz_str == "Europe/London"

    def test_extraction_from_json_string(self):
        """Test extraction from JSON-stringified dict."""
        data = {"stop_reason": "hit your limit resets 4am (America/Los_Angeles)"}
        msg = str(data)
        time_str, tz_str = extract_time_and_tz(msg)
        assert time_str == "4am"
        assert tz_str == "America/Los_Angeles"

    def test_menu_option_extraction(self):
        """Test extraction from menu option format."""
        msg = "Stop and wait for limit to reset 4am (America/Los_Angeles)"
        time_str, tz_str = extract_time_and_tz(msg)
        assert time_str == "4am"
        assert tz_str == "America/Los_Angeles"

    def test_no_time_found(self):
        """Test when no time is present."""
        msg = "user requested stop"
        time_str, tz_str = extract_time_and_tz(msg)
        assert time_str is None
        assert tz_str is None


class TestFullInputProcessing:
    """Test processing of full JSON input structures."""

    def test_json_with_stop_reason(self):
        """Test processing JSON with stop_reason field."""
        data = {"stop_reason": "hit your limit resets 4am (America/Los_Angeles)"}
        msg = str(data)
        assert check_rate_limit_detection(msg)
        time_str, tz_str = extract_time_and_tz(msg)
        assert time_str == "4am"

    def test_nested_json_structure(self):
        """Test processing nested JSON structure."""
        data = {
            "event": "stop",
            "details": {
                "reason": "hit your limit resets 11pm (UTC)"
            }
        }
        msg = str(data)
        assert check_rate_limit_detection(msg)
        time_str, tz_str = extract_time_and_tz(msg)
        assert time_str == "11pm"
        assert tz_str == "UTC"
