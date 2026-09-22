<#
.SYNOPSIS
    Reads whichever of reports/junit-{build,deploy,test}.xml exist and
    writes a consolidated Markdown report to $env:GITHUB_STEP_SUMMARY -
    GitHub Actions renders that as the run's Job Summary, so the full
    picture (which stage failed, the exact compile/login/runtime error)
    is visible right on the run page without digging through raw logs.

    Run with `if: always()` as the last workflow step - safe to call even
    if earlier stages never ran (their report file just won't exist yet,
    e.g. deploy/test after a failed build).
#>
param(
    [string]$ReportsDir = (Join-Path $PSScriptRoot "..\reports")
)

$ErrorActionPreference = "Stop"

function Get-JUnitCases {
    param([string]$Path)
    if (-not (Test-Path $Path)) { return $null }
    [xml]$xml = Get-Content -Path $Path -Raw
    $cases = $xml.testsuite.testcase
    if ($null -eq $cases) { return @() }
    return @($cases)
}

$stages = @(
    @{ Name = "Build (kompilacja PilaJednosuportowa.project)"; File = "junit-build.xml" }
    @{ Name = "Deploy (login / download / start)"; File = "junit-deploy.xml" }
    @{ Name = "Test (smoke test stanu RUN)"; File = "junit-test.xml" }
)
# Plain ASCII everywhere below (no Polish diacritics) - the .ps1 source
# itself round-trips fine through pwsh (PowerShell 7, what CI uses), but
# Windows PowerShell 5.1 misreads a non-BOM UTF-8 source file as the
# system codepage and garbles ą/ć/ę/ł/ń/ó/ś/ż/ź. Not worth the risk for
# a handful of characters.

$lines = New-Object System.Collections.Generic.List[string]
$lines.Add("## CODESYS CI - raport")
$lines.Add("")

$anyFailure = $false
$anyRan = $false

foreach ($stage in $stages) {
    $path = Join-Path $ReportsDir $stage.File
    $cases = Get-JUnitCases -Path $path

    if ($null -eq $cases) {
        $lines.Add("### $([char]0x2B1C) $($stage.Name)")
        $lines.Add("_Etap nie zostal uruchomiony (wczesniejszy etap przerwal pipeline)._")
        $lines.Add("")
        continue
    }

    $anyRan = $true
    foreach ($case in $cases) {
        # <failure> has no attributes, just text content - PowerShell's
        # XML adapter returns that as a plain string here.
        $failure = $case.failure
        $timeAttr = $case.GetAttribute("time")
        $timeSuffix = if ($timeAttr) { " ($timeAttr s)" } else { "" }

        if ($failure) {
            $anyFailure = $true
            $lines.Add("### $([char]0x274C) $($stage.Name) - $($case.name)$timeSuffix")
            $lines.Add("")
            $lines.Add('```')
            $lines.Add(($failure -replace "`r`n", "`n"))
            $lines.Add('```')
        } else {
            $lines.Add("### $([char]0x2705) $($stage.Name) - $($case.name)$timeSuffix")
        }
        $lines.Add("")
    }
}

$verdict = if (-not $anyRan) { "$([char]0x2753) Brak jakichkolwiek raportow - sprawdz logi joba." }
    elseif ($anyFailure) { "$([char]0x274C) Pipeline nie przeszedl - patrz szczegoly bledu wyzej." }
    else { "$([char]0x2705) Wszystkie etapy przeszly." }

$lines.Insert(1, $verdict)
$lines.Insert(2, "")

$summaryPath = $env:GITHUB_STEP_SUMMARY
if ($summaryPath) {
    $lines -join "`n" | Out-File -FilePath $summaryPath -Append -Encoding utf8
} else {
    $lines -join "`n" | Write-Host
}
