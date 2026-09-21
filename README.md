# Codesys CI/CD

Projekt CODESYS (`CICD.project`, CODESYS Control Win V3 x64, target
V3.5 SP22) wraz z pipeline'em CI, który automatycznie kompiluje projekt,
wgrywa go do runtime uruchomionego na hostowanym Windows runnerze GitHub
Actions i sprawdza, czy aplikacja faktycznie działa (RUN) — zwracając
raport z testów.

## Dlaczego to wygląda tak, a nie inaczej

CODESYS Development System (środowisko inżynierskie, w którym otwiera się
`CICD.project`) **działa tylko na Windows** — nie ma wersji linuksowej ani
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
CICD.project                        - projekt CODESYS
CICD.projectarchive                 - wygenerowane archiwum projektu (patrz sekcja niżej) - NIE edytować ręcznie
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
  Update-ProjectArchive.ps1         - (re)generuje CICD.projectarchive z CICD.project - uruchom
                                       LOKALNIE po każdej zmianie projektu, patrz sekcja niżej
  codesys_common.py                 - wspólne helpery (zapis JUnit, ustawienie gateway/adresu urządzenia)
  codesys_build.py                  - CODESYS Scripting: kompilacja projektu (z .projectarchive)
  codesys_deploy.py                 - CODESYS Scripting: login + download + start na runtime
  codesys_test.py                   - CODESYS Scripting: weryfikacja stanu RUN (smoke test)
  codesys_save_archive.py           - CODESYS Scripting użyty przez Update-ProjectArchive.ps1
  Invoke-CodesysBuild.ps1            - wrapper PowerShell dla etapu build
  Invoke-CodesysDeploy.ps1           - wrapper PowerShell dla etapu deploy (install RTE + login/download/start)
  Invoke-CodesysTest.ps1             - wrapper PowerShell dla etapu test (+ zbiera log, stopuje usługę)
.github/workflows/codesys-ci.yml    - workflow GitHub Actions (joby: build, deploy-test)
reports/                            - wygenerowane raporty JUnit XML + log runtime (git-ignored)
work/                                - katalogi robocze rozpakowanego .projectarchive (git-ignored)
```

## CICD.projectarchive - dlaczego to nie tylko CICD.project

Świeża instalacja CODESYS Development System (taka jak na CI) nie ma
zarejestrowanego **opisu urządzenia** (device description) dla targetu
projektu - otwarcie samego `CICD.project` pada wtedy przy kompilacji z
`C188: Device not installed to the system. No code generation possible.`
i kaskadą nierozwiązanych bibliotek placeholderowych. `.projectarchive`
bundluje opis urządzenia razem z projektem, a `projects.open_archive()`
instaluje go automatycznie przy otwarciu - dlatego `codesys_build.py` /
`codesys_deploy.py` / `codesys_test.py` otwierają **archiwum**, nie plik
`.project` bezpośrednio.

**Ważne:** `CICD.projectarchive` trzeba wygenerować LOKALNIE, na maszynie
z już zainstalowanym CODESYS (i zainstalowanym CODESYS Control Win V3 -
inaczej samo urządzenie nie będzie zarejestrowane do zapisania w
archiwum), i commitować razem z `CICD.project` po każdej jego zmianie:

```powershell
./scripts/Update-ProjectArchive.ps1
```

## Etapy pipeline'u (joby CI)

Workflow [`codesys-ci.yml`](.github/workflows/codesys-ci.yml) uruchamia
się na push/PR do `master` oraz ręcznie (`workflow_dispatch`), na hostowanych
runnerach `windows-latest`, jako dwa joby:

1. **build** — cache/pobranie instalatora CODESYS Development System,
   instalacja, otwarcie i kompilacja `CICD.projectarchive`
   ([`codesys_build.py`](scripts/codesys_build.py)). Runtime nie jest tu
   potrzebny wcale - opis urządzenia przychodzi z archiwum. Publikuje
   `reports/junit-build.xml` jako artefakt. Błąd kompilacji przerywa
   pipeline od razu.
2. **deploy-test** — instaluje CODESYS Development System oraz CODESYS
   Control Win V3 x64 (jako usługa Windows; przy instalacji wyłączane jest
   też wymuszone User Management runtime - patrz niżej), po czym przez
   CODESYS Scripting ([`codesys_deploy.py`](scripts/codesys_deploy.py))
   skanuje sieć przez lokalny gateway żeby znaleźć adres runtime (świeżo
   otwarte archiwum nie ma ustawionego adresu urządzenia), loguje się,
   wgrywa (download) i uruchamia aplikację. Następnie
   ([`codesys_test.py`](scripts/codesys_test.py)) loguje się ponownie w
   trybie tylko-monitorowania i sprawdza, czy PLC jest w stanie RUN. Na
   końcu zawsze zbiera log runtime i zatrzymuje usługę (choć i tak cała VM
   zostanie usunięta po jobie). Publikuje `reports/junit-deploy.xml` i
   `reports/junit-test.xml` jako artefakty oraz `junit-test.xml` jako
   czytelne podsumowanie testów w GitHub Actions.

Deploy i test są rozdzielone na osobne kroki z osobnymi raportami JUnit
(nie osobne joby - bo etap testu potrzebuje tej samej, już uruchomionej
usługi runtime co etap deployu, a każdy job GitHub Actions to inna VM),
więc i tak od razu widać, czy problem jest przy wgrywaniu, czy dopiero przy
weryfikacji działania.

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
