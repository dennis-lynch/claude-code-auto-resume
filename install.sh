#!/bin/bash
# Install script for claude-rate-limit-sleep hook
# Safely merges with existing Claude Code configuration

set -e

CLAUDE_DIR="$HOME/.claude"
HOOKS_DIR="$CLAUDE_DIR/hooks"
COMMANDS_DIR="$CLAUDE_DIR/commands"
SETTINGS_FILE="$CLAUDE_DIR/settings.json"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Installing Claude Code Rate Limit Sleep Hook..."

# Create directories if needed
mkdir -p "$HOOKS_DIR"
mkdir -p "$COMMANDS_DIR"

# Copy the hook script
cp "$SCRIPT_DIR/rate-limit-sleep.py" "$HOOKS_DIR/"
chmod +x "$HOOKS_DIR/rate-limit-sleep.py"
echo "✓ Installed hook script to $HOOKS_DIR/rate-limit-sleep.py"

# Copy the slash command
cp "$SCRIPT_DIR/commands/sleep.md" "$COMMANDS_DIR/"
echo "✓ Installed /sleep command to $COMMANDS_DIR/sleep.md"

# Hook configuration to add
HOOK_ENTRY='{
  "hooks": [
    {
      "type": "command",
      "command": "python ~/.claude/hooks/rate-limit-sleep.py",
      "timeout": 86400
    }
  ]
}'

# Merge with existing settings.json
if [ -f "$SETTINGS_FILE" ]; then
    echo "Found existing settings.json, merging..."

    # Backup existing settings.json
    BACKUP_FILE="$SETTINGS_FILE.bak"
    if [ -f "$BACKUP_FILE" ]; then
        BACKUP_FILE="$SETTINGS_FILE.bak.$(date +%Y%m%d_%H%M%S)"
    fi
    cp "$SETTINGS_FILE" "$BACKUP_FILE"
    echo "✓ Backed up settings to $BACKUP_FILE"

    # Check if python3 or python is available for JSON manipulation
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    elif command -v python &> /dev/null; then
        PYTHON_CMD="python"
    else
        echo "Error: Python is required for JSON merging"
        exit 1
    fi

    # Use Python to safely merge the JSON
    $PYTHON_CMD << 'PYEOF'
import json
import sys
from pathlib import Path

settings_file = Path.home() / ".claude" / "settings.json"

# Read existing settings
with open(settings_file, 'r') as f:
    settings = json.load(f)

# New hook entry
new_hook = {
    "hooks": [
        {
            "type": "command",
            "command": "python ~/.claude/hooks/rate-limit-sleep.py",
            "timeout": 86400
        }
    ]
}

# Ensure hooks key exists
if "hooks" not in settings:
    settings["hooks"] = {}

# Ensure Stop key exists
if "Stop" not in settings["hooks"]:
    settings["hooks"]["Stop"] = []

# Check if hook already exists
hook_exists = False
for entry in settings["hooks"]["Stop"]:
    for hook in entry.get("hooks", []):
        if "rate-limit-sleep.py" in hook.get("command", ""):
            hook_exists = True
            print("Hook already installed, skipping...")
            break

if not hook_exists:
    settings["hooks"]["Stop"].append(new_hook)
    with open(settings_file, 'w') as f:
        json.dump(settings, f, indent=2)
    print("✓ Added hook to settings.json")
else:
    print("✓ Hook already configured in settings.json")
PYEOF

else
    echo "Creating new settings.json..."
    cat > "$SETTINGS_FILE" << 'EOF'
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
EOF
    echo "✓ Created settings.json with hook configuration"
fi

echo ""
echo "Installation complete!"
echo ""
echo "Installed components:"
echo "  - Stop hook: Auto-sleeps when rate limited"
echo "  - /sleep command: Manual sleep (e.g., /sleep 2h, /sleep 4pm)"
echo ""
echo "Log file location: $HOOKS_DIR/rate-limit.log"
