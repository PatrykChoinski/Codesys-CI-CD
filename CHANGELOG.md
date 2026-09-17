# Changelog

Wszystkie znaczące zmiany w tym repozytorium są odnotowywane w tym pliku.

## [Unreleased]

### Changed
- Runtime testowy przeniesiony z kontenera Ubuntu (`CODESYS Control for Linux SL`)
  na kontener Windows z `CODESYS Control Win V3 x64` (`docker/Dockerfile`,
  `docker/entrypoint.ps1`, `docker/docker-compose.yml`, `docker/README.md`
  przepisane pod Windows containers).
- Pipeline CI rozbity z jednego joba na trzy oddzielne joby: `build`, `deploy`,
  `test` (`.github/workflows/codesys-ci.yml`), każdy z własnym raportem JUnit.
  Zastąpiono `scripts/codesys_ci.py` + `scripts/Invoke-CodesysCI.ps1` przez:
  `scripts/codesys_build.py` + `Invoke-CodesysBuild.ps1` (kompilacja),
  `scripts/codesys_deploy.py` + `Invoke-CodesysDeploy.ps1` (obraz, kontener,
  login/download/start), `scripts/codesys_test.py` + `Invoke-CodesysTest.ps1`
  (weryfikacja stanu RUN + teardown kontenera).

### Added
- Główny `README.md` opisujący architekturę pipeline'u, uzasadnienie decyzji
  (Windows-only IDE, runtime w kontenerze Windows), strukturę repo, etapy CI,
  wymagania środowiska i ograniczenia (jeden self-hosted runner na etapy
  deploy/test).

### Added
- `.gitignore` ignorujący pliki robocze CODESYS (`*.opt`, `*.~u`, `*.precompilecache`).
- `CLAUDE.md` z zasadami pracy (commit lokalny po każdej zmianie, push tylko na żądanie).

### Removed
- Wycofano ze śledzenia w git pliki robocze CODESYS (`*.opt`, `*.~u`, `*.precompilecache`),
  które od teraz są ignorowane.

### Added
- `docker/Dockerfile` + `docker/entrypoint.sh` + `docker/docker-compose.yml`:
  obraz Ubuntu z runtime CODESYS Control for Linux SL (target V3.5 SP22).
  Instalator wymaga ręcznego pobrania z CODESYS Store (opisane w `docker/README.md`).
- `scripts/codesys_ci.py`: skrypt CODESYS Scripting (kompilacja, deploy przez
  gateway do kontenera, start aplikacji, weryfikacja stanu RUN, raport JUnit XML).
- `scripts/Invoke-CodesysCI.ps1`: orkiestracja na Windows self-hosted runnerze
  (build/uruchomienie kontenera, wywołanie CODESYS.exe headless, zebranie logów,
  teardown kontenera).
- `.github/workflows/codesys-ci.yml`: workflow GitHub Actions (self-hosted
  Windows runner z CODESYS + Docker Desktop) budujący obraz, wgrywający i
  uruchamiający projekt w kontenerze oraz publikujący raport testów (JUnit)
  jako artefakt i test summary.
