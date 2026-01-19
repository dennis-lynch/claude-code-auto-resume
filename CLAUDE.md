# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Claude Code hook that automatically handles rate limit interruptions by parsing reset times, sleeping until the limit resets, and resuming sessions without user intervention.

## Architecture

### Core Components

**rate-limit-sleep.py** - The main hook script that:
- Receives JSON input via stdin from Claude Code's "Stop" hook event
- Uses regex to detect rate limit messages with patterns like "hit your limit resets 4am (America/Los_Angeles)"
- Parses time strings (formats: "4am", "4:00am", "11:30pm") and IANA timezone identifiers
- Calculates sleep duration until reset time + configurable buffer (default: 5 minutes)
- Returns `{"decision": "block"}` to prevent Claude from stopping, or `{"decision": "allow"}` for normal stops
- Logs all activity with timestamps to `~/.claude/hooks/rate-limit.log`

**Time Parsing Logic** (rate-limit-sleep.py:23-59):
- Normalizes timezone strings (handles spaces → underscores)
- Uses Python's `zoneinfo.ZoneInfo` for accurate timezone handling
- Handles 12/24-hour conversion with AM/PM periods
- Automatically adds a day if parsed reset time is in the past

**Installation Scripts**:
- `install.sh` - Unix/Mac/Git Bash installer that merges hook config into existing settings.json
- `install.ps1` - Windows PowerShell installer with equivalent functionality
- `uninstall.sh` - Removes hook script and cleanly removes entries from settings.json

### Settings Configuration Structure

The hook is registered in `~/.claude/settings.json` as:
```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python ~/.claude/hooks/rate-limit-sleep.py",
            "timeout": 86400
          }
        ]
      }
    ]
  }
}
```

The 86400 second (24 hour) timeout ensures the hook can sleep through the entire rate limit period.

## Testing

Test the hook's rate limit detection:
```bash
echo '{"stop_reason": "hit your limit resets 4am (America/Los_Angeles)"}' | python ~/.claude/hooks/rate-limit-sleep.py
```

Expected output: `{"decision": "block"}` and log entry created.

Test non-rate-limit cases:
```bash
echo '{"stop_reason": "user requested"}' | python ~/.claude/hooks/rate-limit-sleep.py
```

Expected output: `{"decision": "allow"}`

View logs:
```bash
tail -f ~/.claude/hooks/rate-limit.log
```

## Configuration

**Buffer time**: Edit `BUFFER_MINUTES` in rate-limit-sleep.py:14 (default: 5 minutes after reset)

**Log location**: `~/.claude/hooks/rate-limit.log` (defined at rate-limit-sleep.py:13)

## Key Implementation Details

- **Python 3.9+ required**: Uses `zoneinfo` module for timezone support
- **Regex pattern** (rate-limit-sleep.py:73): Matches "hit your limit" or "usage limit" followed by reset time in parentheses
- **Error handling**: On parsing errors, returns `{"decision": "allow"}` to fail safely
- **Timezone-aware**: Calculates sleep duration in the target timezone, not local time
- **Idempotent installation**: Both install scripts check for existing hook entries before adding

## Development Workflow

When modifying the hook script:
1. Edit rate-limit-sleep.py
2. Test with the echo command patterns above
3. For real testing, manually trigger a rate limit in Claude Code
4. Check logs at ~/.claude/hooks/rate-limit.log
5. Reinstall with `./install.sh` or `.\install.ps1` to update the deployed version

When modifying installers:
- Test on clean `~/.claude/settings.json` (new install)
- Test with existing settings.json (merge scenario)
- Test idempotency (running install twice)
- Verify JSON structure matches Claude Code's expected format
