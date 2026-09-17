# Codesys CI/CD

Projekt CODESYS (`CICD.project`, CODESYS Control Win V3 x64, target
V3.5 SP22) wraz z pipeline'em CI, który automatycznie kompiluje projekt,
wgrywa go do runtime uruchomionego w kontenerze Docker i sprawdza, czy
aplikacja faktycznie działa (RUN) — zwracając raport z testów.

## Dlaczego to wygląda tak, a nie inaczej

CODESYS Development System (środowisko inżynierskie, w którym otwiera się
`CICD.project`) **działa tylko na Windows** — nie ma wersji linuksowej ani
kontenerowej samego IDE. Dlatego cały pipeline musi wykonywać się na
**Windows self-hosted runnerze** z zainstalowanym CODESYS, sterowanym
headless przez **CODESYS Scripting** (Python/IronPython uruchamiany przez
`CODESYS.exe --runscript=...`).

Do testowania potrzebny jest jednak działający runtime (PLC), do którego
można się połączyć przez CODESYS Gateway i wgrać skompilowaną aplikację.
Zamiast instalować runtime bezpośrednio na runnerze, uruchamiamy go w
**kontenerze Docker Windows** z zainstalowanym `CODESYS Control Win V3 x64`
— dzięki temu środowisko testowe jest odtwarzalne, izolowane i łatwe do
zresetowania między uruchomieniami CI (`docker rm -f` i od nowa).

```
Windows self-hosted runner
├── CODESYS Development System (kompilacja, CODESYS Scripting)
└── Docker Desktop/Engine w trybie "Windows containers"
    └── kontener: CODESYS Control Win V3 x64 (runtime, gateway :1217)
```

## Struktura repo

```
CICD.project                        - projekt CODESYS
docker/
  Dockerfile                        - obraz Windows z CODESYS Control Win V3 (RTE)
  entrypoint.ps1                    - start usługi CODESYSControlWinV3x64 w kontenerze
  docker-compose.yml                - pomocniczy plik do budowy/testów lokalnych
  installers/                       - tu wrzucasz pobrany instalator (git-ignored)
  README.md                         - jak pobrać instalator, wymagania hosta, licencja
scripts/
  codesys_build.py                  - CODESYS Scripting: kompilacja projektu
  codesys_deploy.py                 - CODESYS Scripting: login + download + start na runtime
  codesys_test.py                   - CODESYS Scripting: weryfikacja stanu RUN (smoke test)
  Invoke-CodesysBuild.ps1            - wrapper PowerShell dla etapu build
  Invoke-CodesysDeploy.ps1           - wrapper PowerShell dla etapu deploy (build+start kontenera)
  Invoke-CodesysTest.ps1             - wrapper PowerShell dla etapu test (+ teardown kontenera)
.github/workflows/codesys-ci.yml    - workflow GitHub Actions (3 joby: build, deploy, test)
reports/                            - wygenerowane raporty JUnit XML + logi runtime (git-ignored)
```

## Etapy pipeline'u (joby CI)

Workflow [`codesys-ci.yml`](.github/workflows/codesys-ci.yml) uruchamia
się na push/PR do `master` oraz ręcznie (`workflow_dispatch`), jako trzy
kolejne joby na tym samym self-hosted Windows runnerze (label
`codesys-windows`):

1. **build** — otwiera projekt w CODESYS i go kompiluje
   ([`codesys_build.py`](scripts/codesys_build.py)). Nie dotyka Dockera ani
   żadnego runtime — ma tylko potwierdzić, że kod się kompiluje. Publikuje
   `reports/junit-build.xml` jako artefakt. Błąd kompilacji przerywa
   pipeline od razu.
2. **deploy** — buduje obraz Docker (`docker build`), startuje kontener z
   runtime CODESYS Control Win V3, czeka aż przejdzie healthcheck, po czym
   przez CODESYS Scripting ([`codesys_deploy.py`](scripts/codesys_deploy.py))
   loguje się do runtime przez gateway, wgrywa (download) i uruchamia
   aplikację. Kontener **zostaje uruchomiony** dla joba `test` (w razie
   błędu deployu sam się sprząta). Publikuje `reports/junit-deploy.xml`.
3. **test** — smoke test: loguje się do już działającej aplikacji (bez
   ponownego wgrywania) i sprawdza, czy PLC jest w stanie RUN
   ([`codesys_test.py`](scripts/codesys_test.py)). Niezależnie od wyniku
   zawsze zbiera logi kontenera i go usuwa (`docker rm -f`). Publikuje
   `reports/junit-test.xml` jako artefakt oraz jako czytelne podsumowanie
   testów w GitHub Actions (test summary).

Każdy etap ma osobny raport JUnit XML, więc w GitHub Actions od razu widać,
na którym etapie (kompilacja / wgranie / działanie) coś się wysypało.

**Ograniczenie:** joby `deploy` i `test` dzielą między sobą stan
(uruchomiony kontener) tylko dlatego, że wykonują się na tym samym runnerze.
To działa poprawnie tylko wtedy, gdy za labelką `codesys-windows` stoi
dokładnie jeden runner. Skalowanie na wiele równoległych runnerów wymaga
przekazywania rzeczywistego adresu kontenera między jobami (np. przez
artefakt) zamiast zakładania `127.0.0.1`.

## Wymagania środowiska (self-hosted runner)

- Windows (10/11 Pro/Enterprise lub Windows Server) z zarejestrowanym
  self-hosted runnerem GitHub Actions, labelka `codesys-windows`.
- CODESYS Development System V3.5 SP22 zainstalowany lokalnie na runnerze.
- Docker Desktop/Engine przełączony w tryb **Windows containers** (patrz
  [`docker/README.md`](docker/README.md)).
- Zainstalowany instalator `CODESYS Control Win V3 x64` (pobrany ręcznie
  z CODESYS Store — patrz niżej) dostępny na runnerze pod
  `docker/installers/<plik>`, a jego nazwa ustawiona jako sekret repo
  `CODESYS_RTE_INSTALLER_FILENAME`.

## Licencja / instalator runtime

`CODESYS Control Win V3` nie jest publicznie pobieralny — wymaga konta w
CODESYS Store i akceptacji licencji, więc nie da się go automatycznie
ściągnąć w Dockerfile. Szczegóły pobrania, wymagań hosta (dopasowanie tagu
obrazu bazowego do wersji Windows) oraz działania w trybie demo (bez
licencji runtime, ograniczony czas ciągłej pracy — wystarczający na krótki
smoke test w CI) opisane są w [`docker/README.md`](docker/README.md).

## Praca z repo

Zasady współpracy z Claude nad tym repo (commity lokalne, changelog, brak
automatycznego push) są opisane w [`CLAUDE.md`](CLAUDE.md). Historia zmian
prowadzona jest w [`CHANGELOG.md`](CHANGELOG.md).
