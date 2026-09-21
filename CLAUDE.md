# CLAUDE.md

Zasady pracy Claude w tym repozytorium.

## Git

- Każdą zmianę wprowadzoną w repo commituj lokalnie (małe, opisowe commity).
- Nigdy nie rób `git push` bez wyraźnego polecenia użytkownika w danej wiadomości.
- Każdą zmianę odnotuj w [CHANGELOG.md](CHANGELOG.md) przed/przy commicie.

## Projekt

- `CICD.project` — projekt CODESYS Control Win V3 (Development System, Windows-only).
- CODESYS IDE nie ma wersji na Linuksa/kontenerowej — kompilacja i sterowanie
  (CODESYS Scripting) odbywają się tylko na Windows.
- CI działa na hostowanych runnerach GitHub `windows-latest` — bez Dockera i
  bez self-hosted maszyny. Runtime (`CODESYS Control Win V3 x64`, target
  V3.5 SP22) instalowany jest bezpośrednio na runnerze jako usługa Windows
  (świeża VM per job już daje pełną izolację). Instalatory pobierane z
  prywatnego GitHub Release (tag `Installers`, w tym repo) przez
  `gh release download` i cache'owane przez `actions/cache`, patrz
  `installers/README.md`.
- Pipeline CI (`.github/workflows/codesys-ci.yml`) ma 2 joby: `build`
  (tylko kompilacja `CICD.projectarchive`, bez runtime) → `deploy-test`
  (install RTE + login/download/start + smoke test stanu RUN w jednym
  jobie, bo oba kroki potrzebują tej samej żywej usługi runtime na tej
  samej VM). Szczegóły w `README.md`.
- **`CICD.projectarchive` musi być zregenerowany i commitowany razem z
  `CICD.project` po każdej jego zmianie** (`./scripts/Update-ProjectArchive.ps1`,
  lokalnie, na maszynie z zainstalowanym CODESYS) - świeży CI install nie
  ma zarejestrowanego opisu urządzenia, a archiwum go dostarcza. Patrz
  `README.md`.
- Pełny opis architektury i uzasadnienie decyzji: patrz `README.md`.
