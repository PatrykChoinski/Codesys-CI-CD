<#
.SYNOPSIS
    Regenerates CICD.projectarchive from CICD.project. Run this LOCALLY
    (on a machine with CODESYS Development System AND the project's
    target device already installed, e.g. by installing CODESYS Control
    Win V3) whenever CICD.project changes, then commit the resulting
    CICD.projectarchive alongside it.

.NOTES
    See scripts/codesys_save_archive.py for why the archive exists at
    all: a bare CI install has no device descriptions registered, and
    opening the plain .project fails to compile with "C188: Device not
    installed to the system." The .projectarchive bundles the device
    description so CI can open it without that dependency.
#>
param(
    [string]$CodesysExe = "C:\Program Files\CODESYS 3.5.22.30\CODESYS\Common\CODESYS.exe",
    [string]$Profile = "CODESYS V3.5 SP22 Patch 3",
    [string]$ProjectPath = (Join-Path $PSScriptRoot "..\CICD.project"),
    [string]$ArchivePath = (Join-Path $PSScriptRoot "..\CICD.projectarchive")
)

$ErrorActionPreference = "Stop"

$exitCode = & (Join-Path $PSScriptRoot "Invoke-CodesysCli.ps1") -CodesysExe $CodesysExe `
    -Profile $Profile `
    -ScriptPath (Join-Path $PSScriptRoot "codesys_save_archive.py") `
    -ScriptArguments @($ProjectPath, $ArchivePath)

if ($exitCode -ne 0) {
    throw "Failed to save project archive (exit code $exitCode)"
}

Write-Host "Updated $ArchivePath - remember to commit it alongside CICD.project."
