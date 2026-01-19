#!/usr/bin/env python3
"""
Claude Code hook to handle rate limit by sleeping until reset time.
Can also be invoked manually via CLI: python rate-limit-sleep.py 2h
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

def parse_duration(duration_str: str) -> int | None:
    """Parse duration like '2h', '30m', '45s' into seconds. Returns None if not a duration."""
    duration_str = duration_str.lower().strip()
    match = re.match(r"^(\d+(?:\.\d+)?)\s*(h|hr|hrs|hour|hours|m|min|mins|minute|minutes|s|sec|secs|second|seconds)$", duration_str)
    if not match:
        return None
    
    value = float(match.group(1))
    unit = match.group(2)
    
    if unit in ("h", "hr", "hrs", "hour", "hours"):
        return int(value * 3600)
    elif unit in ("m", "min", "mins", "minute", "minutes"):
        return int(value * 60)
    else:  # seconds
        return int(value)

def parse_time_to_seconds(time_str: str, tz: ZoneInfo = None) -> int | None:
    """Parse time like '4pm', '11:30am' into seconds until that time. Returns None if not a time."""
    time_str = time_str.lower().strip()
    
    # Try to match time formats
    if ":" in time_str:
        match = re.match(r"^(\d{1,2}):(\d{2})\s*(am|pm)$", time_str)
        if not match:
            return None
        hour = int(match.group(1))
        minute = int(match.group(2))
        period = match.group(3)
    else:
        match = re.match(r"^(\d{1,2})\s*(am|pm)$", time_str)
        if not match:
            return None
        hour = int(match.group(1))
        minute = 0
        period = match.group(2)
    
    # Convert to 24-hour
    if period == "pm" and hour != 12:
        hour += 12
    elif period == "am" and hour == 12:
        hour = 0
    
    # Use local timezone if not specified
    if tz is None:
        tz = datetime.now().astimezone().tzinfo
    
    now = datetime.now(tz)
    target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    
    # If target time is in the past, it's for tomorrow
    if target <= now:
        target += timedelta(days=1)
    
    return int((target - now).total_seconds())

def parse_duration_or_time(arg: str) -> int:
    """Parse either a duration (2h, 30m) or time (4pm) into seconds to sleep."""
    # Try duration first
    seconds = parse_duration(arg)
    if seconds is not None:
        return seconds
    
    # Try time
    seconds = parse_time_to_seconds(arg)
    if seconds is not None:
        return seconds
    
    raise ValueError(f"Could not parse '{arg}' as duration (e.g., 2h, 30m) or time (e.g., 4pm, 11:30am)")

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

def manual_sleep(arg: str):
    """Handle manual invocation via CLI argument."""
    try:
        sleep_seconds = parse_duration_or_time(arg)
        wake_time = datetime.now() + timedelta(seconds=sleep_seconds)
        
        log(f"Manual sleep requested: {arg} ({sleep_seconds} seconds)")
        log(f"Sleeping until {wake_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        print(f"Sleeping for {sleep_seconds} seconds (until {wake_time.strftime('%H:%M:%S')})...")
        time.sleep(sleep_seconds)
        
        log("Waking up - resuming Claude")
        print("Awake! Resuming...")
        
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        log("Sleep interrupted by user")
        print("\nSleep interrupted.")
        sys.exit(0)

def hook_mode():
    """Handle hook mode - read from stdin."""
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

def main():
    # Check if invoked with CLI argument (manual mode)
    if len(sys.argv) > 1:
        manual_sleep(sys.argv[1])
    else:
        # Hook mode - read from stdin
        hook_mode()

if __name__ == "__main__":
    main()
