[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

function Invoke-AirGuardSqlFile {
    param([Parameter(Mandatory = $true)][string]$ContainerPath)

    docker compose exec -T postgres psql -v ON_ERROR_STOP=1 -U airguard -d airguard -f $ContainerPath
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to apply $ContainerPath"
    }
}

# Safe for an existing local demo database: schema and seed are idempotent.
Invoke-AirGuardSqlFile "/docker-entrypoint-initdb.d/schema.sql"
Invoke-AirGuardSqlFile "/docker-entrypoint-initdb.d/seed.sql"
Invoke-AirGuardSqlFile "/migrations/20260823_003_fix_vietnamese_station_names_and_alerts.sql"
Invoke-AirGuardSqlFile "/migrations/20260823_004_fix_vietnamese_demo_user_names.sql"
Invoke-AirGuardSqlFile "/migrations/20260831_012_backfill_missing_demo_station_filters.sql"

docker compose exec -T postgres psql -v ON_ERROR_STOP=1 -U airguard -d airguard -c "SELECT station_id FROM stations ORDER BY station_id;"
if ($LASTEXITCODE -ne 0) {
    throw "Demo database validation failed"
}

Write-Host "AirGuard demo schema and seed are ready."
