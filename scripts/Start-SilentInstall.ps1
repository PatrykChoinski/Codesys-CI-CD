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
    [int]$TimeoutMinutes = 15
)

$ErrorActionPreference = "Stop"

$proc = Start-Process -FilePath $InstallerPath -ArgumentList $ArgumentList -PassThru
$finished = $proc.WaitForExit([int]([TimeSpan]::FromMinutes($TimeoutMinutes).TotalMilliseconds))

if (-not $finished) {
    try { $proc.Kill() } catch {}
    throw @"
'$InstallerPath' did not finish within $TimeoutMinutes minute(s) - most
likely it ignored the silent-install switch(es) '$($ArgumentList -join ' ')'
and is waiting on a UI prompt nobody can click in headless CI. Verify the
correct silent-install syntax for this build (run 'installer.exe /?'
locally, or check for an InstallShield 'setup.iss' response-file
workflow) and update the caller's -ArgumentList.
"@
}

if ($proc.ExitCode -ne 0) {
    throw "'$InstallerPath' exited with code $($proc.ExitCode) (args: $($ArgumentList -join ' '))"
}
