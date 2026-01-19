# Runs tests using uv's inline script metadata
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
uv run "$ScriptDir\run_tests.py" @args
exit $LASTEXITCODE
