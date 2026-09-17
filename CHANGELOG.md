# Changelog

Wszystkie znaczące zmiany w tym repozytorium są odnotowywane w tym pliku.

## [Unreleased]

### Fixed
- Instalacja CODESYS Development System w końcu przeszła (trwała ~13 min -
  to był legalnie długi install kilku zależności typu VC++ redist/.NET,
  nie zawieszenie), ale kompilacja padała z błędem CODESYS.exe: "When
  running in --noUI mode, you must specify a profile using
  --profile=...". CODESYS CLI wymaga formatu `--flag=wartość` (ze znakiem
  `=`), a nie `--flag wartość` (spacja) jak było wcześniej. Poprawiono
  `--profile`/`--scriptargs` na format z `=` w `Invoke-CodesysBuild.ps1`,
  `Invoke-CodesysDeploy.ps1`, `Invoke-CodesysTest.ps1`.

### Fixed
- Job `build` wisiał 50+ minut na kroku instalacji CODESYS Development
  System: flaga `/S` (NSIS) była błędna dla tego instalatora
  (InstallShield-wrapped MSI) - prawdopodobnie próbował pokazać UI, na
  które nikt w headless CI nie mógł kliknąć. Poprawiono na `/s /v/qn`
  (InstallShield silent + quiet-MSI) w `Install-CodesysDevSystem.ps1` i
  `Install-CodesysRuntime.ps1`. Dodano `scripts/Start-SilentInstall.ps1`:
  wspólna logika uruchamiania instalatora z twardym timeoutem (domyślnie
  15 min) - zła flaga silent w przyszłości przerwie job czytelnym błędem
  zamiast wisieć aż do limitu czasu joba. Zawieszony run CI ręcznie
  anulowany (`gh run cancel`).

### Fixed
- `scripts/Expand-Installer.ps1`: instalator CODESYS Development System to
  pakiet InstallShield, który poza właściwym `.exe` zawiera dodatkowe
  instalatory-wymagania (VC++ redist, .NET, silnik InstallShield) w
  podfolderze `ISSetupPrerequisites`. Wybór pliku wykluczał teraz te
  podfoldery zamiast polegać wyłącznie na dopasowaniu nazwy do `*Setup*`
  (rzeczywisty plik to `CODESYS 64 3.5.22.30.exe`, bez słowa "Setup").

### Changed
- Instalatory CODESYS przeniesione z pomysłu "link do prywatnego storage +
  sekrety URL" na **assety prywatnego GitHub Release** (tag `Installers`,
  assety `CODESYS.64.3.5.22.30.zip` i `CODESYS.Control.RTE.SL.3.5.22.30.zip`)
  w tym samym repo. Workflow pobiera je przez `gh release download` z
  wbudowanym `GITHUB_TOKEN` zamiast `Invoke-WebRequest` + sekrety
  `CODESYS_DEVSYS_INSTALLER_URL` / `CODESYS_RTE_INSTALLER_URL` (usunięte -
  nieużywane). Eliminuje to problemy z linkami do stron
  podglądu/udostępniania (Synology Drive) zamiast bezpośrednich plików.
  `installers/README.md` zaktualizowany o nowy sposób i instrukcję
  podmiany wersji.

### Fixed
- Instalatory CODESYS Store dostarczane są jako **archiwa .zip**, nie
  gołe `.exe` - workflow pobierał plik pod nazwą `...Setup.exe`, ale
  faktyczna zawartość to zip, stąd błąd `Start-Process: ... corrupted and
  unreadable`. Zmieniono pobieranie na `.zip` (`installers\*.zip`,
  cache'owane jak wcześniej) + dodano krok rozpakowania
  (`scripts/Expand-Installer.ps1`, wyszukuje `.exe` w archiwum) przed
  wywołaniem `Install-CodesysDevSystem.ps1` / `Invoke-CodesysDeploy.ps1`.
  Dodano `scripts/Assert-ValidZip.ps1` (walidacja sygnatury `PK`) obok
  istniejącego `Assert-ValidExe.ps1`.

### Fixed
- `scripts/Assert-ValidExe.ps1`: walidacja pobranego instalatora (rozmiar,
  sygnatura `MZ`) tuż po `Invoke-WebRequest` w workflow oraz w
  `Install-CodesysDevSystem.ps1` / `Install-CodesysRuntime.ps1`. Zapobiega
  mylącemu błędowi `Start-Process: ... corrupted and unreadable`, gdy link
  do instalatora (np. share Synology) zwraca stronę HTML zamiast realnego
  pliku `.exe`. `installers/README.md` opisuje jak to sprawdzić (`curl -I`)
  i naprawić URL.

### Fixed
- Poprawiono numer wersji CODESYS z `3.5.22.0` na faktyczny `3.5.22.30`
  (potwierdzony na stronach store.codesys.com dla "CODESYS Development
  System 3" i "CODESYS Control Win SL") w workflow oraz domyślnych
  ścieżkach `C:\Program Files\CODESYS ...` we wszystkich skryptach.
- Doprecyzowano w README/CLAUDE.md, że oficjalna nazwa runtime w Store to
  "CODESYS Control Win SL" (używana zamiennie z "Control Win V3 x64").

### Changed
- Zrezygnowano z Dockera i self-hosted runnera na rzecz hostowanych
  runnerów GitHub `windows-latest`: świeża maszyna wirtualna per job daje
  wystarczającą izolację, więc CODESYS Control Win V3 x64 (runtime) jest
  teraz instalowany bezpośrednio na runnerze jako usługa Windows zamiast
  w kontenerze. Usunięto katalog `docker/` (Dockerfile, entrypoint.ps1,
  docker-compose.yml).
- Pipeline CI zredukowany z 3 do 2 jobów w `.github/workflows/codesys-ci.yml`:
  `build` → `deploy-test` (etapy deploy i test zostały połączone w jeden
  job, bo na hostowanym runnerze każdy job to osobna, świeża VM - etap
  testu potrzebuje tej samej, już uruchomionej usługi runtime co etap
  deployu). Dodano cache'owanie instalatorów przez `actions/cache` oraz
  przekazywanie skompilowanego projektu między jobami przez artefakt
  `compiled-project`.

### Added
- `scripts/Install-CodesysDevSystem.ps1` i `scripts/Install-CodesysRuntime.ps1`
  — idempotentna, cicha instalacja CODESYS Development System i CODESYS
  Control Win V3 x64 bezpośrednio na runnerze.
- `installers/README.md` — wyjaśnienie, skąd biorą się instalatory
  (wymagane logowanie do CODESYS Store) i jak są dostarczane do CI
  (prywatny storage + sekrety `CODESYS_DEVSYS_INSTALLER_URL` /
  `CODESYS_RTE_INSTALLER_URL`).

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
