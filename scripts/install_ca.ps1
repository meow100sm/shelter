Param()

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$certPath = Join-Path $scriptDir "..\caddy\ssl\localhost.cer"

if (-not (Test-Path $certPath)) {
    Write-Error "Certificate not found at $certPath. Run scripts\generate_local_certs.ps1 first."
    exit 1
}

Write-Host "Importing $certPath into CurrentUser\\Root..."
try {
    Import-Certificate -FilePath $certPath -CertStoreLocation Cert:\CurrentUser\Root | Out-Null
    Write-Host "Certificate trusted for the current Windows user. Restart the browser if needed."
} catch {
    Write-Error "Failed to import the certificate into the Windows trust store."
    exit 1
}
