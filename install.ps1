# Install script for claude-rate-limit-sleep hook (Windows PowerShell)
# Safely merges with existing Claude Code configuration

$ErrorActionPreference = "Stop"

$ClaudeDir = "$env:USERPROFILE\.claude"
$HooksDir = "$ClaudeDir\hooks"
$SettingsFile = "$ClaudeDir\settings.json"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "Installing Claude Code Rate Limit Sleep Hook..."

# Create directories if needed
New-Item -ItemType Directory -Force -Path $HooksDir | Out-Null

# Copy the hook script
Copy-Item "$ScriptDir\rate-limit-sleep.py" -Destination $HooksDir -Force
Write-Host "✓ Installed hook script to $HooksDir\rate-limit-sleep.py"

# Hook configuration
$NewHook = @{
    hooks = @(
        @{
            type = "command"
            command = "python ~/.claude/hooks/rate-limit-sleep.py"
            timeout = 86400
        }
    )
}

if (Test-Path $SettingsFile) {
    Write-Host "Found existing settings.json, merging..."

    # Backup existing settings.json
    $BackupFile = "$SettingsFile.bak"
    if (Test-Path $BackupFile) {
        $Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
        $BackupFile = "$SettingsFile.bak.$Timestamp"
    }
    Copy-Item $SettingsFile -Destination $BackupFile
    Write-Host "✓ Backed up settings to $BackupFile"

    $Settings = Get-Content $SettingsFile -Raw | ConvertFrom-Json -AsHashtable

    if (-not $Settings.ContainsKey("hooks")) {
        $Settings["hooks"] = @{}
    }

    if (-not $Settings["hooks"].ContainsKey("Stop")) {
        $Settings["hooks"]["Stop"] = @()
    }

    # Check if hook already exists
    $HookExists = $false
    foreach ($entry in $Settings["hooks"]["Stop"]) {
        foreach ($hook in $entry["hooks"]) {
            if ($hook["command"] -like "*rate-limit-sleep.py*") {
                $HookExists = $true
                Write-Host "Hook already installed, skipping..."
                break
            }
        }
    }

    if (-not $HookExists) {
        $Settings["hooks"]["Stop"] += $NewHook
        $Settings | ConvertTo-Json -Depth 10 | Set-Content $SettingsFile
        Write-Host "✓ Added hook to settings.json"
    }
} else {
    Write-Host "Creating new settings.json..."
    $Settings = @{
        hooks = @{
            Stop = @($NewHook)
        }
    }
    $Settings | ConvertTo-Json -Depth 10 | Set-Content $SettingsFile
    Write-Host "✓ Created settings.json with hook configuration"
}

Write-Host ""
Write-Host "Installation complete!"
Write-Host "Log file location: $HooksDir\rate-limit.log"
