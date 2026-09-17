# CODESYS Control Win V3 runtime image (target: CODESYS V3.5 SP22)
#
# This is a WINDOWS container (needs Docker Desktop / Docker Engine in
# "Windows containers" mode, running on a Windows host whose build matches
# the base image below - or Hyper-V isolation to bridge a mismatch).
#
# CODESYS Control Win V3 is NOT publicly downloadable - it requires a
# CODESYS Store account and license agreement. Before building this image:
#
#   1. Log in to https://store.codesys.com with your account.
#   2. Download "CODESYS Control Win V3 x64" matching V3.5 SP22.
#   3. Place the downloaded installer (e.g.
#      CODESYSControlWinV3x64Setup.exe) into docker/installers/
#      and pass its filename as the CODESYS_RTE_INSTALLER build arg.
#
# Example (from repo root, Windows container mode):
#   docker build --build-arg CODESYS_RTE_INSTALLER=CODESYSControlWinV3x64Setup.exe `
#                -t codesys-rte-win:3.5.22 -f docker\Dockerfile docker
#
# Without a runtime license, CODESYS Control Win V3 runs in demo mode
# (limited continuous running time per session) - sufficient for CI
# smoke tests.

# escape=`
ARG WINDOWS_BASE_TAG=ltsc2022
FROM mcr.microsoft.com/windows/servercore:${WINDOWS_BASE_TAG}

SHELL ["powershell", "-NoProfile", "-Command", "$ErrorActionPreference='Stop';"]

ARG CODESYS_RTE_INSTALLER
WORKDIR C:\codesys-installer
COPY installers/${CODESYS_RTE_INSTALLER} .\installer.exe

# Silent install. CODESYS installers are NSIS-based - verify the exact
# silent-install switches for your downloaded build with:
#   installer.exe /?
# Common switches are /S (silent) and /D=<install dir> (must be last arg,
# no quotes). Adjust below if your installer differs (e.g. .msi package
# would use msiexec /i installer.msi /qn instead).
RUN Start-Process -FilePath .\installer.exe -ArgumentList '/S' -Wait -PassThru | `
        ForEach-Object { if ($_.ExitCode -ne 0) { throw \"Installer failed with exit code $($_.ExitCode)\" } } ; `
    Remove-Item -Recurse -Force C:\codesys-installer

# Gateway (engineering/download traffic), OPC UA, WebVisu/webserver
EXPOSE 1217 4840 8080

COPY entrypoint.ps1 C:\entrypoint.ps1

HEALTHCHECK --interval=10s --timeout=5s --retries=6 `
    CMD powershell -NoProfile -Command `
        "if ((Get-Service -Name 'CODESYSControlWinV3x64' -ErrorAction SilentlyContinue).Status -eq 'Running') { exit 0 } else { exit 1 }"

ENTRYPOINT ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", "C:\\entrypoint.ps1"]
