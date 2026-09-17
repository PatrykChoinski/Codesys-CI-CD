<#
.SYNOPSIS
    Silently installs the CODESYS Development System (V3.5 SP22) on the
    (ephemeral, hosted) Windows runner. Idempotent: skips the install if
    CODESYS.exe already exists at the expected path.

.PARAMETER InstallerPath
    Path to the previously downloaded/cached installer executable.
#>
param(
    [Parameter(Mandatory = $true)][string]$InstallerPath,
    [string]$CodesysExe = "C:\Program Files\CODESYS 3.5.22.30\CODESYS\Common\CODESYS.exe"
)

$ErrorActionPreference = "Stop"

if (Test-Path $CodesysExe) {
    Write-Host "CODESYS Development System already present at $CodesysExe, skipping install."
    return
}

if (-not (Test-Path $InstallerPath)) {
    throw "Installer not found at $InstallerPath"
}

& (Join-Path $PSScriptRoot "Assert-ValidExe.ps1") -Path $InstallerPath

Write-Host "== Installing CODESYS Development System =="
# NSIS-based installer - verify the exact silent-install switch for your
# downloaded build with: & $InstallerPath /?
$proc = Start-Process -FilePath $InstallerPath -ArgumentList "/S" -Wait -PassThru
if ($proc.ExitCode -ne 0) {
    throw "CODESYS Development System installer failed with exit code $($proc.ExitCode)"
}

if (-not (Test-Path $CodesysExe)) {
    throw "Install reported success but CODESYS.exe was not found at $CodesysExe - check the actual install path/version."
}

Write-Host "CODESYS Development System installed."
