# CODESYS Control Win V3 - Docker runtime (Windows container)

Windows container image providing the CODESYS runtime (target V3.5 SP22,
`CODESYS Control Win V3 x64`) that CI deploys the compiled `CICD.project`
application to for a smoke test.

## Requirements

- A Windows host (Windows 10/11 Pro/Enterprise or Windows Server) with
  Docker Desktop / Docker Engine switched to **Windows containers** mode
  (`Switch to Windows containers...` in Docker Desktop's tray menu, or
  `Set-Service -Name docker` config on Windows Server).
- The base image tag (`ltsc2022` by default, see `WINDOWS_BASE_TAG` build
  arg) should match the host's Windows build for **process isolation**;
  otherwise build/run with `--isolation=hyperv`.

## Why the installer isn't bundled

`CODESYS Control Win V3` is only distributed through the CODESYS Store
after login (license agreement acceptance). It cannot be fetched
anonymously in a Dockerfile `RUN` step, so it must be provided as build
input:

1. Download the installer for V3.5 SP22 from https://store.codesys.com
   (search "CODESYS Control Win V3 x64").
2. Copy it into `docker/installers/` (git-ignored).
3. Build with `--build-arg CODESYS_RTE_INSTALLER=<filename>`.

On the CI runner, store the filename as the `CODESYS_RTE_INSTALLER_FILENAME`
GitHub Actions secret/variable and the installer file itself at
`docker/installers/<filename>` on the self-hosted runner's checkout.

Verify the installer's actual silent-install switches with `installer.exe /?`
before relying on the `/S` flag baked into `docker/Dockerfile` - NSIS-based
CODESYS installers commonly support it, but this should be confirmed per
downloaded build.

## Runtime license

Without a runtime license, CODESYS Control Win V3 runs in demo mode
(limited continuous running time per session before it needs a restart),
which is sufficient for short CI smoke tests. For production or longer
test runs, apply a container/runtime license as described in the CODESYS
Control Win V3 manual.

## Local manual test

```powershell
cd docker
$env:CODESYS_RTE_INSTALLER = "CODESYSControlWinV3x64Setup.exe"
docker compose build
docker compose up -d
docker logs -f codesys-rte
```

Gateway is exposed on `localhost:1217`, OPC UA on `4840`, web/WebVisu on `8080`.
