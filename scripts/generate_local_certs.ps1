Param()

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$pythonExe = Join-Path $scriptDir "..\.venv\Scripts\python.exe"

if (-not (Test-Path $pythonExe)) {
    Write-Error "Python executable not found at $pythonExe. Activate the virtual environment or install dependencies first."
    exit 1
}

& $pythonExe (Join-Path $scriptDir "generate_local_certs.py")

if ($LASTEXITCODE -ne 0) {
    Write-Error "Certificate generation failed."
    exit 1
}
