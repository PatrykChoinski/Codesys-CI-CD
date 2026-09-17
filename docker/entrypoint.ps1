# Starts the CODESYS Control Win V3 service in the foreground container
# session and keeps the container alive while the service is running,
# streaming its log so `docker logs` shows activity.

$ErrorActionPreference = "Stop"
$ServiceName = "CODESYSControlWinV3x64"

Start-Service -Name $ServiceName

$logDir = "C:\ProgramData\CODESYS\CODESYSControlWinV3x64"
$logFile = $null
if (Test-Path $logDir) {
    $logFile = Get-ChildItem -Path $logDir -Filter *.log -Recurse -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending | Select-Object -First 1
}

if ($logFile) {
    Get-Content -Path $logFile.FullName -Wait -Tail 20
} else {
    # No log file found (path may differ per install) - just keep the
    # container alive while the service is running.
    while ((Get-Service -Name $ServiceName).Status -eq "Running") {
        Start-Sleep -Seconds 5
    }
}
