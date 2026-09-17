# CLAUDE.md

Zasady pracy Claude w tym repozytorium.

## Git

- Każdą zmianę wprowadzoną w repo commituj lokalnie (małe, opisowe commity).
- Nigdy nie rób `git push` bez wyraźnego polecenia użytkownika w danej wiadomości.
- Każdą zmianę odnotuj w [CHANGELOG.md](CHANGELOG.md) przed/przy commicie.

## Projekt

- `CICD.project` — projekt CODESYS Control Win V3 (Development System, Windows-only).
- CODESYS IDE nie ma wersji na Linuksa — kompilacja projektu może odbywać się tylko
  na Windows (self-hosted runner z zainstalowanym CODESYS).
- Docker/Ubuntu w tym repo hostuje wyłącznie runtime (`CODESYS Control for Linux SL`,
  target V3.5 SP22) do wgrywania i testowania skompilowanej aplikacji przez gateway.
