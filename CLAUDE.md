# CLAUDE.md

Zasady pracy Claude w tym repozytorium.

## Git

- Każdą zmianę wprowadzoną w repo commituj lokalnie (małe, opisowe commity).
- Nigdy nie rób `git push` bez wyraźnego polecenia użytkownika w danej wiadomości.
- Każdą zmianę odnotuj w [CHANGELOG.md](CHANGELOG.md) przed/przy commicie.

## Projekt

- `PilaJednosuportowa.project` — projekt CODESYS Control Win V3 (Development System, Windows-only).
- CODESYS IDE nie ma wersji na Linuksa/kontenerowej — kompilacja i sterowanie
  (CODESYS Scripting) odbywają się tylko na Windows.
- CI działa na hostowanych runnerach GitHub `windows-latest` — bez Dockera i
  bez self-hosted maszyny. Runtime (`CODESYS Control Win V3 x64`, target
  V3.5 SP22) instalowany jest bezpośrednio na runnerze jako usługa Windows
  (świeża VM per job już daje pełną izolację). Instalatory pobierane z
  prywatnego GitHub Release (tag `Installers`, w tym repo) przez
  `gh release download` i cache'owane przez `actions/cache`, patrz
  `installers/README.md`.
- Pipeline CI (`.github/workflows/codesys-ci.yml`) to **1 job**
  (`build-deploy-test`) z 3 etapami po sobie: kompilacja żywego
  `PilaJednosuportowa.project` → install RTE + login/download/start →
  smoke test stanu RUN. Był kiedyś podzielony na 2 joby, ale Dev System
  nie da się bezpiecznie cache'ować między jobami (próba się nie
  powiodła - patrz CHANGELOG), więc 2 joby oznaczały instalowanie go
  dwa razy (~26 zamiast ~13 min) - stąd z powrotem 1 job. Szczegóły w
  `README.md`.
- **`PilaJednosuportowa.projectarchive` służy TYLKO do "primingu"
  repozytorium urządzeń** (build otwiera je i od razu zamyka) - kod
  zawsze pochodzi z żywego `PilaJednosuportowa.project`, więc zwykła
  zmiana kodu **nie wymaga** regenerowania archiwum. Trzeba je
  zregenerować (`./scripts/Update-ProjectArchive.ps1`, lokalnie, na
  maszynie z zainstalowanym CODESYS Control Win V3) tylko gdy zmienia
  się target/urządzenie projektu albo zestaw bibliotek — i wtedy wgrać
  wynikowy plik jako asset do prywatnego GitHub Release (tag
  `ProjectArchive`), bo plik jest za duży (~120 MB) na commit do git
  (git-ignored, patrz `.gitignore`/`README.md`).
- Projekt jest zaszyfrowany hasłem (CODESYS "Encryption Password") -
  `projects.open()`/`projects.open_archive()` wymagają parametru
  `encryption_password`, inaczej headless CI wisi/pada na dialogu, który
  `--noUI`/`--textPrompts` nie może obsłużyć. Hasło w CI pochodzi z
  sekretu repo `PROJECT_PASSWORD` (zmienna env `CODESYS_PROJECT_PASSWORD`
  we wszystkich trzech krokach - Compile/Deploy/Test). Nigdy nie
  zapisywać hasła w repo/logach. Patrz `README.md`.
- Pełny opis architektury i uzasadnienie decyzji: patrz `README.md`.
