param(
    [switch]$CreateSuperuser,
    [switch]$Down
)

$ErrorActionPreference = 'Stop'

if ($Down) {
    Write-Host "Stopping containers..." -ForegroundColor Yellow
    docker compose down
    exit $LASTEXITCODE
}

Write-Host "Starting PawCare (Docker)..." -ForegroundColor Cyan

docker compose up -d --build

if ($LASTEXITCODE -ne 0) {
    throw "docker compose failed"
}

if ($CreateSuperuser) {
    Write-Host "Creating Django superuser (interactive)..." -ForegroundColor Cyan
    docker compose run --rm web python manage.py createsuperuser
}

Write-Host "Done." -ForegroundColor Green
Write-Host "Open: http://127.0.0.1:8000/" -ForegroundColor Green
Write-Host "Stop: .\\scripts\\demo.ps1 -Down" -ForegroundColor Yellow
