<#
.SYNOPSIS
    Validates and extracts a CODESYS installer .zip, then locates the
    installer .exe inside it. Writes the resolved .exe path as its only
    pipeline output, so callers can do:

        $exePath = ./scripts/Expand-Installer.ps1 -ZipPath a.zip -DestinationDir b
#>
param(
    [Parameter(Mandatory = $true)][string]$ZipPath,
    [Parameter(Mandatory = $true)][string]$DestinationDir
)

$ErrorActionPreference = "Stop"

& (Join-Path $PSScriptRoot "Assert-ValidZip.ps1") -Path $ZipPath

New-Item -ItemType Directory -Force -Path $DestinationDir | Out-Null
Expand-Archive -Path $ZipPath -DestinationPath $DestinationDir -Force

$exes = Get-ChildItem -Path $DestinationDir -Filter *.exe -Recurse
if ($exes.Count -eq 0) {
    throw "No .exe found after extracting '$ZipPath' into '$DestinationDir'."
}

$chosen = $null
if ($exes.Count -eq 1) {
    $chosen = $exes[0]
} else {
    $setupMatches = $exes | Where-Object { $_.Name -match "Setup" }
    if ($setupMatches.Count -eq 1) {
        $chosen = $setupMatches[0]
    } else {
        $candidates = ($exes | ForEach-Object { $_.FullName }) -join "`n  "
        throw @"
Found multiple .exe files after extracting '$ZipPath' and none/more than
one matched '*Setup*' unambiguously - pick the right one and adjust
Expand-Installer.ps1 (or pass a narrower -DestinationDir per installer):
  $candidates
"@
    }
}

Write-Output $chosen.FullName
