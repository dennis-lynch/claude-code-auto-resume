#!/usr/bin/env python3
"""
Claude Code hook to handle rate limit by sleeping until reset time.
"""
import sys
import json
import re
import time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from pathlib import Path

LOG_FILE = Path.home() / ".claude" / "hooks" / "rate-limit.log"
BUFFER_MINUTES = 5

def log(message: str):
    """Append timestamped message to log file."""
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a") as f:
        f.write(f"[{timestamp}] {message}\n")

def parse_reset_time(time_str: str, tz_str: str) -> datetime:
    """Parse reset time like '4am' or '11:30pm' with timezone."""
    # Normalize timezone string (handle common variations)
    tz_str = tz_str.strip().replace(" ", "_")
    tz = ZoneInfo(tz_str)

    # Parse time - handle formats: "4am", "4:00am", "11:30pm"
    time_str = time_str.lower().strip()

    if ":" in time_str:
        # Format: "4:00am" or "11:30pm"
        match = re.match(r"(\d{1,2}):(\d{2})\s*(am|pm)", time_str)
        hour = int(match.group(1))
        minute = int(match.group(2))
        period = match.group(3)
    else:
        # Format: "4am" or "11pm"
        match = re.match(r"(\d{1,2})\s*(am|pm)", time_str)
        hour = int(match.group(1))
        minute = 0
        period = match.group(2)

    # Convert to 24-hour
    if period == "pm" and hour != 12:
        hour += 12
    elif period == "am" and hour == 12:
        hour = 0

    # Get current time in that timezone
    now = datetime.now(tz)
    reset = now.replace(hour=hour, minute=minute, second=0, microsecond=0)

    # If reset time is in the past, it's for tomorrow
    if reset <= now:
        reset += timedelta(days=1)

    return reset

def main():
    try:
        # Read stdin
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        input_data = {}

    # Convert entire input to string to search for rate limit pattern
    message = str(input_data)

    # Rate limit indicator patterns
    rate_limit_indicators = [
        r"hit your limit",
        r"usage limit",
        r"stop\s+and\s+wait\s+for\s+(?:limit|rate)",
        r"rate\s*limit",
    ]

    # Check if this looks like a rate limit scenario
    is_rate_limit = any(re.search(p, message, re.IGNORECASE) for p in rate_limit_indicators)

    if not is_rate_limit:
        print(json.dumps({"decision": "allow"}))
        return

    # Extract time and timezone from the message
    time_pattern = r"(\d{1,2}(?::\d{2})?\s*(?:am|pm))\s*\(([^)]+)\)"
    match = re.search(time_pattern, message, re.IGNORECASE)

    if not match:
        log("Rate limit detected but no reset time found")
        print(json.dumps({"decision": "allow"}))
        return

    time_str = match.group(1)  # e.g., "4am" or "11:30pm"
    tz_str = match.group(2)    # e.g., "America/Los_Angeles"

    log(f"Rate limit detected. Reset time: {time_str} ({tz_str})")

    try:
        reset_time = parse_reset_time(time_str, tz_str)
        wake_time = reset_time + timedelta(minutes=BUFFER_MINUTES)

        # Calculate sleep duration
        now = datetime.now(reset_time.tzinfo)
        sleep_seconds = (wake_time - now).total_seconds()

        if sleep_seconds > 0:
            log(f"Sleeping until {wake_time.strftime('%Y-%m-%d %H:%M:%S %Z')} ({sleep_seconds:.0f} seconds)")
            time.sleep(sleep_seconds)
            log("Waking up - resuming Claude")
        else:
            log("Reset time already passed, continuing immediately")

        # Tell Claude to continue (block the stop)
        print(json.dumps({"decision": "block"}))

    except Exception as e:
        log(f"Error parsing time: {e}")
        # On error, allow normal stop behavior
        print(json.dumps({"decision": "allow"}))

if __name__ == "__main__":
    main()
