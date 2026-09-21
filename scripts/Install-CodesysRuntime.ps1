<#
.SYNOPSIS
    Silently installs CODESYS Control Win V3 x64 (the runtime under test)
    directly on the runner - no Docker/container involved - and starts it
    as a Windows service.

.PARAMETER InstallerPath
    Path to the previously downloaded/cached installer executable.
#>
param(
    [Parameter(Mandatory = $true)][string]$InstallerPath
)

$ErrorActionPreference = "Stop"

function Find-CodesysControlService {
    # The exact internal service Name isn't confirmed against official
    # docs, but its display name reliably contains "CODESYS Control" -
    # resolve dynamically instead of guessing the short Name.
    Get-Service | Where-Object { $_.DisplayName -like "*CODESYS Control*" } | Select-Object -First 1
}

function Disable-MandatoryUserManagement {
    # CODESYS Control >= SP17 defaults to requiring an activated device
    # user management before any engineering login is accepted. On a
    # fresh install nobody has activated it yet, and the interactive
    # "would you like to activate it now? create an admin user..." prompt
    # this triggers cannot be answered in headless CI (it just fails with
    # "The handle is invalid" even with --textPrompts). The documented
    # fix is this config line - normally shipped commented out - in every
    # CODESYSControl.cfg found under the install:
    # https://content.helpme-codesys.com/en/CODESYS%20Development%20System/_cds_sec_faq_deactivating_usermanagement.html
    Write-Host "== Disabling mandatory device user management (headless CI can't answer the interactive activation prompt) =="
    $cfgFiles = Get-ChildItem -Path "C:\ProgramData\CODESYS", "C:\Program Files", "C:\Program Files (x86)" `
        -Recurse -Filter "CODESYSControl.cfg" -ErrorAction SilentlyContinue
    foreach ($f in $cfgFiles) {
        $content = Get-Content -Path $f.FullName
        if ($content -match "^;SECURITY\.UserMgmtEnforce=NO") {
            $content -replace '^;SECURITY\.UserMgmtEnforce=NO', 'SECURITY.UserMgmtEnforce=NO' | Set-Content -Path $f.FullName
            Write-Host "Patched $($f.FullName)"
        }
    }
}

$service = Find-CodesysControlService
$wasAlreadyRunning = $service -and $service.Status -eq "Running"

if (-not $service) {
    if (-not (Test-Path $InstallerPath)) {
        throw "Installer not found at $InstallerPath"
    }

    & (Join-Path $PSScriptRoot "Assert-ValidExe.ps1") -Path $InstallerPath

    Write-Host "== Installing CODESYS Control Win V3 x64 =="
    # InstallShield-wrapped installer (same family as the Development
    # System one - see ISSetupPrerequisites next to it). /s triggers
    # InstallShield's own silent mode, /v/qn passes "quiet, no UI" through
    # to the underlying MSI. Verify with & $InstallerPath /? if this ever
    # stops working for a newer build.
    & (Join-Path $PSScriptRoot "Start-SilentInstall.ps1") -InstallerPath $InstallerPath -ArgumentList @("/s", "/v/qn")

    $service = Find-CodesysControlService
    if (-not $service) {
        throw "Install reported success but no service with display name like '*CODESYS Control*' was found - check the installed service name (Get-Service | Format-Table Name, DisplayName)."
    }
} else {
    Write-Host "Service '$($service.Name)' already installed, skipping install."
}

Disable-MandatoryUserManagement

$serviceName = $service.Name
Set-Service -Name $serviceName -StartupType Automatic
if ($wasAlreadyRunning) {
    Restart-Service -Name $serviceName -Force
} else {
    Start-Service -Name $serviceName
}

$deadline = (Get-Date).AddSeconds(60)
while ((Get-Service -Name $serviceName).Status -ne "Running") {
    if ((Get-Date) -gt $deadline) {
        throw "Service '$serviceName' did not reach Running state within 60s"
    }
    Start-Sleep -Seconds 2
}

Write-Host "CODESYS Control Win V3 x64 runtime ('$serviceName') is running."
