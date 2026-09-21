<#
.SYNOPSIS
    Runs CODESYS.exe headless with a given script and returns its exit
    code. Centralizes the exact command-line syntax confirmed against the
    official docs (https://content.helpme-codesys.com/en/CODESYS%20Scripting/_cds_starting_script_via_command_line.html):

        CODESYS.exe --profile="<profile>" --runscript="<script>.py" --scriptargs:'<arg1> <arg2>' --noUI

    Note --scriptargs uses a COLON and single quotes (not --scriptargs=),
    and multiple arguments are space-separated within that single-quoted
    block, read back in the script via plain `sys.argv`.
#>
param(
    [Parameter(Mandatory = $true)][string]$CodesysExe,
    [Parameter(Mandatory = $true)][string]$Profile,
    [Parameter(Mandatory = $true)][string]$ScriptPath,
    [Parameter(Mandatory = $true)][string[]]$ScriptArguments
)

$ErrorActionPreference = "Stop"

$scriptArgsValue = ($ScriptArguments | ForEach-Object { '"{0}"' -f $_ }) -join ' '
# --textPrompts prevents confirmation dialogs (e.g. login warnings) from
# silently blocking forever in headless mode - without it, some of these
# still pop up even under --noUI and just hang since nothing can click them.
$argumentString = "--profile=`"$Profile`" --runscript=`"$ScriptPath`" --scriptargs:'$scriptArgsValue' --noUI --textPrompts"

$proc = Start-Process -FilePath $CodesysExe -ArgumentList $argumentString -Wait -PassThru -NoNewWindow
return $proc.ExitCode
