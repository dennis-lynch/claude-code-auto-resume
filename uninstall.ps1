# Uninstall script for claude-rate-limit-sleep hook (Windows PowerShell)

$ErrorActionPreference = "Stop"

$ClaudeDir = "$env:USERPROFILE\.claude"
$HooksDir = "$ClaudeDir\hooks"
$CommandsDir = "$ClaudeDir\commands"
$SettingsFile = "$ClaudeDir\settings.json"

Write-Host "Uninstalling Claude Code Rate Limit Sleep Hook..."

# Remove hook script
if (Test-Path "$HooksDir\rate-limit-sleep.py") {
    Remove-Item "$HooksDir\rate-limit-sleep.py" -Force
    Write-Host "✓ Removed hook script"
}

# Remove slash command
if (Test-Path "$CommandsDir\sleep.md") {
    Remove-Item "$CommandsDir\sleep.md" -Force
    Write-Host "✓ Removed /sleep command"
}

# Remove from settings.json if it exists
if (Test-Path $SettingsFile) {
    $Settings = Get-Content $SettingsFile -Raw | ConvertFrom-Json -AsHashtable

    if ($Settings.ContainsKey("hooks") -and $Settings["hooks"].ContainsKey("Stop")) {
        # Filter out our hook
        $FilteredStop = @()
        foreach ($entry in $Settings["hooks"]["Stop"]) {
            $HasRateLimitHook = $false
            foreach ($hook in $entry["hooks"]) {
                if ($hook["command"] -like "*rate-limit-sleep.py*") {
                    $HasRateLimitHook = $true
                    break
                }
            }
            if (-not $HasRateLimitHook) {
                $FilteredStop += $entry
            }
        }
        $Settings["hooks"]["Stop"] = $FilteredStop

        # Clean up empty arrays
        if ($Settings["hooks"]["Stop"].Count -eq 0) {
            $Settings["hooks"].Remove("Stop")
        }
        if ($Settings["hooks"].Count -eq 0) {
            $Settings.Remove("hooks")
        }

        $Settings | ConvertTo-Json -Depth 10 | Set-Content $SettingsFile
        Write-Host "✓ Removed hook from settings.json"
    }
}

Write-Host ""
Write-Host "Uninstall complete!"
Write-Host "Note: Log file preserved at $HooksDir\rate-limit.log (delete manually if desired)"
