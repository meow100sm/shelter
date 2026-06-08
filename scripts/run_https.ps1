Param()

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$pythonExe = Join-Path $scriptDir "..\.venv\Scripts\python.exe"

if (-not (Test-Path $pythonExe)) {
    Write-Error "Python executable not found at $pythonExe. Activate the virtual environment first."
    exit 1
}

& $pythonExe (Join-Path $scriptDir "run_https_server.py")
