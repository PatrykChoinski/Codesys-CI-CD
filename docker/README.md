# CODESYS Control for Linux SL - Docker runtime

Docker image providing the CODESYS runtime (target V3.5 SP22) that CI deploys
the compiled `CICD.project` application to for a smoke test.

## Why the installer isn't bundled

`CODESYS Control for Linux SL` is only distributed through the CODESYS Store
after login (license agreement acceptance). It cannot be fetched anonymously
in a Dockerfile `RUN curl ...` step, so it must be provided as build input:

1. Download the installer for V3.5 SP22 from https://store.codesys.com
   (search "CODESYS Control for Linux SL").
2. Copy it into `docker/installers/` (git-ignored).
3. Build with `--build-arg CODESYS_RTE_INSTALLER=<filename>`.

On the CI runner, store the filename as the `CODESYS_RTE_INSTALLER_FILENAME`
GitHub Actions secret/variable and the installer file itself at
`docker/installers/<filename>` on the self-hosted runner's checkout.

## Runtime license

Without a runtime license, CODESYS Control for Linux SL runs in demo mode
(limited continuous running time per session before it needs a restart),
which is sufficient for short CI smoke tests. For production or longer test
runs, apply a container license via `CODESYSControl.cfg` / license file as
described in the CODESYS Control for Linux SL manual.

## Local manual test

```powershell
cd docker
docker compose build --build-arg CODESYS_RTE_INSTALLER=<filename>
docker compose up -d
docker logs -f codesys-rte
```

Gateway is exposed on `localhost:1217`, OPC UA on `4840`, web/WebVisu on `8080`.
