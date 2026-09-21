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
    [string]$ArchivePath = (Join-Path $PSScriptRoot "..\CICD.projectarchive"),
    [string]$ExtractDir = (Join-Path $PSScriptRoot "..\work\build"),
    [string]$ReportPath = (Join-Path $PSScriptRoot "..\reports\junit-build.xml")
)

$ErrorActionPreference = "Stop"
New-Item -ItemType Directory -Force -Path (Split-Path $ReportPath) | Out-Null
New-Item -ItemType Directory -Force -Path $ExtractDir | Out-Null

Write-Host "== Compiling project =="
$codesysExit = & (Join-Path $PSScriptRoot "Invoke-CodesysCli.ps1") -CodesysExe $CodesysExe `
    -Profile $Profile `
    -ScriptPath (Join-Path $PSScriptRoot "codesys_build.py") `
    -ScriptArguments @($ArchivePath, $ExtractDir, $ReportPath)

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
