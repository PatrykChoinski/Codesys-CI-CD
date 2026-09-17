<#
.SYNOPSIS
    BUILD stage: compiles the CODESYS project via CODESYS Scripting.
    Does not touch Docker or any runtime - fails fast on compile errors.
#>
param(
    [string]$CodesysExe = "C:\Program Files\CODESYS 3.5.22.30\CODESYS\Common\CODESYS.exe",
    [string]$ProjectPath = (Join-Path $PSScriptRoot "..\CICD.project"),
    [string]$ReportPath = (Join-Path $PSScriptRoot "..\reports\junit-build.xml")
)

$ErrorActionPreference = "Stop"
New-Item -ItemType Directory -Force -Path (Split-Path $ReportPath) | Out-Null

Write-Host "== Compiling project =="
$scriptArgs = "$ProjectPath;$ReportPath"
& $CodesysExe "--profile=CODESYS V3.5 SP22" --noUI `
    "--runscript=$(Join-Path $PSScriptRoot 'codesys_build.py')" `
    "--scriptargs=$scriptArgs"
$codesysExit = $LASTEXITCODE

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
