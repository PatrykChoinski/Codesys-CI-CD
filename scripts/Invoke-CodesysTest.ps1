<#
.SYNOPSIS
    TEST stage: runs the smoke test against the application deployed by
    the DEPLOY stage in the same job (same runner, no container to tear
    down), collects the runtime log and stops the service.
#>
param(
    [string]$CodesysExe = "C:\Program Files\CODESYS 3.5.22.30\CODESYS\Common\CODESYS.exe",
    # Must match exactly what's registered on the machine (Start Menu
    # shortcut arguments show the authoritative string) - for 3.5.22.30
    # that's "...Patch 3", NOT just "CODESYS V3.5 SP22".
    [string]$Profile = "CODESYS V3.5 SP22 Patch 3",
    [string]$ProjectPath = (Join-Path $PSScriptRoot "..\CICD.project"),
    [string]$ReportPath = (Join-Path $PSScriptRoot "..\reports\junit-test.xml")
)

$ErrorActionPreference = "Stop"
New-Item -ItemType Directory -Force -Path (Split-Path $ReportPath) | Out-Null

try {
    Write-Host "== Running CODESYS Scripting smoke test =="
    $codesysExit = & (Join-Path $PSScriptRoot "Invoke-CodesysCli.ps1") -CodesysExe $CodesysExe `
        -Profile $Profile `
        -ScriptPath (Join-Path $PSScriptRoot "codesys_test.py") `
        -ScriptArguments @($ProjectPath, $ReportPath)

    if (Test-Path $ReportPath) {
        Write-Host "== Test report =="
        Get-Content $ReportPath
    } else {
        Write-Warning "No report generated at $ReportPath"
    }

    if ($codesysExit -ne 0) {
        throw "Smoke test failed (exit code $codesysExit)"
    }

    Write-Host "Test stage finished successfully."
}
finally {
    Write-Host "== Collecting runtime log and stopping the service =="
    # Resolve the service by display name rather than a guessed short
    # Name - CODESYS Control Win's exact internal service Name isn't
    # confirmed, but its display name reliably contains "CODESYS Control".
    $service = Get-Service | Where-Object { $_.DisplayName -like "*CODESYS Control*" } | Select-Object -First 1

    $logDir = "C:\ProgramData\CODESYS\CODESYSControlWinV3x64"
    $logDest = Join-Path (Split-Path $ReportPath) "codesys-rte.log"
    if (Test-Path $logDir) {
        Get-ChildItem -Path $logDir -Filter *.log -Recurse -ErrorAction SilentlyContinue |
            Sort-Object LastWriteTime -Descending | Select-Object -First 1 |
            ForEach-Object { Copy-Item $_.FullName -Destination $logDest -Force }
    }

    if ($service) {
        Stop-Service -Name $service.Name -ErrorAction SilentlyContinue
    }
}
