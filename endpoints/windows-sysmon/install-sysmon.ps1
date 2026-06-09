# Install Sysmon with the SwiftOnSecurity config on the Windows endpoint.
# Run in an elevated PowerShell from this folder:
#   powershell -ExecutionPolicy Bypass -File .\install-sysmon.ps1
$ErrorActionPreference = "Stop"
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$work = Join-Path $env:TEMP "sysmon-install"
New-Item -ItemType Directory -Force -Path $work | Out-Null
Write-Host "[*] Downloading Sysmon..."
Invoke-WebRequest -UseBasicParsing -Uri "https://download.sysinternals.com/files/Sysmon.zip" -OutFile "$work\Sysmon.zip"
Expand-Archive -Path "$work\Sysmon.zip" -DestinationPath $work -Force
$cfg = Join-Path $PSScriptRoot "sysmonconfig.xml"
Write-Host "[*] Installing Sysmon with $cfg"
& "$work\Sysmon64.exe" -accepteula -i $cfg
Write-Host "[+] Sysmon installed. Events: Microsoft-Windows-Sysmon/Operational (IDs 1=ProcessCreate, 3=NetworkConnect, 11=FileCreate)."