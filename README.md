# Codesys CI/CD

Projekt CODESYS (`PilaJednosuportowa.project`, CODESYS Control Win V3 x64, target
V3.5 SP22) wraz z pipeline'em CI, który automatycznie kompiluje projekt,
wgrywa go do runtime uruchomionego na hostowanym Windows runnerze GitHub
Actions i sprawdza, czy aplikacja faktycznie działa (RUN) — zwracając
raport z testów.

## Dlaczego to wygląda tak, a nie inaczej

CODESYS Development System (środowisko inżynierskie, w którym otwiera się
`PilaJednosuportowa.project`) **działa tylko na Windows** — nie ma wersji linuksowej ani
kontenerowej samego IDE. Sterujemy nim headless przez **CODESYS Scripting**
(Python/IronPython uruchamiany przez `CODESYS.exe --runscript=...`).

Runtime do testów (w Store występuje pod nazwą **CODESYS Control Win SL**,
w kodzie/skryptach nazywany zamiennie `CODESYS Control Win V3 x64` - to ten
sam produkt: V3 to generacja platformy, SL to typ licencji) instalujemy
**bezpośrednio
na tym samym runnerze**, bez Dockera i bez self-hosted maszyny: hostowany
runner GitHub (`windows-latest`) to i tak świeża, jednorazowa maszyna
wirtualna dla każdego joba, więc sama w sobie daje pełną izolację - kontener
nic by tu nie dodał. Zamiast cache'owania warstw obrazu, cache'ujemy
pobrane instalatory (`actions/cache`), żeby nie ściągać ich z prywatnego
storage przy każdym uruchomieniu; sama instalacja (silent install) i tak
odpala się w każdym jobie od nowa, bo maszyna jest za każdym razem czysta.

```
windows-latest (hostowany runner GitHub Actions, świeża VM per job)
├── CODESYS Development System (kompilacja, CODESYS Scripting)
└── CODESYS Control Win V3 x64 (runtime, zainstalowany jako usługa Windows, gateway :1217)
```

## Struktura repo

```
PilaJednosuportowa.project           - projekt CODESYS
PilaJednosuportowa.projectarchive    - wygenerowane archiwum projektu (patrz sekcja niżej) - NIE
                                       edytować ręcznie, NIE commitować (git-ignored, ~120 MB -
                                       wgrywane jako asset GitHub Release, patrz niżej)
installers/
  README.md                         - skąd biorą się instalatory (licencja, prywatny storage, .zip)
                                       (same archiwa/instalatory są git-ignored)
scripts/
  Assert-ValidZip.ps1               - walidacja pobranego .zip (rozmiar, sygnatura PK)
  Assert-ValidExe.ps1               - walidacja rozpakowanego .exe (rozmiar, sygnatura MZ)
  Expand-Installer.ps1              - rozpakowuje .zip i znajduje właściwy .exe w środku
  Install-CodesysDevSystem.ps1      - silent install CODESYS Development System
  Install-CodesysRuntime.ps1        - silent install + start CODESYS Control Win V3 (usługa),
                                       wyłącza wymuszone User Management (patrz niżej)
  Update-ProjectArchive.ps1         - (re)generuje PilaJednosuportowa.projectarchive z
                                       PilaJednosuportowa.project - uruchom LOKALNIE tylko gdy
                                       zmienia się target/urządzenie/biblioteki, patrz sekcja niżej
  codesys_common.py                 - wspólne helpery (zapis JUnit, ustawienie gateway/adresu urządzenia)
  codesys_build.py                  - CODESYS Scripting: kompilacja projektu (z .projectarchive)
  codesys_deploy.py                 - CODESYS Scripting: login + download + start na runtime
  codesys_test.py                   - CODESYS Scripting: weryfikacja stanu RUN (smoke test)
  codesys_save_archive.py           - CODESYS Scripting użyty przez Update-ProjectArchive.ps1
  Invoke-CodesysBuild.ps1            - wrapper PowerShell dla etapu build
  Invoke-CodesysDeploy.ps1           - wrapper PowerShell dla etapu deploy (install RTE + login/download/start)
  Invoke-CodesysTest.ps1             - wrapper PowerShell dla etapu test (+ zbiera log, stopuje usługę)
  Write-Summary.ps1                 - zbiera junit-*.xml w jeden raport Markdown (GitHub Job Summary)
.github/workflows/codesys-ci.yml    - workflow GitHub Actions (1 job: build-deploy-test)
reports/                            - wygenerowane raporty JUnit XML + log runtime (git-ignored)
work/                                - katalogi robocze rozpakowanego .projectarchive (git-ignored)
```

## PilaJednosuportowa.projectarchive - do czego służy (i do czego NIE)

Świeża instalacja CODESYS Development System (taka jak na CI) nie ma
zarejestrowanego **opisu urządzenia** (device description) dla targetu
projektu - otwarcie samego `PilaJednosuportowa.project` pada wtedy przy
kompilacji z
`C188: Device not installed to the system. No code generation possible.`
i kaskadą nierozwiązanych bibliotek placeholderowych. `.projectarchive`
bundluje opis urządzenia razem z projektem, a `projects.open_archive()`
instaluje go automatycznie przy otwarciu - ale ta instalacja trafia do
**współdzielonego, ogólnomaszynowego repozytorium urządzeń**
(`C:\ProgramData\CODESYS\Devices`), nie tylko do projektu z archiwum.

Dlatego archiwum jest używane wyłącznie do jednorazowego "primingu" na
początku joba (`codesys_build.py` otwiera je i od razu zamyka) - **kod
zawsze pochodzi z żywego `PilaJednosuportowa.project`**, otwieranego
normalnie przez `projects.open()` we wszystkich trzech etapach
(build/deploy/test). Zmiana kodu w `PilaJednosuportowa.project` nie
wymaga regenerowania archiwum.

Archiwum jest przy tym duże (~120 MB, dla tego projektu ponad limit
100 MB na plik w commicie do GitHub) - dlatego jest git-ignored i
wgrywane jako asset **prywatnego GitHub Release** (tag `ProjectArchive`),
skąd workflow ściąga je przez `gh release download` przed etapem build
(bez cache'owania - w przeciwieństwie do instalatorów CODESYS to
właśnie ten plik zmienia się razem z projektem, więc cache mógłby
"primować" nieaktualnym urządzeniem).

**Kiedy trzeba zregenerować `PilaJednosuportowa.projectarchive`:** tylko
gdy zmienia się sam **target/urządzenie** projektu (inny model PLC,
inna wersja urządzenia) albo zestaw bibliotek, na maszynie z już
zainstalowanym CODESYS (i zainstalowanym CODESYS Control Win V3 -
inaczej samo urządzenie nie będzie zarejestrowane do zapisania w
archiwum), a potem trzeba wgrać wynikowy plik jako nowy asset do
Release `ProjectArchive` (nadpisując poprzedni):

```powershell
$env:CODESYS_PROJECT_PASSWORD = "..."   # projekt jest zaszyfrowany, patrz niżej
./scripts/Update-ProjectArchive.ps1
gh release upload ProjectArchive PilaJednosuportowa.projectarchive --clobber
```

## Zaszyfrowany projekt

`PilaJednosuportowa.project`/`.projectarchive` są zabezpieczone hasłem
szyfrowania projektu (CODESYS "Encryption Password" - Project Properties
> Protection). Bez podania hasła `projects.open()` /
`projects.open_archive()` w CODESYS Scripting wyświetlają modalny dialog
"Encryption Password", który pod `--noUI`/`--textPrompts` nic nie może
obsłużyć - kończy się to błędem `StandardError: Operation cancelled by
user.`. Hasło jest przekazywane jako `encryption_password` do obu tych
wywołań (patrz `scripts/codesys_build.py`, `codesys_deploy.py`,
`codesys_test.py`, `codesys_save_archive.py`), a w CI pochodzi z sekretu
repo **`PROJECT_PASSWORD`** (`gh secret set PROJECT_PASSWORD`), wstrzykiwanego
jako zmienna środowiskowa `CODESYS_PROJECT_PASSWORD` do kroków Compile/
Deploy/Test w workflow - nigdy nie jest zapisywane w repo ani logowane.

## Etapy pipeline'u (jeden job CI)

Workflow [`codesys-ci.yml`](.github/workflows/codesys-ci.yml) uruchamia
się na push/PR do `master` oraz ręcznie (`workflow_dispatch`), na hostowanym
runnerze `windows-latest`, jako **jeden job** (`build-deploy-test`) z
trzema etapami po sobie:

1. **build** — cache/pobranie instalatora CODESYS Development System,
   instalacja, pobranie `PilaJednosuportowa.projectarchive` z Release
   `ProjectArchive` i "priming" repozytorium urządzeń (otwórz i zamknij),
   otwarcie i kompilacja żywego `PilaJednosuportowa.project`
   ([`codesys_build.py`](scripts/codesys_build.py)). Publikuje
   `reports/junit-build.xml` jako artefakt.
2. **deploy** — instaluje CODESYS Control Win V3 x64 (jako usługa Windows;
   przy instalacji wyłączane jest też wymuszone User Management runtime -
   patrz niżej), po czym przez CODESYS Scripting
   ([`codesys_deploy.py`](scripts/codesys_deploy.py)) otwiera
   `PilaJednosuportowa.project`, skanuje sieć przez lokalny gateway żeby znaleźć adres
   runtime (świeżo otwarty projekt nie ma ustawionego adresu urządzenia),
   loguje się, wgrywa (download) i uruchamia aplikację - odpytując przez
   do 10s czy stan RUN faktycznie się utrwalił po `start()`. Publikuje
   `reports/junit-deploy.xml`.
3. **test** — ([`codesys_test.py`](scripts/codesys_test.py)) loguje się
   ponownie, niezależnie, w trybie tylko-monitorowania i sprawdza, czy PLC
   jest w stanie RUN. Na końcu zawsze zbiera log runtime i zatrzymuje
   usługę (choć i tak cała VM zostanie usunięta po jobie). Publikuje
   `reports/junit-test.xml` jako artefakt oraz jako czytelne podsumowanie
   testów w GitHub Actions.

Błąd kompilacji (etap 1) zatrzymuje job od razu - domyślne zachowanie
GitHub Actions: nieudany krok przerywa pozostałe kroki w tym samym jobie
- więc etapy deploy/test w ogóle się nie odpalą, mimo że wszystko jest w
jednym jobie. Trzy etapy to jeden job (nie osobne joby jak wcześniej),
bo Dev System nie da się bezpiecznie cache'ować między jobami (patrz
komentarz w workflow) - rozdzielenie na 2 joby oznaczało instalowanie go
dwa razy (~26 min zamiast ~13 min). Każdy etap ma osobny raport JUnit,
więc mimo wspólnego joba i tak od razu widać, czy problem jest przy
kompilacji, wgrywaniu, czy dopiero przy weryfikacji działania.

## Raport z przebiegu (Job Summary)

Ostatni krok workflow (`Write consolidated report`,
[`Write-Summary.ps1`](scripts/Write-Summary.ps1), zawsze uruchamiany,
nawet po niepowodzeniu wcześniejszego etapu) czyta wszystkie istniejące
`reports/junit-*.xml` i składa je w jeden raport Markdown, wypisywany do
[GitHub Job Summary](https://github.blog/2022-05-09-supercharging-github-actions-with-job-summaries/)
- widoczny od razu na górze strony przebiegu w zakładce Actions, bez
przeszukiwania logów. Dla etapu który padł widać pełną treść błędu (np.
listę błędów kompilacji, jeden pod drugim), dla etapów które się nie
odpaliły (bo wcześniejszy etap przerwał pipeline) - wyraźne oznaczenie
"nie uruchomiono".

## Wymuszone User Management na runtime

CODESYS Control >= SP17 domyślnie wymaga aktywowanego zarządzania
użytkownikami przed jakimkolwiek logowaniem inżynierskim - świeży runtime
(jak na CI) nie ma go jeszcze aktywowanego, co normalnie skutkuje
interaktywnym pytaniem "would you like to activate it now? create an
admin user...", którego nic w headless CI nie może obsłużyć (kończy się
błędem `The handle is invalid`, nawet z `--textPrompts`).
`Install-CodesysRuntime.ps1` odkomentowuje `SECURITY.UserMgmtEnforce=NO`
w każdym znalezionym `CODESYSControl.cfg` przed startem usługi (patrz
[dokumentacja CODESYS](https://content.helpme-codesys.com/en/CODESYS%20Development%20System/_cds_sec_faq_deactivating_usermanagement.html)).

## Wymagania

- Brak self-hosted runnera i Dockera — wystarczy standardowy hostowany
  `windows-latest` (dostępny od razu dla repo/organizacji na GitHub).
- Instalatory CODESYS (Development System + Control Win V3 x64/Control Win
  SL) wgrane jako assety prywatnego GitHub Release (tag `Installers`) w
  tym repo — pobierane w workflow przez `gh release download` z wbudowanym
  `GITHUB_TOKEN`, bez żadnego zewnętrznego hostingu/sekretów URL. Patrz
  [`installers/README.md`](installers/README.md) po szczegóły, dokładne
  nazwy assetów i jak podmienić wersję (CODESYS Store wymaga logowania,
  więc nie da się tego pobrać anonimowo bezpośrednio w workflow — stąd ten
  pośredni krok).
- Licencja CODESYS Development System musi dopuszczać headless build na
  świeżej maszynie w każdym uruchomieniu CI (jeśli licencja wymaga
  aktywacji online per-maszyna, może to wymagać licencji floating/CmC albo
  dodatkowego kroku aktywacji - do zweryfikowania z posiadaną licencją).
  Runtime bez licencji działa w trybie demo (ograniczony czas ciągłej
  pracy), co wystarcza na krótki smoke test w CI.

## Praca z repo

Zasady współpracy z Claude nad tym repo (commity lokalne, changelog, brak
automatycznego push) są opisane w [`CLAUDE.md`](CLAUDE.md). Historia zmian
prowadzona jest w [`CHANGELOG.md`](CHANGELOG.md).
