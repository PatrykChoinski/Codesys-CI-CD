# Changelog

Wszystkie znaczące zmiany w tym repozytorium są odnotowywane w tym pliku.

## [Unreleased]

### Added
- Raport kompilacji podaje przy każdym błędzie obiekt (ścieżka POU w
  drzewie projektu) i pozycję, np. `Error C4: 'iEncoderImpulse' is no
  component of 'IoConfig_Globals_Mapping' [Device/Plc Logic/Application/
  Settings/Encoders, Line 7, Column 1 (Impl)]` - w `junit-build.xml`, w
  Job Summary oraz jako adnotacje `::error::` na stronie runu (widoczne
  bez dostępu do logów). Formatowanie w `format_compile_message()`
  (`scripts/codesys_common.py`). Błąd kompilacji tego projektu po
  podmianie AX8 -> Win V3 x64 jest oczekiwany (zmienna z wbudowanego I/O
  AX8) - test ma go zgłaszać.

### Fixed
- Podmiana urządzenia w CI padała z `The object 'Device' could not be
  saved. (Reason: The handle is invalid.)` - projekt jest z
  DIADesigner-AX 1.10, więc zmiana urządzenia pyta o podniesienie formatu
  zapisu do SP22 (prompt `LossOfDataWarning2`), a headless CI nie ma
  stdin. `retarget_device()` na czas `update()` włącza
  `PromptHandling.LogSimplePrompts` (domyślne "Yes", tylko w pamięci).
- Po podmianie urządzenia znikały referencje bibliotek dodawane przez
  urządzenie AX8 (`SM3_Basic`, `SM3_CNC`, `SM3_Drive_ETC`, ...), a
  placeholdery rozwiązywały się inaczej (501 błędów kompilacji).
  `retarget_device()` teraz: dodaje z powrotem placeholdery, które
  zniknęły; przekierowuje nierozwiązane na najnowszą zainstalowaną
  bibliotekę o tej samej nazwie (SoftMotion -> 4.19/4.20); przypina do
  wersji z AX8 placeholdery z nowej zmiennej workflow
  `CODESYS_KEEP_PLACEHOLDERS` (domyślnie `IecVarAccess` - 4.6.0.0 z Win
  V3 x64 kłóci się z `SymbolicVarsBase` projektu). Zweryfikowane lokalnie
  na CODESYS 3.5.22.30: 501 -> 2 błędy. Pozostałe 2 (`Encoders`, linia 7,
  `IoConfig_Globals_Mapping.iEncoderImpulse`) to zmienna zmapowana na
  wbudowane I/O sterownika AX8, którego Win V3 x64 nie ma.

### Changed
- CI podmienia w projekcie urządzenie AX8 (którego nie ma na runnerze) na
  `CODESYS Control Win V3 x64` 3.5.22.30 (`4096|0000 0004`) przed
  kompilacją, deployem i testem - nowa funkcja `retarget_device()` w
  `scripts/codesys_common.py` (odpowiednik "Update Device" w IDE,
  `ScriptDeviceObject.update(...)`), sterowana zmienną
  `CODESYS_TARGET_DEVICE` w workflow (pusta = bez podmiany). Zmiana
  tylko w pamięci/na runnerze - `PilaJednosuportowa.project` w repo
  nadal ma AX8. W SP22/SoftMotion 4.x nie ma osobnego urządzenia
  "Win V3 x64 SoftMotion" - SoftMotion działa na zwykłym Win V3 x64.
- Zastąpiono testowy projekt `CICD.project`/`CICD.projectarchive`
  prawdziwym projektem `PilaJednosuportowa.project`/
  `PilaJednosuportowa.projectarchive` - zaktualizowano wszystkie
  domyślne ścieżki w skryptach (`Invoke-CodesysBuild.ps1`,
  `Invoke-CodesysDeploy.ps1`, `Invoke-CodesysTest.ps1`,
  `Update-ProjectArchive.ps1`) oraz komentarze/dokumentację
  (`README.md`, `CLAUDE.md`). Archiwum tego projektu ma ~120 MB - ponad
  limit 100 MB na plik w commicie do GitHub - więc przestało być
  commitowane do git (dodane do `.gitignore`) i jest teraz wgrywane jako
  asset prywatnego GitHub Release (nowy tag `ProjectArchive`), skąd
  workflow ściąga je świeżo przy każdym uruchomieniu (bez cache'owania,
  w przeciwieństwie do instalatorów CODESYS - to ten plik zmienia się
  razem z projektem, więc cache mógłby "primować" nieaktualnym
  urządzeniem).

### Fixed
- Naprawiono błąd składni ST w projekcie (`C189`/`C9`/`C190` -
  nieoczekiwany token `!` zamiast `;`), który celowo wprowadzono wcześniej
  do testu ścieżki błędu w CI (dotyczyło jeszcze poprzedniego, testowego
  projektu `CICD.project`). Kompilacja powinna teraz przechodzić.
- Lokalny test kompilacji `PilaJednosuportowa.project` padał na
  `StandardError: Operation cancelled by user.` w `projects.open_archive()`
  - okazało się, że projekt/archiwum jest zaszyfrowane hasłem (dialog
  "Encryption Password", który `--noUI`/`--textPrompts` nie może
  obsłużyć headless). Naprawiono przez dodanie parametru
  `encryption_password` do wszystkich wywołań `projects.open()` /
  `projects.open_archive()` (`codesys_build.py`, `codesys_deploy.py`,
  `codesys_test.py`, `codesys_save_archive.py`), zasilanego z nowego
  sekretu repo `PROJECT_PASSWORD` przez zmienną env
  `CODESYS_PROJECT_PASSWORD` we wszystkich trzech krokach workflow.
- Po naprawie hasła, lokalny test kompilacji przechodził (`0 errors, 95
  warnings: Ready for download`), ale cały etap build i tak kończył się
  błędem - `project.save()` w `codesys_build.py` (optymalizacja: zapisuje
  skompilowany stan na dysk, żeby DEPLOY nie musiał kompilować od nowa)
  padał z `StandardError: The project could not be saved... This project
  has been opened in read-only mode`, bo prawdziwy projekt ma ustawiony
  status "Released" w CODESYS (tryb tylko-do-odczytu). `project.save()`
  jest teraz owinięty w osobny try/except, który tylko loguje ostrzeżenie
  - nieudany zapis (best-effort, opcjonalny) nie może już zmieniać
  udanej kompilacji w failed build.

### Changed
- `CICD.projectarchive` używane teraz TYLKO do "primingu" repozytorium
  urządzeń (`codesys_build.py` otwiera je i od razu zamyka na początku
  joba) - kod aplikacji zawsze pochodzi z żywego `CICD.project`, otwieranego
  normalnie przez `projects.open()` we wszystkich trzech etapach. Wcześniej
  wszystkie trzy etapy otwierały samo archiwum, co wymagało jego
  regeneracji po KAŻDEJ zmianie kodu - teraz archiwum trzeba regenerować
  tylko przy zmianie targetu/urządzenia albo bibliotek. Zadziałało dzięki
  temu, że instalacja opisu urządzenia z archiwum trafia do
  współdzielonego, ogólnomaszynowego repozytorium (`C:\ProgramData\CODESYS\Devices`),
  nie tylko do projektu otwartego z tego konkretnego archiwum.

### Added
- `scripts/Write-Summary.ps1` + krok `Write consolidated report` (ostatni
  w workflow, `if: always()`) - zbiera wszystkie istniejące
  `reports/junit-*.xml` w jeden raport Markdown wypisywany do GitHub Job
  Summary (widoczny na górze strony przebiegu, bez przeszukiwania logów).
  Dla nieudanego etapu pokazuje pełną treść błędu (np. listę błędów
  kompilacji w blokach kodu), dla nieodpalonych etapów - "nie
  uruchomiono".

### Fixed
- `write_junit()` w `codesys_common.py` trzymał treść błędu w atrybucie
  XML `message="..."` - normalizacja białych znaków w atrybutach XML
  zlepia wieloliniowe błędy kompilacji w jedną linię przy odczycie.
  Przeniesiono treść do zawartości tekstowej elementu `<failure>`, co
  zachowuje podziały linii. Dodano też wymuszone kodowanie UTF-8 przy
  zapisie pliku raportu.

### Fixed
- Pierwszy przebieg pojedynczego joba: build i deploy przeszły (deploy
  poprawnie potwierdził stan RUN po `start()`), ale `test` znowu znalazł
  aplikację w stanie `stop`, mimo "The application is up to date". Jedyna
  różnica względem deployu: `codesys_test.py` logował się z
  `always_update=False`. Skoro test otwiera `.projectarchive` do INNEGO
  `extract_dir` niż deploy, wynikowa aplikacja rozruchowa najpewniej nigdy
  nie jest bajt-identyczna nawet z tego samego źródła - z `False` CODESYS
  zdaje się w takiej sytuacji zatrzymywać aplikację zamiast zostawić ją
  bez zmian. Zmieniono na `always_update=True` (jak w deployu, zgodnie z
  oficjalnym przykładem z forum) i dodano taki sam retry `start()` +
  odpytywanie stanu przez do 10s jak w deployu.

### Changed
- Pipeline CI z powrotem jako **1 job** (`build-deploy-test`) zamiast
  2 (`build` → `deploy-test`) - skoro cache instalacji Dev System między
  jobami nie działa (patrz wpis wyżej), rozdzielenie na 2 joby oznaczało
  instalowanie go dwa razy (~26 min zamiast ~13 min). Kroki w jednym jobie
  są sekwencyjne, więc błąd kompilacji nadal zatrzymuje deploy/test
  automatycznie (domyślne zachowanie GitHub Actions), bez utraty
  "fail-fast" które dawał podział na joby - tylko już bez podwójnej
  instalacji.

### Fixed
- Pierwszy pełny przebieg CI, w którym deploy (login/download/start)
  faktycznie przeszedł (fix gateway + user management + kod 3010 zadziałały
  razem) - ale test padł: `Application state was stop, expected run`.
  Kod się zgadzał ("The application is up to date"), więc to nie problem
  z nie-deterministycznym rekompilowaniem w osobnym `extract_dir` - `start()`
  w deployu prawdopodobnie nie zdążyło/nie utrwaliło się zanim skrypt się
  wylogował. `codesys_deploy.py` teraz odpytuje stan przez do 10s po
  `start()` i traktuje brak stanu RUN jako błąd deployu (zamiast mylącego
  błędu dopiero w oddzielnym etapie test).

### Reverted
- Cache całego katalogu instalacji Dev System (dodany wcześniej) wycofany
  - `CODESYS.exe` wisiał w nieskończoność (52+ min zanim ręcznie anulowano
  run) po restarcie z cache samych plików, najpewniej na niewidzialnym
  dialogu "Select Profile" - instalator ustawia coś (rejestr?) czego
  samo skopiowanie plików nie odtwarza. Zostaje tylko cache pobranego
  `.zip` (bezpieczny, nie wpływa na sam install), a właściwa instalacja
  (~14 min) znowu uruchamia się w każdym jobie.

### Added
- `timeout-minutes` na poziomie joba (`build`: 30, `deploy-test`: 45) -
  domyślny limit GitHub Actions to 6h; po powyższym zawieszeniu (musiałem
  ręcznie zauważyć i anulować po 52 min) to zbyt duży margines błędu.

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
