<#
  SOC-Lab SSH brute-force attack launcher.
  Choose the target: the local ubuntu-ssh-target container, or a REMOTE SSH host.

  Examples:
    .\scripts\attack.ps1                         # local ubuntu-ssh-target (container)
    .\scripts\attack.ps1 -Target ubuntu          # same as above
    .\scripts\attack.ps1 -Target 192.168.1.50    # a REMOTE Linux/SSH host on your LAN
    .\scripts\attack.ps1 -Target 192.168.1.50 -User root
#>
param(
  [string]$Target = "ubuntu",      # "ubuntu" (local container) or an IP/hostname (remote)
  [string]$User   = "devops"       # SSH username to brute force
)
$ErrorActionPreference = "Stop"
$docker = "C:\Program Files\Docker\Docker\resources\bin\docker.exe"
$env:PATH = (Split-Path $docker) + ";" + $env:PATH
Set-Location (Split-Path $PSScriptRoot -Parent)   # repo root

if ($Target -ieq "ubuntu") {
    $dest = "ubuntu-ssh-target"; $kind = "LOCAL container (ubuntu-ssh-target)"
} else {
    $dest = $Target;            $kind = "REMOTE host ($Target)"
}
Write-Host ""
Write-Host "===== SOC-Lab SSH brute force =====" -ForegroundColor Cyan
Write-Host ("Target : {0}" -f $kind)
Write-Host ("SSH user: {0}" -f $User)
Write-Host "Detection: Wazuh rule 100100 -> responder -> TheHive case" -ForegroundColor DarkGray
Write-Host ""
docker compose --profile attack run --rm -e TARGET=$dest -e SSH_USER=$User attacker
Write-Host ""
Write-Host "[*] Attack finished. Check TheHive (http://127.0.0.1:9000) for the auto-created case." -ForegroundColor Green