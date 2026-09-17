# Instalatory CODESYS

Ten katalog jest miejscem docelowym dla pobranych instalatorów CODESYS w
trakcie CI (git-ignored - nic poza tym plikiem tu nie trafia do repo).

CODESYS Development System i CODESYS Control Win V3 nie są publicznie
pobieralne - wymagają konta w CODESYS Store i akceptacji licencji, więc
workflow **nie** ściąga ich bezpośrednio ze store.codesys.com.

## Skąd workflow bierze pliki

Instalatory (jako `.zip`, tak dostarcza je CODESYS Store) są wgrane jako
załączniki (assets) do **prywatnego GitHub Release** w tym repozytorium,
tag **`Installers`**:

- `CODESYS.64.3.5.22.30.zip` - CODESYS Development System.
- `CODESYS.Control.RTE.SL.3.5.22.30.zip` - CODESYS Control Win V3 (Control Win SL).

Workflow ściąga je stamtąd przez `gh release download` z wbudowanym
`GITHUB_TOKEN` - brak zewnętrznych sekretów z URL-ami, brak zależności od
Synology/File Station czy innego hostingu, dostęp działa tak długo jak
osoba/CI ma dostęp do repo. Pobrane pliki są dodatkowo cache'owane
(`actions/cache`, klucz oparty o `CODESYS_VERSION`), więc ściąganie z
Release odpala się tylko przy braku trafienia w cache.

⚠️ **To działa prywatnie tylko jeśli samo repo jest prywatne** - Release i
jego assety dziedziczą widoczność repozytorium. Jeśli repo kiedyś zostanie
upublicznione, instalatory (licencjonowane oprogramowanie) staną się
publicznie pobieralne.

## Aktualizacja wersji / podmiana instalatorów

1. Pobierz nowe `.zip` ze store.codesys.com.
2. Utwórz nowy GitHub Release z nowym tagiem (np. `Installers` można
   nadpisać nowymi assetami albo utworzyć nowy release na nową wersję) i
   wgraj tam pliki `.zip` (przez UI: "Attach binaries" - upewnij się, że
   trafiają w ten box, a nie w pole treści release notes, które ma limit
   25 MB zamiast 2 GB na asset).
3. Zaktualizuj w `.github/workflows/codesys-ci.yml`:
   `CODESYS_VERSION`, `CODESYS_RELEASE_TAG` (jeśli zmieniony) oraz dokładne
   nazwy `CODESYS_DEVSYS_ASSET` / `CODESYS_RTE_ASSET`.

## Rozpakowywanie

`scripts/Expand-Installer.ps1` waliduje pobrany `.zip`
(`scripts/Assert-ValidZip.ps1` - sygnatura `PK`), rozpakowuje go i sam
znajduje właściwy `.exe` w środku (dopasowanie po `*Setup*.exe`, jeśli
jest ich więcej niż jeden) - jego ścieżkę przekazuje dalej do
`Install-CodesysDevSystem.ps1` / `Invoke-CodesysDeploy.ps1`.
