# Claude Code Rate Limit Sleep Hook

Automatically handles Claude Code usage limits by sleeping until the reset time and resuming your session.

## Installation

### Unix/Mac/Git Bash
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

## Running Tests

Requires [uv](https://docs.astral.sh/uv/).

```bash
# Unix/Mac/Git Bash
./run_tests.sh

# Windows PowerShell
.\run_tests.ps1

# Direct (any platform)
uv run run_tests.py
```

## Manual Testing
```bash
# Test rate limit detection
echo '{"stop_reason": "hit your limit resets 4am (America/Los_Angeles)"}' | python rate-limit-sleep.py

# Test non-rate-limit (should allow)
echo '{"stop_reason": "user requested"}' | python rate-limit-sleep.py
```

## How It Works

1. Hook receives JSON from Claude Code's "Stop" event
2. Checks if stop reason matches rate limit patterns
3. Parses reset time and timezone from message
4. Sleeps until reset time + 5 minute buffer
5. Returns `{"decision": "block"}` to prevent stopping

## Configuration

- **Buffer time**: Edit `BUFFER_MINUTES` in `rate-limit-sleep.py` (default: 5 minutes)
- **Log file**: `~/.claude/hooks/rate-limit.log`

## Requirements

- Python 3.9+
- Claude Code CLI

## License

MIT
