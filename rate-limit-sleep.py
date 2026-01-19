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
    
    # Try to get timezone, with fallback to local timezone
    try:
        tz = ZoneInfo(tz_str)
    except Exception as e:
        # On Windows without tzdata package, ZoneInfo may not find IANA timezones
        # Fall back to local system timezone
        log(f"DEBUG: ZoneInfo failed for '{tz_str}': {e}, using local timezone")
        tz = datetime.now().astimezone().tzinfo

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

def get_recent_transcript_content(transcript_path: str, num_lines: int = 20) -> str:
    """Read the last N lines of the transcript JSONL file and extract text content."""
    try:
        path = Path(transcript_path)
        if not path.exists():
            log(f"DEBUG: Transcript file not found: {transcript_path}")
            return ""
        
        # Read all lines and get last N
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
        
        recent_lines = lines[-num_lines:] if len(lines) > num_lines else lines
        
        # Extract text content from each JSON line
        content_parts = []
        for line in recent_lines:
            try:
                entry = json.loads(line.strip())
                # Look for message content in various possible locations
                if isinstance(entry, dict):
                    # Common patterns for message content
                    if "message" in entry:
                        msg = entry["message"]
                        if isinstance(msg, str):
                            content_parts.append(msg)
                        elif isinstance(msg, dict) and "content" in msg:
                            content_parts.append(str(msg["content"]))
                    if "content" in entry:
                        content_parts.append(str(entry["content"]))
                    if "text" in entry:
                        content_parts.append(str(entry["text"]))
                    # Also stringify the whole entry to catch nested content
                    content_parts.append(str(entry))
            except json.JSONDecodeError:
                content_parts.append(line)
        
        return " ".join(content_parts)
    except Exception as e:
        log(f"DEBUG: Error reading transcript: {e}")
        return ""


def hook_mode():
    """Handle hook mode - read from stdin."""
    try:
        # Read stdin
        input_data = json.load(sys.stdin)
        log(f"DEBUG: Received JSON input: {json.dumps(input_data, indent=2)[:1000]}")
    except json.JSONDecodeError as e:
        log(f"DEBUG: JSON decode error: {e}")
        input_data = {}

    # Stop hooks don't receive message content directly - only metadata
    # We need to read the transcript file to find rate limit messages
    transcript_path = input_data.get("transcript_path", "")
    transcript_content = get_recent_transcript_content(transcript_path)
    
    # Combine input metadata and transcript content for searching
    message = str(input_data) + " " + transcript_content
    log(f"DEBUG: Combined message (first 500 chars): {message[:500]}")

    # Rate limit indicator patterns
    rate_limit_indicators = [
        r"hit your limit",
        r"usage limit",
        r"stop\s+and\s+wait\s+for\s+(?:limit|rate)",
        r"rate\s*limit",
    ]

    # Check if this looks like a rate limit scenario
    is_rate_limit = any(re.search(p, message, re.IGNORECASE) for p in rate_limit_indicators)
    log(f"DEBUG: is_rate_limit = {is_rate_limit}")

    if not is_rate_limit:
        log("DEBUG: Not a rate limit, returning continue=False")
        print(json.dumps({"continue": False}))
        return

    # Extract time and timezone from the message
    time_pattern = r"(\d{1,2}(?::\d{2})?\s*(?:am|pm))\s*\(([^)]+)\)"
    match = re.search(time_pattern, message, re.IGNORECASE)

    if not match:
        log("Rate limit detected but no reset time found")
        print(json.dumps({"continue": False}))
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

        # Tell Claude to continue (block the stop, resume Claude)
        print(json.dumps({"continue": True}))

    except Exception as e:
        log(f"Error parsing time: {e}")
        # On error, allow normal stop behavior
        print(json.dumps({"continue": False}))

def main():
    # Check if invoked with CLI argument (manual mode)
    if len(sys.argv) > 1:
        manual_sleep(sys.argv[1])
    else:
        # Hook mode - read from stdin
        hook_mode()

if __name__ == "__main__":
    main()
