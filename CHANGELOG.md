# Changelog

Wszystkie znaczące zmiany w tym repozytorium są odnotowywane w tym pliku.

## [Unreleased]

### Fixed
- Cache instalacji Dev System działa (`deploy-test` doszedł do kroku
  deploy w 1m43s zamiast 15m23s - download/extract/install całkowicie
  pominięte), ale jak podejrzewałem, sama usługa RTE dołączona przez
  installer Dev System **nie przetrwała** cache'owania samych plików
  (rejestracja usługi Windows to wpis SCM, nie plik) - `Install-CodesysRuntime.ps1`
  poprawnie wykrył brak usługi i zainstalował właściwy, samodzielny RTE
  z naszego zip-a, który jednak zakończył się kodem **3010**
  (`ERROR_SUCCESS_REBOOT_REQUIRED` - prawidłowy kod sukcesu Windows
  Installera, nie błąd). `Start-SilentInstall.ps1` traktował każdy
  niezerowy kod jako porażkę - teraz akceptuje 3010/3011 jako sukces
  (restart nieistotny na jednorazowej VM CI).

### Fixed
- `deploy-test` w CI padał na `KeyError: Name 'Gateway-1' not found.` -
  `configure_device_gateway()` zakładał, że gateway o tej nazwie zawsze
  istnieje (tak było na mojej maszynie testowej z historią użycia), ale
  świeży runner CI ma zero zarejestrowanych gateway. Naprawiono: bierze
  pierwszy istniejący gateway, a jeśli nie ma żadnego, tworzy nowy
  TCP/IP na `localhost:1217` (potwierdzone na przykładzie z forum
  CODESYS).

### Changed
- Dodano cache całego zainstalowanego katalogu Dev System
  (`actions/cache` na `C:\Program Files\CODESYS <wersja>`, oba joby) -
  instalacja (~14 min) powtarzała się w każdym z 2 jobów. Job `deploy-test`
  (`needs: build`) startuje po zapisaniu cache przez `build`, więc powinien
  dostać ją z cache w tym samym uruchomieniu. Nie jest to 100% pewne
  (cache to same pliki, nie rejestr/SCM - jeśli coś zależy od wpisów
  rejestru zrobionych przez instalator, może wyjść inny błąd przy trafieniu
  w cache) - do zweryfikowania w praktyce.

### Changed
- Job `build` (dodana wcześniej instalacja RTE w tym jobie, żeby
  zarejestrować opis urządzenia) okazała się no-opem w CI - usługa RTE
  była już zainstalowana przez sam instalator Dev System. Zamiast tego
  projekt teraz kompiluje/loguje się przez **`CICD.projectarchive`**
  (nowy plik, wygenerowany z `CICD.project` przez nowy
  `scripts/Update-ProjectArchive.ps1` - trzeba go regenerować i commitować
  po każdej zmianie projektu). `projects.open_archive()` samo instaluje
  opis urządzenia przy otwarciu, więc job `build` w ogóle nie potrzebuje
  już runtime. Usunięto z workflow zbędne kroki instalacji RTE w jobie
  `build` oraz przekazywanie artefaktu `compiled-project` między jobami
  (każdy job otwiera to samo `.projectarchive` z checkout).
- `scripts/codesys_build.py` / `codesys_deploy.py` / `codesys_test.py`:
  wydzielono wspólne helpery do nowego `scripts/codesys_common.py`
  (`write_junit`, `configure_device_gateway`).

### Fixed
- Nawet z zarejestrowanym opisem urządzenia, login nadal padał: najpierw
  `Gateway not configured properly` (świeżo otwarte archiwum ma zerowy
  GUID gateway na Device - `set_gateway_and_address` z samym IP też nie
  działa, bo lokalny runtime jest adresowany krótkim kodem przypisywanym
  przez gateway, nie adresem IP), potem `Currently, the user management is
  not activated on the device` (CODESYS Control >= SP17 domyślnie wymaga
  aktywowanego User Management, a świeży runtime go nie ma - interaktywne
  pytanie o aktywację nie da się obsłużyć headless, kończy się `The handle
  is invalid` nawet z `--textPrompts`). Naprawiono: `configure_device_gateway()`
  skanuje sieć przez `online.gateways['Gateway-1'].perform_network_scan()`
  i ustawia znaleziony adres (potwierdzone na oficjalnym przykładzie z forum
  CODESYS); `Install-CodesysRuntime.ps1` odkomentowuje
  `SECURITY.UserMgmtEnforce=NO` w każdym znalezionym `CODESYSControl.cfg`
  przed startem usługi (potwierdzone w oficjalnej dokumentacji CODESYS).
- `Expand-Installer.ps1`: archiwum RTE zawiera dwa pliki `.exe` poza
  `ISSetupPrerequisites` - wariant 32-bit (`CODESYS Control RTE
  3.5.22.30.exe`) i 64-bit (`CODESYS Control RTE 64 3.5.22.30.exe`).
  Dodano dopasowanie po `*64*` (sprawdzane przed `*Setup*`), żeby wybrać
  właściwy wariant x64 zamiast przerywać z błędem "multiple candidates".

### Fixed
- Job `build` na CI padał na kompilacji: `Build: Error: C188: Device not
  installed to the system. No code generation possible.` + kaskada
  `Could not open library '#...'` dla placeholderów (`IoStandard`,
  `CmpLog`, `CAA Types`, ...). Świeży Dev System nie ma zarejestrowanego
  opisu urządzenia dla targetu projektu (CODESYS Control Win V3 x64) -
  ten opis rejestruje się dopiero przy instalacji samego RTE. Job `build`
  instalował tylko Dev System, nigdy RTE (to robił dotąd wyłącznie
  `deploy-test`). Dodano do joba `build` te same kroki cache/pobrania/
  instalacji CODESYS Control Win V3 co w `deploy-test`, przed
  kompilacją - RTE nie jest tam uruchamiany, tylko instalowany (co
  rejestruje potrzebny opis urządzenia).

### Fixed
- Przetestowano lokalnie (na maszynie z realnie zainstalowanym CODESYS,
  zamiast czekać ~15 min na każdy przebieg CI) i znaleziono dwa kolejne
  realne błędy:
  - **Nazwa profilu**: `--profile="CODESYS V3.5 SP22"` samo w sobie nie
    jest prawidłową nazwą - zarejestrowany profil dla wersji 3.5.22.30 to
    `"CODESYS V3.5 SP22 Patch 3"` (potwierdzone wprost z argumentów
    skrótu w Menu Start). Ustawiono to jako domyślne w
    `Invoke-CodesysBuild.ps1`/`Invoke-CodesysDeploy.ps1`/`Invoke-CodesysTest.ps1`
    (parametr `-Profile`, można nadpisać do testów na innej wersji).
  - **Cudzysłowy w `--scriptargs`**: `Invoke-CodesysCli.ps1` łączył
    argumenty spacją bez indywidualnego cytowania każdego z nich - dla
    ścieżek zawierających spacje (np. lokalny checkout w folderze
    `Codesys CI CD`) tokenizer CODESYS rozbijał jedną ścieżkę na kilka
    argumentów, przez co skrypt dostawał ucięte, błędne wartości bez
    żadnego widocznego błędu (cichy exit code 1, brak raportu). Naprawiono
    przez owijanie każdego argumentu w cudzysłowy przed złączeniem.
  - `Start-SilentInstall.ps1`: podniesiono domyślny timeout z 15 do 40 min
    (obserwowane ~13 min na hostowanym runnerze, ale znacznie dłużej na
    wolniejszej maszynie) i naprawiono zabijanie na timeout - InstallShield
    odpala dalsze procesy `msiexec`, które nie kończyły się razem z
    procesem nadrzędnym; teraz zabijane jest całe drzewo procesów
    (`taskkill /T /F`).
- Zweryfikowano całe użycie CODESYS Scripting/CLI wobec oficjalnej
  dokumentacji (content.helpme-codesys.com, forum.codesys.com,
  forge.codesys.com) zamiast dalszego zgadywania - dwie poprzednie
  poprawki `--profile` (spacja, potem `=`) wciąż nie działały:
  - **CLI**: potwierdzony realny format to `--scriptargs:'arg1 arg2'`
    (dwukropek + pojedyncze cudzysłowy, argumenty oddzielone spacją), nie
    `--scriptargs="..."`. `Invoke-CodesysCli.ps1` buduje teraz cały string
    argumentów ręcznie w tym dokładnym formacie i zweryfikowano lokalnie
    (przez `cmd.exe echo`), że `Start-Process` przekazuje go do procesu
    bez zniekształceń.
  - **Python/scripting API**: usunięto niepotwierdzony `from scriptengine
    import projects, system` + wymyślone `app.build()`,
    `system.get_script_args()`, `system.exit_code = ...`,
    `app.get_device().set_communication_address(...)`. Zastąpiono
    potwierdzonymi wzorcami z oficjalnych przykładów: `from scriptengine
    import *` (jaw­ny odpowiednik automatycznego importu), argumenty przez
    zwykły `sys.argv`, kompilacja przez
    `project.active_application.generate_code()` + sprawdzenie
    `system.get_message_objects(CompileCategory, Severity.FatalError|Error)`,
    logowanie/start przez `online.create_online_application(app)` +
    `OnlineChangeOption`/`ApplicationState`, wyjście przez `system.exit(code)`.
  - Usunięto krok ustawiania adresu urządzenia (nigdzie niepotwierdzone
    API) - projekt musi już być skonfigurowany na localhost (tak jak przy
    lokalnym developmencie na tej samej maszynie co runtime).
  - `Install-CodesysRuntime.ps1`/`Invoke-CodesysTest.ps1`: nazwa usługi
    Windows dla runtime nie jest pewna (dokumentacja pokazuje różne
    warianty) - usługa jest teraz wyszukiwana dynamicznie po
    `DisplayName -like "*CODESYS Control*"` zamiast zgadywania sztywnej
    nazwy `CODESYSControlWinV3x64`.

### Fixed
- Poprzednia poprawka `--profile=...` nadal nie działała - komunikat błędu
  CODESYS.exe pokazuje wymagany format z **literalnymi cudzysłowami wokół
  wartości**: `--profile="profile name"`. PowerShell'owe cudzysłowy przy
  wywołaniu przez `&` chronią tylko przed rozbiciem po spacji na poziomie
  własnego parsowania linii poleceń, nie wstawiają cudzysłowu jako
  znaku do środka argumentu. Dodano `scripts/Invoke-CodesysCli.ps1`
  (wspólna funkcja dla build/deploy/test), który buduje cały string
  argumentów ręcznie (`--profile="..." --noUi --runscript="..."
  --scriptargs="..."`) i uruchamia przez `Start-Process`, dający pełną
  kontrolę nad cudzysłowami w linii poleceń.

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
