<#
.SYNOPSIS
    TEST stage: runs the smoke test against the application deployed by
    the DEPLOY stage in the same job (same runner, no container to tear
    down), collects the runtime log and stops the service.
#>
param(
    [string]$CodesysExe = "C:\Program Files\CODESYS 3.5.22.30\CODESYS\Common\CODESYS.exe",
    [string]$ProjectPath = (Join-Path $PSScriptRoot "..\CICD.project"),
    [string]$DeviceAddress = "127.0.0.1",
    [int]$GatewayPort = 1217,
    [string]$ServiceName = "CODESYSControlWinV3x64",
    [string]$ReportPath = (Join-Path $PSScriptRoot "..\reports\junit-test.xml")
)

$ErrorActionPreference = "Stop"
New-Item -ItemType Directory -Force -Path (Split-Path $ReportPath) | Out-Null

try {
    Write-Host "== Running CODESYS Scripting smoke test =="
    $scriptArgs = "$ProjectPath;$DeviceAddress;$GatewayPort;$ReportPath"
    $codesysExit = & (Join-Path $PSScriptRoot "Invoke-CodesysCli.ps1") -CodesysExe $CodesysExe `
        -Profile "CODESYS V3.5 SP22" `
        -ScriptPath (Join-Path $PSScriptRoot "codesys_test.py") `
        -ScriptArgs $scriptArgs

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
    $logDir = "C:\ProgramData\CODESYS\CODESYSControlWinV3x64"
    $logDest = Join-Path (Split-Path $ReportPath) "codesys-rte.log"
    if (Test-Path $logDir) {
        Get-ChildItem -Path $logDir -Filter *.log -Recurse -ErrorAction SilentlyContinue |
            Sort-Object LastWriteTime -Descending | Select-Object -First 1 |
            ForEach-Object { Copy-Item $_.FullName -Destination $logDest -Force }
    }
    Stop-Service -Name $ServiceName -ErrorAction SilentlyContinue
}
