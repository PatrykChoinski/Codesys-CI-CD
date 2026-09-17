<#
.SYNOPSIS
    Silently installs CODESYS Control Win V3 x64 (the runtime under test)
    directly on the runner - no Docker/container involved - and starts it
    as a Windows service.

.PARAMETER InstallerPath
    Path to the previously downloaded/cached installer executable.
#>
param(
    [Parameter(Mandatory = $true)][string]$InstallerPath,
    [string]$ServiceName = "CODESYSControlWinV3x64"
)

$ErrorActionPreference = "Stop"

$existing = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
if (-not $existing) {
    if (-not (Test-Path $InstallerPath)) {
        throw "Installer not found at $InstallerPath"
    }

    & (Join-Path $PSScriptRoot "Assert-ValidExe.ps1") -Path $InstallerPath

    Write-Host "== Installing CODESYS Control Win V3 x64 =="
    # NSIS-based installer - verify the exact silent-install switch for your
    # downloaded build with: & $InstallerPath /?
    $proc = Start-Process -FilePath $InstallerPath -ArgumentList "/S" -Wait -PassThru
    if ($proc.ExitCode -ne 0) {
        throw "CODESYS Control Win V3 installer failed with exit code $($proc.ExitCode)"
    }

    $existing = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
    if (-not $existing) {
        throw "Install reported success but service '$ServiceName' was not found - check the installed service name."
    }
} else {
    Write-Host "Service '$ServiceName' already installed, skipping install."
}

Set-Service -Name $ServiceName -StartupType Automatic
Start-Service -Name $ServiceName

$deadline = (Get-Date).AddSeconds(60)
while ((Get-Service -Name $ServiceName).Status -ne "Running") {
    if ((Get-Date) -gt $deadline) {
        throw "Service '$ServiceName' did not reach Running state within 60s"
    }
    Start-Sleep -Seconds 2
}

Write-Host "CODESYS Control Win V3 x64 runtime is running."
