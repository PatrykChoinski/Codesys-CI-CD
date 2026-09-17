<#
.SYNOPSIS
    TEST stage: runs the smoke test against the already-deployed
    application (container started and left running by the DEPLOY stage),
    then always tears the container down and collects its logs.
#>
param(
    [string]$CodesysExe = "C:\Program Files\CODESYS 3.5.22.0\CODESYS\Common\CODESYS.exe",
    [string]$ProjectPath = (Join-Path $PSScriptRoot "..\CICD.project"),
    [string]$ContainerName = "codesys-rte-ci",
    [int]$GatewayPort = 1217,
    [string]$ReportPath = (Join-Path $PSScriptRoot "..\reports\junit-test.xml")
)

$ErrorActionPreference = "Stop"
New-Item -ItemType Directory -Force -Path (Split-Path $ReportPath) | Out-Null

try {
    Write-Host "== Running CODESYS Scripting smoke test =="
    $scriptArgs = "$ProjectPath;127.0.0.1;$GatewayPort;$ReportPath"
    & $CodesysExe --profile "CODESYS V3.5 SP22" --noUI `
        "--runscript=$(Join-Path $PSScriptRoot 'codesys_test.py')" `
        --scriptargs $scriptArgs
    $codesysExit = $LASTEXITCODE

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
    Write-Host "== Collecting runtime logs and tearing down container =="
    docker logs $ContainerName 2>&1 | Out-File (Join-Path (Split-Path $ReportPath) "codesys-rte.log")
    docker rm -f $ContainerName | Out-Null
}
