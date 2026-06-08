Param()

$port = 8444
$ruleName = "PawCare HTTPS $port"

$principal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Error "Run this script in an elevated PowerShell window (Administrator)."
    exit 1
}

try {
    $existing = Get-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue
    if ($null -eq $existing) {
        New-NetFirewallRule -DisplayName $ruleName -Direction Inbound -Action Allow -Protocol TCP -LocalPort $port -Profile Private | Out-Null
        Write-Host "Firewall rule created for TCP $port on the Private profile."
    } else {
        Write-Host "Firewall rule already exists: $ruleName"
    }
} catch {
    Write-Error "Failed to create firewall rule. Run PowerShell as Administrator."
    exit 1
}
