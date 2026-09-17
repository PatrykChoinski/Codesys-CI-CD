# Instalatory CODESYS

Ten katalog jest miejscem docelowym dla pobranych instalatorów CODESYS w
trakcie CI (git-ignored - nic poza tym plikiem tu nie trafia do repo).

CODESYS Development System i CODESYS Control Win V3 nie są publicznie
pobieralne - wymagają konta w CODESYS Store i akceptacji licencji, więc
workflow **nie** ściąga ich bezpośrednio ze store.codesys.com. Zamiast
tego trzeba je raz pobrać ręcznie i wystawić z prywatnego, dostępnego dla
runnera miejsca (np. private GitHub Release asset, Azure Blob z SAS token,
S3 z presigned URL) pod adresami przekazanymi jako sekrety repo:

- `CODESYS_DEVSYS_INSTALLER_URL` - instalator CODESYS Development System
  (V3.5 SP22, np. `CODESYS-3.5.22.0-Setup.exe`).
- `CODESYS_RTE_INSTALLER_URL` - instalator CODESYS Control Win V3 x64
  (np. `CODESYSControlWinV3x64Setup.exe`).

Workflow cache'uje pobrane pliki (`actions/cache`, klucz oparty o
`CODESYS_VERSION`), więc ściąganie ich z prywatnego storage odpala się
tylko przy braku trafienia w cache - kolejne uruchomienia na tym samym
kluczu nie pobierają ich ponownie. Sam proces instalacji (silent install)
uruchamia się jednak w każdym jobie od nowa, bo hostowany runner GitHub
(`windows-latest`) to za każdym razem świeża, jednorazowa maszyna.

## Ważne: URL musi być bezpośrednim linkiem do pliku

`Invoke-WebRequest` w workflow zapisuje 1:1 to, co dostanie pod danym URL.
Jeśli URL to link do **strony podglądu/udostępniania** (np. link Synology
Drive `.../d/s/<id>/<key>` otwierany normalnie w przeglądarce, gdzie plik
ściąga się dopiero po kliknięciu przycisku "Pobierz"), to zamiast realnego
`.exe` zostanie zapisana strona HTML - a próba jej uruchomienia kończy się
błędem `Start-Process: ... file or directory is corrupted and unreadable`.

Przed wstawieniem URL do sekretu warto zweryfikować, że to faktycznie
bezpośredni link do pliku:

```powershell
curl.exe -I "<url>"
```

Odpowiedź powinna mieć `Content-Type: application/octet-stream` (albo
`application/x-msdownload`) i `Content-Length` zgodny z rozmiarem
instalatora - nie `Content-Type: text/html`. Jeśli link Synology zwraca
HTML, sprawdź w Synology Drive/File Station opcję bezpośredniego linku do
pobrania (nie link "do podglądu") albo rozważ inny hosting (prywatny
GitHub Release asset, Azure Blob z SAS token).

Workflow i tak waliduje pobrany plik (`scripts/Assert-ValidExe.ps1` -
sprawdza rozmiar i sygnaturę `MZ`) i przerywa job z czytelnym komunikatem
zamiast dopiero przy próbie instalacji.
