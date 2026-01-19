#!/bin/bash
# Uninstall script for claude-rate-limit-sleep hook

set -e

CLAUDE_DIR="$HOME/.claude"
HOOKS_DIR="$CLAUDE_DIR/hooks"
COMMANDS_DIR="$CLAUDE_DIR/commands"
SETTINGS_FILE="$CLAUDE_DIR/settings.json"

echo "Uninstalling Claude Code Rate Limit Sleep Hook..."

# Remove hook script
if [ -f "$HOOKS_DIR/rate-limit-sleep.py" ]; then
    rm "$HOOKS_DIR/rate-limit-sleep.py"
    echo "✓ Removed hook script"
fi

# Remove slash command
if [ -f "$COMMANDS_DIR/sleep.md" ]; then
    rm "$COMMANDS_DIR/sleep.md"
    echo "✓ Removed /sleep command"
fi

# Remove from settings.json if it exists
if [ -f "$SETTINGS_FILE" ]; then
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    elif command -v python &> /dev/null; then
        PYTHON_CMD="python"
    else
        echo "Warning: Python not found, please manually remove hook from settings.json"
        exit 0
    fi

    $PYTHON_CMD << 'PYEOF'
import json
from pathlib import Path

settings_file = Path.home() / ".claude" / "settings.json"

with open(settings_file, 'r') as f:
    settings = json.load(f)

if "hooks" in settings and "Stop" in settings["hooks"]:
    # Filter out our hook
    settings["hooks"]["Stop"] = [
        entry for entry in settings["hooks"]["Stop"]
        if not any("rate-limit-sleep.py" in h.get("command", "")
                   for h in entry.get("hooks", []))
    ]

    # Clean up empty arrays
    if not settings["hooks"]["Stop"]:
        del settings["hooks"]["Stop"]
    if not settings["hooks"]:
        del settings["hooks"]

    with open(settings_file, 'w') as f:
        json.dump(settings, f, indent=2)
    print("✓ Removed hook from settings.json")
PYEOF
fi

echo ""
echo "Uninstall complete!"
echo "Note: Log file preserved at $HOOKS_DIR/rate-limit.log (delete manually if desired)"
