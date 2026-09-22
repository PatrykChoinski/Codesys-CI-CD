<#
.SYNOPSIS
    DEPLOY stage: installs/starts the CODESYS Control Win V3 x64 runtime
    directly on the runner (no Docker), then logs in, downloads and starts
    the application on it via CODESYS Scripting.

.PARAMETER RteInstallerPath
    Path to the CODESYS Control Win V3 x64 installer (downloaded/cached by
    the workflow before calling this script, see installers/README.md).

.NOTES
    No device/gateway address is passed to the script - the project's
    device is assumed to already target the local runtime (127.0.0.1),
    which is where DEPLOY just installed and started it.
#>
param(
    [string]$CodesysExe = "C:\Program Files\CODESYS 3.5.22.30\CODESYS\Common\CODESYS.exe",
    # Must match exactly what's registered on the machine (Start Menu
    # shortcut arguments show the authoritative string) - for 3.5.22.30
    # that's "...Patch 3", NOT just "CODESYS V3.5 SP22".
    [string]$Profile = "CODESYS V3.5 SP22 Patch 3",
    [string]$ProjectPath = (Join-Path $PSScriptRoot "..\PilaJednosuportowa.project"),
    [Parameter(Mandatory = $true)][string]$RteInstallerPath,
    [string]$ReportPath = (Join-Path $PSScriptRoot "..\reports\junit-deploy.xml"),
    # The project is encrypted - password comes from the
    # CODESYS_PROJECT_PASSWORD env var (set from the PROJECT_PASSWORD
    # GitHub Actions secret in the workflow), never hardcoded/committed.
    [string]$EncryptionPassword = $env:CODESYS_PROJECT_PASSWORD
)

$ErrorActionPreference = "Stop"
New-Item -ItemType Directory -Force -Path (Split-Path $ReportPath) | Out-Null

& (Join-Path $PSScriptRoot "Install-CodesysRuntime.ps1") -InstallerPath $RteInstallerPath

Write-Host "== Running CODESYS Scripting (login, download, start) =="
$codesysExit = & (Join-Path $PSScriptRoot "Invoke-CodesysCli.ps1") -CodesysExe $CodesysExe `
    -Profile $Profile `
    -ScriptPath (Join-Path $PSScriptRoot "codesys_deploy.py") `
    -ScriptArguments @($ProjectPath, $ReportPath, $EncryptionPassword)

if (Test-Path $ReportPath) {
    Write-Host "== Deploy report =="
    Get-Content $ReportPath
} else {
    Write-Warning "No report generated at $ReportPath"
}

if ($codesysExit -ne 0) {
    throw "Deploy failed (exit code $codesysExit)"
}

Write-Host "Deploy stage finished successfully."
