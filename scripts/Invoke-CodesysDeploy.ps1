<#
.SYNOPSIS
    DEPLOY stage: builds/starts the CODESYS Control Win V3 runtime Windows
    container, then logs in, downloads and starts the application on it
    via CODESYS Scripting. Leaves the container RUNNING for the TEST stage
    (torn down there, not here).

.PARAMETER CodesysRteInstaller
    Filename of the CODESYS Control Win V3 x64 installer placed under
    docker/installers/ (see docker/Dockerfile header for how to obtain it).
#>
param(
    [string]$CodesysExe = "C:\Program Files\CODESYS 3.5.22.0\CODESYS\Common\CODESYS.exe",
    [string]$ProjectPath = (Join-Path $PSScriptRoot "..\CICD.project"),
    [Parameter(Mandatory = $true)][string]$CodesysRteInstaller,
    [string]$ImageTag = "codesys-rte-win:3.5.22",
    [string]$ContainerName = "codesys-rte-ci",
    [int]$GatewayPort = 1217,
    [string]$ReportPath = (Join-Path $PSScriptRoot "..\reports\junit-deploy.xml")
)

$ErrorActionPreference = "Stop"
$repoRoot = Join-Path $PSScriptRoot ".."
$dockerDir = Join-Path $repoRoot "docker"
New-Item -ItemType Directory -Force -Path (Split-Path $ReportPath) | Out-Null

$serverOsType = (docker info --format '{{.OSType}}').Trim()
if ($serverOsType -ne "windows") {
    throw "Docker is in '$serverOsType' containers mode - switch Docker Desktop/Engine to Windows containers first (see docker/README.md)."
}

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

    Write-Host "== Running CODESYS Scripting (login, download, start) =="
    $scriptArgs = "$ProjectPath;127.0.0.1;$GatewayPort;$ReportPath"
    & $CodesysExe --profile "CODESYS V3.5 SP22" --noUI `
        "--runscript=$(Join-Path $PSScriptRoot 'codesys_deploy.py')" `
        --scriptargs $scriptArgs
    $codesysExit = $LASTEXITCODE

    if (Test-Path $ReportPath) {
        Write-Host "== Deploy report =="
        Get-Content $ReportPath
    } else {
        Write-Warning "No report generated at $ReportPath"
    }

    if ($codesysExit -ne 0) {
        throw "Deploy failed (exit code $codesysExit)"
    }
}
catch {
    # Deploy failed - no point leaving the container around for a TEST
    # stage that won't run. Successful deploys leave it running; the TEST
    # stage is responsible for tearing it down.
    Write-Host "== Deploy failed, tearing down container =="
    docker logs $ContainerName 2>&1 | Out-File (Join-Path (Split-Path $ReportPath) "codesys-rte-deploy.log")
    docker rm -f $ContainerName | Out-Null
    throw
}

Write-Host "Deploy stage finished successfully. Container '$ContainerName' left running for the test stage."
