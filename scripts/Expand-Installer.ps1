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

# InstallShield-based CODESYS installers bundle prerequisite installers
# (VC++ redist, .NET, the InstallShield engine itself) under an
# "ISSetupPrerequisites" subfolder - the real installer is the one
# sitting outside of it (typically directly in $DestinationDir).
$candidates = $exes | Where-Object { $_.FullName -notmatch "ISSetupPrerequisites" }
if ($candidates.Count -eq 0) {
    $candidates = $exes
}

$chosen = $null
if ($candidates.Count -eq 1) {
    $chosen = $candidates[0]
} else {
    # Some CODESYS installer zips bundle both the 32-bit and 64-bit
    # variant (e.g. "CODESYS Control RTE 3.5.22.30.exe" vs "CODESYS
    # Control RTE 64 3.5.22.30.exe") - we always target x64.
    $x64Matches = $candidates | Where-Object { $_.Name -match "64" }
    $setupMatches = $candidates | Where-Object { $_.Name -match "Setup" }
    if ($x64Matches.Count -eq 1) {
        $chosen = $x64Matches[0]
    } elseif ($setupMatches.Count -eq 1) {
        $chosen = $setupMatches[0]
    } else {
        $list = ($candidates | ForEach-Object { $_.FullName }) -join "`n  "
        throw @"
Found multiple candidate .exe files after extracting '$ZipPath' (outside
ISSetupPrerequisites) and none/more than one matched '*64*' or '*Setup*'
unambiguously - pick the right one and adjust Expand-Installer.ps1:
  $list
"@
    }
}

Write-Output $chosen.FullName
