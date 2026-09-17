<#
.SYNOPSIS
    Sanity-checks a downloaded installer before running it: fails fast
    with a clear message instead of Start-Process's cryptic "file or
    directory is corrupted and unreadable" when the download actually
    saved an HTML error/login page instead of the real .exe (a common
    failure mode with share links, e.g. Synology "File Station" links
    that serve a landing page instead of the raw file to non-browser
    clients like Invoke-WebRequest).
#>
param(
    [Parameter(Mandatory = $true)][string]$Path
)

$ErrorActionPreference = "Stop"

$item = Get-Item -Path $Path
if ($item.Length -lt 1MB) {
    $preview = Get-Content -Path $Path -TotalCount 20 -ErrorAction SilentlyContinue
    throw @"
'$Path' is only $($item.Length) bytes - too small to be a real CODESYS
installer. The download most likely returned an HTML/error page instead
of the binary (common with share links that show a landing page to
non-browser clients). First lines of the file:
$($preview -join "`n")

Check that the secret URL is a DIRECT download link (test with
'curl -I <url>' and confirm Content-Type is application/octet-stream,
not text/html), not a share/preview page URL.
"@
}

$bytes = [System.IO.File]::ReadAllBytes($Path)[0..1]
if ($bytes[0] -ne 0x4D -or $bytes[1] -ne 0x5A) {
    # "MZ" magic number every Windows PE executable starts with.
    throw "'$Path' does not start with the 'MZ' executable signature - it is not a valid .exe (got bytes: $($bytes -join ','))."
}

Write-Host "$Path looks like a valid executable ($([math]::Round($item.Length / 1MB, 1)) MB)."
