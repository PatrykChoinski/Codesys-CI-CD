<#
.SYNOPSIS
    Orchestrates the CODESYS CI pipeline on a Windows self-hosted runner:
    builds/starts the Ubuntu CODESYS runtime container, drives CODESYS
    Scripting to compile+deploy+smoke-test the project against it, then
    tears the container down and surfaces a JUnit report.

.PARAMETER CodesysExe
    Full path to CODESYS.exe (Development System) matching V3.5 SP22.

.PARAMETER ProjectPath
    Full path to CICD.project.

.PARAMETER CodesysRteInstaller
    Filename of the CODESYS Control for Linux SL installer placed under
    docker/installers/ (see docker/Dockerfile header for how to obtain it).
#>
param(
    [string]$CodesysExe = "C:\Program Files\CODESYS 3.5.22.0\CODESYS\Common\CODESYS.exe",
    [string]$ProjectPath = (Join-Path $PSScriptRoot "..\CICD.project"),
    [Parameter(Mandatory = $true)][string]$CodesysRteInstaller,
    [string]$ImageTag = "codesys-rte:3.5.22",
    [string]$ContainerName = "codesys-rte-ci",
    [int]$GatewayPort = 1217,
    [string]$ReportPath = (Join-Path $PSScriptRoot "..\reports\junit-codesys-ci.xml")
)

$ErrorActionPreference = "Stop"
$repoRoot = Join-Path $PSScriptRoot ".."
$dockerDir = Join-Path $repoRoot "docker"
New-Item -ItemType Directory -Force -Path (Split-Path $ReportPath) | Out-Null

Write-Host "== Building CODESYS runtime image =="
docker build --build-arg "CODESYS_RTE_INSTALLER=$CodesysRteInstaller" `
    -t $ImageTag -f (Join-Path $dockerDir "Dockerfile") $dockerDir
if ($LASTEXITCODE -ne 0) { throw "docker build failed" }

Write-Host "== Starting CODESYS runtime container =="
docker rm -f $ContainerName 2>$null | Out-Null
docker run -d --name $ContainerName `
    -p ${GatewayPort}:1217 -p 4840:4840 -p 8080:8080 `
    $ImageTag
if ($LASTEXITCODE -ne 0) { throw "docker run failed" }

try {
    Write-Host "== Waiting for runtime health check =="
    $healthy = $false
    for ($i = 0; $i -lt 24; $i++) {
        $status = docker inspect --format "{{.State.Health.Status}}" $ContainerName
        if ($status -eq "healthy") { $healthy = $true; break }
        Start-Sleep -Seconds 5
    }
    if (-not $healthy) {
        docker logs $ContainerName
        throw "CODESYS runtime container did not become healthy"
    }

    Write-Host "== Running CODESYS Scripting (compile, deploy, smoke test) =="
    $scriptArgs = "$ProjectPath;127.0.0.1;$GatewayPort;$ReportPath"
    & $CodesysExe --profile "CODESYS V3.5 SP22" --noUI `
        "--runscript=$(Join-Path $PSScriptRoot 'codesys_ci.py')" `
        --scriptargs $scriptArgs
    $codesysExit = $LASTEXITCODE

    if (Test-Path $ReportPath) {
        Write-Host "== Test report =="
        Get-Content $ReportPath
    } else {
        Write-Warning "No report generated at $ReportPath"
    }

    if ($codesysExit -ne 0) {
        throw "CODESYS scripting reported failures (exit code $codesysExit)"
    }
}
finally {
    Write-Host "== Collecting runtime logs =="
    docker logs $ContainerName 2>&1 | Out-File (Join-Path (Split-Path $ReportPath) "codesys-rte.log")

    Write-Host "== Tearing down container =="
    docker rm -f $ContainerName | Out-Null
}

Write-Host "CODESYS CI pipeline finished successfully."
