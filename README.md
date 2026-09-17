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
installers/
  README.md                         - skąd biorą się instalatory (licencja, prywatny storage)
                                       (same instalatory .exe są git-ignored)
scripts/
  Install-CodesysDevSystem.ps1      - silent install CODESYS Development System
  Install-CodesysRuntime.ps1        - silent install + start CODESYS Control Win V3 (usługa)
  codesys_build.py                  - CODESYS Scripting: kompilacja projektu
  codesys_deploy.py                 - CODESYS Scripting: login + download + start na runtime
  codesys_test.py                   - CODESYS Scripting: weryfikacja stanu RUN (smoke test)
  Invoke-CodesysBuild.ps1            - wrapper PowerShell dla etapu build
  Invoke-CodesysDeploy.ps1           - wrapper PowerShell dla etapu deploy (install RTE + login/download/start)
  Invoke-CodesysTest.ps1             - wrapper PowerShell dla etapu test (+ zbiera log, stopuje usługę)
.github/workflows/codesys-ci.yml    - workflow GitHub Actions (joby: build, deploy-test)
reports/                            - wygenerowane raporty JUnit XML + log runtime (git-ignored)
```

## Etapy pipeline'u (joby CI)

Workflow [`codesys-ci.yml`](.github/workflows/codesys-ci.yml) uruchamia
się na push/PR do `master` oraz ręcznie (`workflow_dispatch`), na hostowanych
runnerach `windows-latest`, jako dwa joby:

1. **build** — cache/pobranie instalatora CODESYS Development System,
   instalacja, otwarcie i kompilacja projektu
   ([`codesys_build.py`](scripts/codesys_build.py)). Publikuje
   `reports/junit-build.xml` jako artefakt oraz sam skompilowany projekt
   (razem z `*.precompilecache`) jako artefakt `compiled-project`, który
   przejmuje kolejny job. Błąd kompilacji przerywa pipeline od razu.
2. **deploy-test** — pobiera artefakt `compiled-project`, instaluje
   CODESYS Development System oraz CODESYS Control Win V3 x64 (jako
   usługa Windows), po czym przez CODESYS Scripting
   ([`codesys_deploy.py`](scripts/codesys_deploy.py)) loguje się do
   runtime przez gateway, wgrywa (download) i uruchamia aplikację.
   Następnie ([`codesys_test.py`](scripts/codesys_test.py)) loguje się
   ponownie w trybie tylko-monitorowania i sprawdza, czy PLC jest w stanie
   RUN. Na końcu zawsze zbiera log runtime i zatrzymuje usługę (choć i tak
   cała VM zostanie usunięta po jobie). Publikuje `reports/junit-deploy.xml`
   i `reports/junit-test.xml` jako artefakty oraz `junit-test.xml` jako
   czytelne podsumowanie testów w GitHub Actions.

Deploy i test są rozdzielone na osobne kroki z osobnymi raportami JUnit
(nie osobne joby - bo etap testu potrzebuje tej samej, już uruchomionej
usługi runtime co etap deployu, a każdy job GitHub Actions to inna VM),
więc i tak od razu widać, czy problem jest przy wgrywaniu, czy dopiero przy
weryfikacji działania.

## Wymagania

- Brak self-hosted runnera i Dockera — wystarczy standardowy hostowany
  `windows-latest` (dostępny od razu dla repo/organizacji na GitHub).
- Instalatory CODESYS (Development System + Control Win V3 x64) wystawione
  z prywatnego storage pod adresami w sekretach repo
  `CODESYS_DEVSYS_INSTALLER_URL` i `CODESYS_RTE_INSTALLER_URL` — patrz
  [`installers/README.md`](installers/README.md) po szczegóły i uzasadnienie
  (CODESYS Store wymaga logowania, więc nie da się tego pobrać anonimowo
  bezpośrednio w workflow).
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
