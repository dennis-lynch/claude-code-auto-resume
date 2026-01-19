"""Tests for time parsing functionality."""
import pytest
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


class TestTimeFormatParsing:
    """Test various time format strings."""

    def test_simple_am(self, rate_limit_sleep):
        """Test simple AM time like '4am'."""
        result = rate_limit_sleep.parse_reset_time("4am", "UTC")
        assert result.hour == 4
        assert result.minute == 0

    def test_simple_pm(self, rate_limit_sleep):
        """Test simple PM time like '11pm'."""
        result = rate_limit_sleep.parse_reset_time("11pm", "UTC")
        assert result.hour == 23
        assert result.minute == 0

    def test_colon_format_am(self, rate_limit_sleep):
        """Test colon format like '4:00am'."""
        result = rate_limit_sleep.parse_reset_time("4:00am", "UTC")
        assert result.hour == 4
        assert result.minute == 0

    def test_colon_format_pm_with_minutes(self, rate_limit_sleep):
        """Test colon format like '11:30pm'."""
        result = rate_limit_sleep.parse_reset_time("11:30pm", "UTC")
        assert result.hour == 23
        assert result.minute == 30

    def test_midnight(self, rate_limit_sleep):
        """Test midnight (12am)."""
        result = rate_limit_sleep.parse_reset_time("12am", "UTC")
        assert result.hour == 0
        assert result.minute == 0

    def test_noon(self, rate_limit_sleep):
        """Test noon (12pm)."""
        result = rate_limit_sleep.parse_reset_time("12pm", "UTC")
        assert result.hour == 12
        assert result.minute == 0

    def test_almost_midnight(self, rate_limit_sleep):
        """Test 11:59pm."""
        result = rate_limit_sleep.parse_reset_time("11:59pm", "UTC")
        assert result.hour == 23
        assert result.minute == 59

    def test_whitespace_between(self, rate_limit_sleep):
        """Test time with space like '4 am'."""
        result = rate_limit_sleep.parse_reset_time("4 am", "UTC")
        assert result.hour == 4
        assert result.minute == 0

    def test_uppercase_am_pm(self, rate_limit_sleep):
        """Test uppercase AM/PM like '4AM'."""
        result = rate_limit_sleep.parse_reset_time("4AM", "UTC")
        assert result.hour == 4
        assert result.minute == 0


class TestTimezoneHandling:
    """Test timezone parsing and handling."""

    def test_los_angeles(self, rate_limit_sleep):
        """Test America/Los_Angeles timezone."""
        result = rate_limit_sleep.parse_reset_time("4am", "America/Los_Angeles")
        assert result.tzinfo == ZoneInfo("America/Los_Angeles")

    def test_new_york(self, rate_limit_sleep):
        """Test America/New_York timezone."""
        result = rate_limit_sleep.parse_reset_time("4am", "America/New_York")
        assert result.tzinfo == ZoneInfo("America/New_York")

    def test_london(self, rate_limit_sleep):
        """Test Europe/London timezone."""
        result = rate_limit_sleep.parse_reset_time("4am", "Europe/London")
        assert result.tzinfo == ZoneInfo("Europe/London")

    def test_tokyo(self, rate_limit_sleep):
        """Test Asia/Tokyo timezone."""
        result = rate_limit_sleep.parse_reset_time("4am", "Asia/Tokyo")
        assert result.tzinfo == ZoneInfo("Asia/Tokyo")

    def test_utc(self, rate_limit_sleep):
        """Test UTC timezone."""
        result = rate_limit_sleep.parse_reset_time("4am", "UTC")
        assert result.tzinfo == ZoneInfo("UTC")

    def test_space_normalization(self, rate_limit_sleep):
        """Test that spaces in timezone are converted to underscores."""
        # "America/Los Angeles" should become "America/Los_Angeles"
        result = rate_limit_sleep.parse_reset_time("4am", "America/Los Angeles")
        assert result.tzinfo == ZoneInfo("America/Los_Angeles")


class TestPastTimeHandling:
    """Test that past times are handled correctly (add a day)."""

    def test_past_time_adds_day(self, rate_limit_sleep):
        """Test that a time in the past results in next day."""
        tz = ZoneInfo("UTC")
        now = datetime.now(tz)

        # Parse a time that's 1 hour ago
        past_hour = (now.hour - 1) % 24
        if past_hour < 12:
            time_str = f"{past_hour}am" if past_hour != 0 else "12am"
        else:
            time_str = f"{past_hour - 12}pm" if past_hour != 12 else "12pm"

        result = rate_limit_sleep.parse_reset_time(time_str, "UTC")

        # Result should be in the future
        assert result > now

    def test_future_time_same_day(self, rate_limit_sleep):
        """Test that a time in the future stays on same day."""
        tz = ZoneInfo("UTC")
        now = datetime.now(tz)

        # Parse a time that's 2 hours from now
        future_hour = (now.hour + 2) % 24
        if future_hour < 12:
            time_str = f"{future_hour}am" if future_hour != 0 else "12am"
        else:
            adjusted_hour = future_hour - 12 if future_hour != 12 else 12
            time_str = f"{adjusted_hour}pm"

        result = rate_limit_sleep.parse_reset_time(time_str, "UTC")

        # Result should be in the future
        assert result > now
        # And within 24 hours (not next day, unless we're close to midnight)
        assert result - now < timedelta(days=1)
