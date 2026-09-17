<#
.SYNOPSIS
    Runs CODESYS.exe headless with a given script and returns its exit
    code. Centralizes the exact command-line syntax CODESYS.exe expects:
    --flag="value" with LITERAL quotes around values (confirmed by its
    own error message: 'you must specify a profile using
    --profile="profile name"') - PowerShell's `&` operator quoting for
    spaces alone is not enough, so this builds the command line as one
    string and runs it via Start-Process for full control over quoting.
#>
param(
    [Parameter(Mandatory = $true)][string]$CodesysExe,
    [Parameter(Mandatory = $true)][string]$Profile,
    [Parameter(Mandatory = $true)][string]$ScriptPath,
    [Parameter(Mandatory = $true)][string]$ScriptArgs
)

$ErrorActionPreference = "Stop"

$argumentString = '--profile="{0}" --noUI --runscript="{1}" --scriptargs="{2}"' -f $Profile, $ScriptPath, $ScriptArgs

$proc = Start-Process -FilePath $CodesysExe -ArgumentList $argumentString -Wait -PassThru -NoNewWindow
return $proc.ExitCode
