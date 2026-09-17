# Changelog

Wszystkie znaczące zmiany w tym repozytorium są odnotowywane w tym pliku.

## [Unreleased]

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
