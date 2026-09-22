<#
.SYNOPSIS
    Regenerates PilaJednosuportowa.projectarchive from
    PilaJednosuportowa.project. Run this LOCALLY (on a machine with
    CODESYS Development System AND the project's target device already
    installed, e.g. by installing CODESYS Control Win V3) whenever the
    project's target/device or bundled libraries change, then re-upload
    the resulting .projectarchive to the GitHub Release asset CI
    downloads it from (see README.md - it's too large to commit to git).

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
    [string]$ProjectPath = (Join-Path $PSScriptRoot "..\PilaJednosuportowa.project"),
    [string]$ArchivePath = (Join-Path $PSScriptRoot "..\PilaJednosuportowa.projectarchive"),
    # The project is encrypted - pass its encryption password here (or
    # via $env:CODESYS_PROJECT_PASSWORD) since this runs headless
    # (--noUI) too and can't answer the "Encryption Password" dialog.
    [string]$EncryptionPassword = $env:CODESYS_PROJECT_PASSWORD
)

$ErrorActionPreference = "Stop"

$exitCode = & (Join-Path $PSScriptRoot "Invoke-CodesysCli.ps1") -CodesysExe $CodesysExe `
    -Profile $Profile `
    -ScriptPath (Join-Path $PSScriptRoot "codesys_save_archive.py") `
    -ScriptArguments @($ProjectPath, $ArchivePath, $EncryptionPassword)

if ($exitCode -ne 0) {
    throw "Failed to save project archive (exit code $exitCode)"
}

Write-Host "Updated $ArchivePath - remember to re-upload it to the GitHub Release asset CI downloads it from (see README.md)."
