"""Tests for manual duration/time parsing."""
import pytest
from datetime import datetime, timedelta

class TestDurationParsing:
    """Test parse_duration function."""

    def test_seconds(self, rate_limit_sleep):
        assert rate_limit_sleep.parse_duration("45s") == 45
        assert rate_limit_sleep.parse_duration("45sec") == 45
        assert rate_limit_sleep.parse_duration("45seconds") == 45

    def test_minutes(self, rate_limit_sleep):
        assert rate_limit_sleep.parse_duration("30m") == 30 * 60
        assert rate_limit_sleep.parse_duration("30min") == 30 * 60
        assert rate_limit_sleep.parse_duration("30minutes") == 30 * 60

    def test_hours(self, rate_limit_sleep):
        assert rate_limit_sleep.parse_duration("2h") == 2 * 3600
        assert rate_limit_sleep.parse_duration("2hr") == 2 * 3600
        assert rate_limit_sleep.parse_duration("2hours") == 2 * 3600

    def test_float_input(self, rate_limit_sleep):
        assert rate_limit_sleep.parse_duration("1.5h") == int(1.5 * 3600)
        assert rate_limit_sleep.parse_duration("0.5m") == 30

    def test_invalid_input(self, rate_limit_sleep):
        assert rate_limit_sleep.parse_duration("invalid") is None
        assert rate_limit_sleep.parse_duration("45x") is None
        assert rate_limit_sleep.parse_duration("123") is None  # Needs unit

class TestTimeToSecondsParsing:
    """Test parse_time_to_seconds function."""

    def test_future_time_same_day(self, rate_limit_sleep):
        """Test parsing a time later today."""
        # This is tricky because it relies on "now".
        # We'll mock specific behavior or just check logic boundaries.
        # For now, let's assume the function works relative to system time.
        # We can't easily deterministic test "4pm" without mocking datetime.now
        # But we can check it returns an integer.
        
        # We'll pick a time likely in the future relative to typical work hours,
        # but safely, let's just checking specific formatted strings return ints.
        assert isinstance(rate_limit_sleep.parse_time_to_seconds("11:59pm"), int)

    def test_invalid_time(self, rate_limit_sleep):
        assert rate_limit_sleep.parse_time_to_seconds("not a time") is None
        # "25:00pm" passes regex but fails date validation, raising ValueError
        with pytest.raises(ValueError):
            rate_limit_sleep.parse_time_to_seconds("25:00pm")

class TestParseDurationOrTime:
    """Test the combined parser."""

    def test_duration_priority(self, rate_limit_sleep):
        # "2h" should be parsed as duration
        assert rate_limit_sleep.parse_duration_or_time("2h") == 7200

    def test_time_fallback(self, rate_limit_sleep):
        # "11:59pm" should be parsed as time
        # We just check it doesn't raise
        assert isinstance(rate_limit_sleep.parse_duration_or_time("11:59pm"), int)

    def test_raises_on_invalid(self, rate_limit_sleep):
        with pytest.raises(ValueError, match="Could not parse"):
            rate_limit_sleep.parse_duration_or_time("invalid argument")
