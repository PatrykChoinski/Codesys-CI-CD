<#
.SYNOPSIS
    BUILD stage: compiles the CODESYS project via CODESYS Scripting.
    Does not touch Docker or any runtime - fails fast on compile errors.
#>
param(
    [string]$CodesysExe = "C:\Program Files\CODESYS 3.5.22.30\CODESYS\Common\CODESYS.exe",
    # Must match exactly what's registered on the machine (Start Menu
    # shortcut arguments show the authoritative string) - for 3.5.22.30
    # that's "...Patch 3", NOT just "CODESYS V3.5 SP22".
    [string]$Profile = "CODESYS V3.5 SP22 Patch 3",
    # Only used to "prime" the machine-wide device repository (see
    # codesys_build.py) - actual code always comes from $ProjectPath.
    [string]$ArchivePath = (Join-Path $PSScriptRoot "..\PilaJednosuportowa.projectarchive"),
    [string]$PrimeExtractDir = (Join-Path $PSScriptRoot "..\work\prime"),
    [string]$ProjectPath = (Join-Path $PSScriptRoot "..\PilaJednosuportowa.project"),
    [string]$ReportPath = (Join-Path $PSScriptRoot "..\reports\junit-build.xml"),
    # The project archive is encrypted - password comes from the
    # CODESYS_PROJECT_PASSWORD env var (set from the PROJECT_PASSWORD
    # GitHub Actions secret in the workflow), never hardcoded/committed.
    [string]$ArchivePassword = $env:CODESYS_PROJECT_PASSWORD
)

$ErrorActionPreference = "Stop"
New-Item -ItemType Directory -Force -Path (Split-Path $ReportPath) | Out-Null
New-Item -ItemType Directory -Force -Path $PrimeExtractDir | Out-Null

Write-Host "== Compiling project =="
$codesysExit = & (Join-Path $PSScriptRoot "Invoke-CodesysCli.ps1") -CodesysExe $CodesysExe `
    -Profile $Profile `
    -ScriptPath (Join-Path $PSScriptRoot "codesys_build.py") `
    -ScriptArguments @($ArchivePath, $PrimeExtractDir, $ProjectPath, $ReportPath, $ArchivePassword)

if (Test-Path $ReportPath) {
    Write-Host "== Build report =="
    Get-Content $ReportPath
} else {
    Write-Warning "No report generated at $ReportPath"
}

if ($codesysExit -ne 0) {
    throw "Compilation failed (exit code $codesysExit)"
}

Write-Host "Build stage finished successfully."
