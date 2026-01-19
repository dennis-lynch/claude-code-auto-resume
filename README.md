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

## Usage

### Automatic
The hook runs automatically when Claude hits a usage limit, sleeping until the specified reset time.

### Manual
You can also use the `/sleep` command to pause Claude manually:
- `/sleep 2h` - Sleep for 2 hours
- `/sleep 4pm` - Sleep until 4:00 PM

## Uninstallation

### Unix/Mac/Git Bash
```bash
./uninstall.sh
```

### Windows PowerShell
```powershell
.\uninstall.ps1
```

## How It Works

1. Hook receives "Stop" event from Claude.
2. Reads the last few lines of the transcript to detect rate limit messages.
3. Parses reset time and timezone.
4. Sleeps until reset time + 5 minute buffer.
5. Resumes Claude automatically (`{"continue": true}`).

## Configuration

- **Buffer time**: Edit `BUFFER_MINUTES` in `rate-limit-sleep.py` (default: 5 minutes)
- **Log file**: `~/.claude/hooks/rate-limit.log`

## Requirements

- Python 3.9+
- Claude Code CLI
- [uv](https://docs.astral.sh/uv/).

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

## License

MIT
