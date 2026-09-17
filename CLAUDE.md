# CLAUDE.md

Zasady pracy Claude w tym repozytorium.

## Git

- Każdą zmianę wprowadzoną w repo commituj lokalnie (małe, opisowe commity).
- Nigdy nie rób `git push` bez wyraźnego polecenia użytkownika w danej wiadomości.
- Każdą zmianę odnotuj w [CHANGELOG.md](CHANGELOG.md) przed/przy commicie.

## Projekt

- `CICD.project` — projekt CODESYS Control Win V3 (Development System, Windows-only).
- CODESYS IDE nie ma wersji na Linuksa/kontenerowej — kompilacja i sterowanie
  (CODESYS Scripting) odbywają się tylko na Windows (self-hosted runner z
  zainstalowanym CODESYS).
- Runtime do testów (`CODESYS Control Win V3 x64`, target V3.5 SP22) działa w
  **kontenerze Windows** (Docker Desktop/Engine w trybie "Windows containers"),
  patrz `docker/README.md`.
- Pipeline CI (`.github/workflows/codesys-ci.yml`) jest podzielony na 3 joby:
  `build` (kompilacja) → `deploy` (obraz + kontener + login/download/start) →
  `test` (smoke test stanu RUN + teardown kontenera). Szczegóły w `README.md`.
- Pełny opis architektury i uzasadnienie decyzji: patrz `README.md`.
