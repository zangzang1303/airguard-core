# Install git pre-push hook for AI log submission (Windows PowerShell).
# Run once after cloning: powershell -ExecutionPolicy Bypass -File scripts\setup_hooks.ps1

$ErrorActionPreference = 'Stop'

$HookFile = '.git/hooks/pre-push'

# Git on Windows runs hooks via Git Bash, so the hook body must be bash.
$HookBody = @'
#!/usr/bin/env bash
# Pre-push: sweep recent Antigravity / Gemini prompts, then submit AI logs.
if command -v cmd.exe >/dev/null 2>&1; then
  cmd.exe //c scripts\\\\_pyrun.cmd scripts\\\\log_antigravity.py --auto || true
  cmd.exe //c scripts\\\\_pyrun.cmd scripts\\\\submit_log.py || true
else
  bash scripts/_pyrun.sh scripts/log_antigravity.py --auto || true
  bash scripts/_pyrun.sh scripts/submit_log.py || true
fi
exit 0
'@

[System.IO.File]::WriteAllText(
    (Resolve-Path $HookFile).Path,
    $HookBody,
    [System.Text.UTF8Encoding]::new($false)
)
Write-Host "[ai-log] Git pre-push hook installed."

if (-not (Test-Path .ai-log)) { New-Item -ItemType Directory -Path .ai-log | Out-Null }
if (-not (Test-Path .ai-log/.gitkeep)) { New-Item -ItemType File -Path .ai-log/.gitkeep | Out-Null }

Write-Host "[ai-log] Setup complete. Configure AI_LOG_SERVER in your .env file."
