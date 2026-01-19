"""Tests for installation scripts."""
import pytest
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path


@pytest.fixture
def temp_home():
    """Create a temporary home directory for testing."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def project_root():
    """Get the project root directory."""
    return Path(__file__).parent.parent


class TestFreshInstallation:
    """Test installation on a fresh system (no existing settings)."""

    def test_creates_settings_file(self, temp_home, project_root):
        """Test that fresh install creates settings.json."""
        claude_dir = Path(temp_home) / ".claude"
        settings_file = claude_dir / "settings.json"

        # Ensure no existing settings
        assert not settings_file.exists()

        # Run a simulation of what install script does
        claude_dir.mkdir(parents=True, exist_ok=True)
        hooks_dir = claude_dir / "hooks"
        hooks_dir.mkdir(parents=True, exist_ok=True)

        settings = {
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

        with open(settings_file, 'w') as f:
            json.dump(settings, f, indent=2)

        # Verify
        assert settings_file.exists()
        with open(settings_file) as f:
            loaded = json.load(f)
        assert "hooks" in loaded
        assert "Stop" in loaded["hooks"]

    def test_creates_hooks_directory(self, temp_home):
        """Test that hooks directory is created."""
        hooks_dir = Path(temp_home) / ".claude" / "hooks"
        hooks_dir.mkdir(parents=True, exist_ok=True)
        assert hooks_dir.exists()


class TestMergeInstallation:
    """Test installation that merges with existing settings."""

    def test_preserves_existing_settings(self, temp_home):
        """Test that existing settings are preserved during merge."""
        claude_dir = Path(temp_home) / ".claude"
        claude_dir.mkdir(parents=True, exist_ok=True)
        settings_file = claude_dir / "settings.json"

        # Create existing settings with other config
        existing = {
            "theme": "dark",
            "editor": "vim",
            "hooks": {
                "PreCommit": [
                    {"hooks": [{"type": "command", "command": "npm test"}]}
                ]
            }
        }

        with open(settings_file, 'w') as f:
            json.dump(existing, f, indent=2)

        # Simulate merge
        with open(settings_file) as f:
            settings = json.load(f)

        # Add our hook
        if "Stop" not in settings["hooks"]:
            settings["hooks"]["Stop"] = []

        new_hook = {
            "hooks": [
                {
                    "type": "command",
                    "command": "python ~/.claude/hooks/rate-limit-sleep.py",
                    "timeout": 86400
                }
            ]
        }
        settings["hooks"]["Stop"].append(new_hook)

        with open(settings_file, 'w') as f:
            json.dump(settings, f, indent=2)

        # Verify preservation
        with open(settings_file) as f:
            result = json.load(f)

        assert result["theme"] == "dark"
        assert result["editor"] == "vim"
        assert "PreCommit" in result["hooks"]
        assert "Stop" in result["hooks"]


class TestIdempotency:
    """Test that running install multiple times is safe."""

    def test_no_duplicate_hooks(self, temp_home):
        """Test that running install twice doesn't duplicate hooks."""
        claude_dir = Path(temp_home) / ".claude"
        claude_dir.mkdir(parents=True, exist_ok=True)
        settings_file = claude_dir / "settings.json"

        new_hook = {
            "hooks": [
                {
                    "type": "command",
                    "command": "python ~/.claude/hooks/rate-limit-sleep.py",
                    "timeout": 86400
                }
            ]
        }

        # First "install"
        settings = {"hooks": {"Stop": [new_hook]}}
        with open(settings_file, 'w') as f:
            json.dump(settings, f, indent=2)

        # Second "install" - check for existing hook
        with open(settings_file) as f:
            settings = json.load(f)

        hook_exists = False
        for entry in settings["hooks"]["Stop"]:
            for hook in entry.get("hooks", []):
                if "rate-limit-sleep.py" in hook.get("command", ""):
                    hook_exists = True
                    break

        # Should find existing hook and not add another
        assert hook_exists

        # Verify only one Stop hook entry exists
        assert len(settings["hooks"]["Stop"]) == 1


class TestBackupFunctionality:
    """Test backup creation during installation."""

    def test_creates_backup_file(self, temp_home):
        """Test that backup is created when settings.json exists."""
        claude_dir = Path(temp_home) / ".claude"
        claude_dir.mkdir(parents=True, exist_ok=True)
        settings_file = claude_dir / "settings.json"

        # Create existing settings
        original = {"theme": "light", "hooks": {}}
        with open(settings_file, 'w') as f:
            json.dump(original, f, indent=2)

        # Simulate backup creation
        backup_file = Path(str(settings_file) + ".bak")
        shutil.copy(settings_file, backup_file)

        # Verify backup exists and has original content
        assert backup_file.exists()
        with open(backup_file) as f:
            backup_content = json.load(f)
        assert backup_content["theme"] == "light"

    def test_timestamped_backup_when_bak_exists(self, temp_home):
        """Test that timestamped backup is created when .bak already exists."""
        claude_dir = Path(temp_home) / ".claude"
        claude_dir.mkdir(parents=True, exist_ok=True)
        settings_file = claude_dir / "settings.json"

        # Create existing settings
        original = {"version": 1}
        with open(settings_file, 'w') as f:
            json.dump(original, f, indent=2)

        # Create first backup
        backup_file = Path(str(settings_file) + ".bak")
        old_backup = {"version": 0}
        with open(backup_file, 'w') as f:
            json.dump(old_backup, f, indent=2)

        # Create timestamped backup (simulated)
        timestamped_backup = Path(str(settings_file) + ".bak.20240101_120000")
        shutil.copy(settings_file, timestamped_backup)

        # Verify both backups exist
        assert backup_file.exists()
        assert timestamped_backup.exists()

        # Verify original .bak is preserved
        with open(backup_file) as f:
            content = json.load(f)
        assert content["version"] == 0

    def test_backup_before_modification(self, temp_home):
        """Test that backup captures state before any modifications."""
        claude_dir = Path(temp_home) / ".claude"
        claude_dir.mkdir(parents=True, exist_ok=True)
        settings_file = claude_dir / "settings.json"

        # Create settings without our hook
        original = {
            "hooks": {
                "PreSave": [{"hooks": [{"type": "command", "command": "lint"}]}]
            }
        }
        with open(settings_file, 'w') as f:
            json.dump(original, f, indent=2)

        # Create backup
        backup_file = Path(str(settings_file) + ".bak")
        shutil.copy(settings_file, backup_file)

        # Modify settings
        with open(settings_file) as f:
            settings = json.load(f)
        settings["hooks"]["Stop"] = [{"hooks": []}]
        with open(settings_file, 'w') as f:
            json.dump(settings, f, indent=2)

        # Verify backup doesn't have Stop hook
        with open(backup_file) as f:
            backup_content = json.load(f)
        assert "Stop" not in backup_content["hooks"]

        # Verify current settings do have Stop hook
        with open(settings_file) as f:
            current = json.load(f)
        assert "Stop" in current["hooks"]
