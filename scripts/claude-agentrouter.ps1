[CmdletBinding()]
param(
    [Alias("p")]
    [string]$Prompt,

    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$ClaudeArgs
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
$agentRouterKey = $env:AGENTROUTER_API_KEY
$agentRouterModel = $env:AGENTROUTER_MODEL
$agentRouterBaseUrl = $env:AGENTROUTER_BASE_URL

if (
    [string]::IsNullOrWhiteSpace($agentRouterKey) -or
    [string]::IsNullOrWhiteSpace($agentRouterModel) -or
    [string]::IsNullOrWhiteSpace($agentRouterBaseUrl)
) {
    foreach ($fileName in @(".env.local", ".env")) {
        $envPath = Join-Path $projectRoot $fileName
        if (-not (Test-Path -LiteralPath $envPath)) {
            continue
        }

        $envLines = Get-Content -LiteralPath $envPath

        if ([string]::IsNullOrWhiteSpace($agentRouterKey)) {
            $keyLine = $envLines |
                Where-Object { $_ -match '^\s*AGENTROUTER_API_KEY\s*=' } |
                Select-Object -Last 1

            if ($null -ne $keyLine) {
                $agentRouterKey = ($keyLine -split '=', 2)[1].Trim().Trim('"').Trim("'")
            }
        }

        if ([string]::IsNullOrWhiteSpace($agentRouterModel)) {
            $modelLine = $envLines |
                Where-Object { $_ -match '^\s*AGENTROUTER_MODEL\s*=' } |
                Select-Object -Last 1

            if ($null -ne $modelLine) {
                $agentRouterModel = ($modelLine -split '=', 2)[1].Trim().Trim('"').Trim("'")
            }
        }

        if ([string]::IsNullOrWhiteSpace($agentRouterBaseUrl)) {
            $baseUrlLine = $envLines |
                Where-Object { $_ -match '^\s*AGENTROUTER_BASE_URL\s*=' } |
                Select-Object -Last 1

            if ($null -ne $baseUrlLine) {
                $agentRouterBaseUrl = ($baseUrlLine -split '=', 2)[1].Trim().Trim('"').Trim("'")
            }
        }
    }
}

if ([string]::IsNullOrWhiteSpace($agentRouterKey)) {
    throw "Missing AGENTROUTER_API_KEY. Add it to the ignored .env.local/.env file or set it in the current PowerShell session."
}

if ([string]::IsNullOrWhiteSpace($agentRouterBaseUrl)) {
    $agentRouterBaseUrl = "https://co.agentrouter.org"
}

$env:ANTHROPIC_BASE_URL = $agentRouterBaseUrl
$env:ANTHROPIC_AUTH_TOKEN = $agentRouterKey
$env:ANTHROPIC_API_KEY = $agentRouterKey

if (-not [string]::IsNullOrWhiteSpace($agentRouterModel)) {
    $env:ANTHROPIC_MODEL = $agentRouterModel
}

Push-Location $projectRoot
try {
    $effectiveArgs = @()
    if (-not [string]::IsNullOrWhiteSpace($Prompt)) {
        $effectiveArgs += @("-p", $Prompt)
    }
    $effectiveArgs += $ClaudeArgs
    & claude @effectiveArgs
    $claudeExitCode = $LASTEXITCODE
}
finally {
    Pop-Location
}

exit $claudeExitCode
