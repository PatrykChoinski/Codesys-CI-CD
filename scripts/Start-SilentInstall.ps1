<#
.SYNOPSIS
    Runs an installer with a hard timeout, so a wrong silent-install
    switch (installer falls back to showing a UI/prompt nobody can click
    in headless CI) fails the job after a bounded wait instead of hanging
    until the whole workflow run times out.

.PARAMETER ArgumentList
    Silent-install switches for the installer (e.g. @('/s', '/v/qn') for
    an InstallShield-wrapped MSI, @('/S') for NSIS).
#>
param(
    [Parameter(Mandatory = $true)][string]$InstallerPath,
    [Parameter(Mandatory = $true)][string[]]$ArgumentList,
    # InstallShield bootstraps chain through several msiexec runs (VC++
    # redist x86/x64, .NET, the product itself) - observed ~13 min on a
    # GitHub-hosted runner, but this varies a lot with disk/CPU/AV
    # contention, so the default leaves real headroom rather than cutting
    # it close.
    [int]$TimeoutMinutes = 40
)

$ErrorActionPreference = "Stop"

$proc = Start-Process -FilePath $InstallerPath -ArgumentList $ArgumentList -PassThru
$finished = $proc.WaitForExit([int]([TimeSpan]::FromMinutes($TimeoutMinutes).TotalMilliseconds))

if (-not $finished) {
    # The launcher process spawns further msiexec children that don't die
    # with it - kill the whole tree so a timeout doesn't leave a half
    # -finished install running in the background.
    try { taskkill /T /F /PID $proc.Id 2>&1 | Out-Null } catch {}
    throw @"
'$InstallerPath' did not finish within $TimeoutMinutes minute(s) - most
likely it ignored the silent-install switch(es) '$($ArgumentList -join ' ')'
and is waiting on a UI prompt nobody can click in headless CI. Verify the
correct silent-install syntax for this build (run 'installer.exe /?'
locally, or check for an InstallShield 'setup.iss' response-file
workflow) and update the caller's -ArgumentList.
"@
}

# 3010/3011 = ERROR_SUCCESS_REBOOT_REQUIRED/INITIATED - genuine Windows
# Installer success codes, just noting a reboot would normally be needed
# to finish. Irrelevant here: this is a single-use CI VM torn down right
# after the job, and CODESYS.exe/the service work fine without it.
$successCodes = @(0, 3010, 3011)
if ($successCodes -notcontains $proc.ExitCode) {
    throw "'$InstallerPath' exited with code $($proc.ExitCode) (args: $($ArgumentList -join ' '))"
}
if ($proc.ExitCode -ne 0) {
    Write-Host "'$InstallerPath' exited with code $($proc.ExitCode) (reboot-required success code, ignoring)"
}
