# Install the AI-log pre-push hook without discarding an existing user hook.
# Run once after cloning: powershell -ExecutionPolicy Bypass -File scripts\setup_hooks.ps1

$ErrorActionPreference = 'Stop'

$RepoRoot = (& git rev-parse --show-toplevel).Trim()
if (-not $RepoRoot) { throw 'Not inside a Git working tree.' }

$HookPath = (& git rev-parse --git-path hooks/pre-push).Trim()
if ([System.IO.Path]::IsPathRooted($HookPath)) {
    $HookFile = $HookPath
} else {
    $HookFile = Join-Path $RepoRoot $HookPath
}
$UserHook = "$HookFile.user"
$Marker = '# AI_LOG_HOOK_V2'

$HookDir = Split-Path -Parent $HookFile
if (-not (Test-Path -LiteralPath $HookDir)) {
    New-Item -ItemType Directory -Path $HookDir | Out-Null
}

if (Test-Path -LiteralPath $HookFile) {
    $Existing = Get-Content -LiteralPath $HookFile -Raw
    if (-not $Existing.Contains($Marker)) {
        $IsLegacyAiLog = $Existing.Contains('scripts/log_antigravity.py') -and
            $Existing.Contains('scripts/submit_log.py')
        if ($IsLegacyAiLog) {
            Write-Host '[ai-log] Upgrading legacy AI-log pre-push hook.'
        } else {
            if (Test-Path -LiteralPath $UserHook) {
                throw "Refusing to overwrite existing backup: $UserHook"
            }
            Move-Item -LiteralPath $HookFile -Destination $UserHook
            Write-Host "[ai-log] Preserved existing pre-push hook as $UserHook"
        }
    }
}

$HookBody = @'
#!/usr/bin/env bash
# AI_LOG_HOOK_V2
set -u

REPO_ROOT=$(git rev-parse --show-toplevel) || exit 1
cd "$REPO_ROOT" || exit 1
USER_HOOK=$(git rev-parse --git-path hooks/pre-push.user)

if [ -f "$USER_HOOK" ]; then
  chmod +x "$USER_HOOK" 2>/dev/null || true
  "$USER_HOOK" "$@" || exit $?
fi

bash scripts/_pyrun.sh scripts/log_antigravity.py --auto || exit $?
bash scripts/_pyrun.sh scripts/submit_log.py || exit $?
'@

$Utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($HookFile, $HookBody, $Utf8NoBom)

if (-not (Test-Path -LiteralPath (Join-Path $RepoRoot '.ai-log'))) {
    New-Item -ItemType Directory -Path (Join-Path $RepoRoot '.ai-log') | Out-Null
}
$GitKeep = Join-Path $RepoRoot '.ai-log/.gitkeep'
if (-not (Test-Path -LiteralPath $GitKeep)) {
    New-Item -ItemType File -Path $GitKeep | Out-Null
}

Write-Host '[ai-log] Git pre-push hook installed. Logging errors will block the push.'
Write-Host '[ai-log] Configure AI_LOG_SERVER and AI_LOG_API_KEY in .env.'
