param(
    [string]$BackupDir = "$PSScriptRoot\..\backups",
    [int]$RetentionDays = 30
)

$ErrorActionPreference = 'Stop'

function Write-Log {
    param([string]$Message)
    $timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
    $line = "[$timestamp] $Message"
    $line | Tee-Object -FilePath $script:LogFile -Append | Out-Null
}

$ProjectRoot = (Resolve-Path "$PSScriptRoot\..")
Set-Location $ProjectRoot

$BackupDir = (Resolve-Path -LiteralPath $BackupDir -ErrorAction SilentlyContinue) ?? (New-Item -ItemType Directory -Path $BackupDir -Force).FullName
$dbDir = Join-Path $BackupDir 'db'
$mediaDir = Join-Path $BackupDir 'media'
$logsDir = Join-Path $BackupDir 'logs'
New-Item -ItemType Directory -Path $dbDir, $mediaDir, $logsDir -Force | Out-Null

$dateOnly = Get-Date -Format 'yyyy-MM-dd'
$timestamp = Get-Date -Format 'yyyy-MM-dd_HH-mm-ss'
$script:LogFile = Join-Path $logsDir "backup_$dateOnly.log"

# Load .env if present (simple KEY=VALUE lines)
$envFile = Join-Path $ProjectRoot '.env'
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        $line = $_.Trim()
        if (-not $line -or $line.StartsWith('#')) { return }
        $parts = $line.Split('=', 2)
        if ($parts.Length -eq 2) {
            $name = $parts[0].Trim()
            $value = $parts[1].Trim().Trim('"')
            if ($name) { [System.Environment]::SetEnvironmentVariable($name, $value) }
        }
    }
}

$pgDb = $env:POSTGRES_DB; if (-not $pgDb) { $pgDb = 'shelter_db' }
$pgUser = $env:POSTGRES_USER; if (-not $pgUser) { $pgUser = 'shelter_user' }
$pgPass = $env:POSTGRES_PASSWORD; if (-not $pgPass) { $pgPass = '2112' }
$pgHost = $env:POSTGRES_HOST; if (-not $pgHost) { $pgHost = 'localhost' }
$pgPort = $env:POSTGRES_PORT; if (-not $pgPort) { $pgPort = '5433' }

$dbDumpFile = Join-Path $dbDir "${pgDb}_${timestamp}.dump"
$mediaArchive = Join-Path $mediaDir "media_${timestamp}.zip"

Write-Log "Backup started"
Write-Log "Project root: $ProjectRoot"
Write-Log "Backup dir: $BackupDir"
Write-Log "Retention days: $RetentionDays"

# 1) DB dump (prefer Docker Compose service db)
Write-Log "DB dump: starting"
$useDockerDb = $false
try {
    docker compose version | Out-Null
    if (Test-Path (Join-Path $ProjectRoot 'docker-compose.yml')) {
        $services = docker compose config --services 2>$null
        if ($services -match '(^|\s)db(\s|$)') { $useDockerDb = $true }
    }
} catch {
    $useDockerDb = $false
}

if ($useDockerDb) {
    Write-Log "DB dump mode: docker compose exec db"
    $env:PGPASSWORD = $pgPass
    # Redirect stdout to file
    docker compose exec -T db pg_dump -U $pgUser -F c $pgDb | Set-Content -Encoding Byte -Path $dbDumpFile
} else {
    Write-Log "DB dump mode: local pg_dump"
    $pgDump = Get-Command pg_dump -ErrorAction SilentlyContinue
    if (-not $pgDump) {
        throw "pg_dump not found. Install PostgreSQL client tools or use Docker Compose db service."
    }
    $env:PGPASSWORD = $pgPass
    & $pgDump.Path -h $pgHost -p $pgPort -U $pgUser -F c -f $dbDumpFile $pgDb
}
Write-Log "DB dump: OK -> $dbDumpFile"

# 2) Archive media/
Write-Log "Media archive: starting"
$mediaPath = Join-Path $ProjectRoot 'media'
if (Test-Path $mediaPath) {
    if (Test-Path $mediaArchive) { Remove-Item $mediaArchive -Force }
    Compress-Archive -Path $mediaPath -DestinationPath $mediaArchive -Force
    Write-Log "Media archive: OK -> $mediaArchive"
} else {
    Write-Log "Media archive: skipped (media/ folder not found)"
}

# 3) Cleanup old backups/logs
Write-Log "Cleanup: removing files older than $RetentionDays days"
$cutoff = (Get-Date).AddDays(-$RetentionDays)
Get-ChildItem $dbDir -File -Filter '*.dump' -ErrorAction SilentlyContinue | Where-Object { $_.LastWriteTime -lt $cutoff } | Remove-Item -Force -ErrorAction SilentlyContinue
Get-ChildItem $mediaDir -File -Filter 'media_*.zip' -ErrorAction SilentlyContinue | Where-Object { $_.LastWriteTime -lt $cutoff } | Remove-Item -Force -ErrorAction SilentlyContinue
Get-ChildItem $logsDir -File -Filter 'backup_*.log' -ErrorAction SilentlyContinue | Where-Object { $_.LastWriteTime -lt $cutoff } | Remove-Item -Force -ErrorAction SilentlyContinue

Write-Log "Backup finished successfully"
