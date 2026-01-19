# Sleep Command

Sleep for a specified duration or until a specific time, then continue working.

## Usage

- `/sleep 2h` - Sleep for 2 hours
- `/sleep 30m` - Sleep for 30 minutes
- `/sleep 45s` - Sleep for 45 seconds
- `/sleep 4pm` - Sleep until 4:00 PM
- `/sleep 11:30am` - Sleep until 11:30 AM

## Instructions

Run this command to sleep for the specified time:

```
python $CLAUDE_HOOKS_DIR/rate-limit-sleep.py $ARGUMENTS
```

Where `$CLAUDE_HOOKS_DIR` is:
- Windows: `%USERPROFILE%\.claude\hooks`
- macOS/Linux: `~/.claude/hooks`

After the sleep completes, continue with whatever task was in progress before the sleep was requested.
