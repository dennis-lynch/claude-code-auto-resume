# Claude Code Rate Limit Sleep Hook

Automatically handles Claude Code usage limits by sleeping until the reset time and resuming your session.

## Features

- Detects rate limit messages like "You've hit your limit "resets 4am (America/Los_Angeles)"
- Parses the reset time and timezone
- Sleeps until 5 minutes after the reset time
- Automatically continues your Claude Code session
- Logs all activity to ~/.claude/hooks/rate-limit.log

## Requirements

- Python 3.9+ (for `zoneinfo` module)
- Claude Code CLI

## Installation

### Unix/Mac/Git Bash (Windows)

```bash
git clone git@github.com:dennis-lynch/claude-code-auto-resume.git
cd claude-code-auto-resume
./install.sh
```

### Windows PowerShell

```powershell
git clone git@github.com:dennis-lynch/claude-code-auto-resume.git
cd claude-code-auto-resume
.\install.ps1
```

## Uninstallation

```bash
./uninstall.sh
```

## Configuration

The default configuration:
- **Buffer time**: 5 minutes after reset (edit `BUFFER_MINUTES` in the script)
- **Log file**: ~/.claude/hooks/rate-limit.log

## How It Works

This hook uses Claude Code's "Stop" hook event. When Claude is about to stop:

1. The hook receives JSON containing the stop reason
2. It checks if the reason matches a rate limit pattern
3. If matched, it parses the reset time and timezone
4. Sleeps until the reset time + buffer
5. Returns `{"decision": "block"}` to prevent Claude from stopping

## Testing

```bash
echo '{"stop_reason": "hit your limit resets 4am (America/Los_Angeles)"}' | python ~/.claude/hooks/rate-limit-sleep.py
```

## License

MIT
