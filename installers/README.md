# Instalatory CODESYS

Ten katalog jest miejscem docelowym dla pobranych instalatorów CODESYS w
trakcie CI (git-ignored - nic poza tym plikiem tu nie trafia do repo).

CODESYS Development System i CODESYS Control Win V3 nie są publicznie
pobieralne - wymagają konta w CODESYS Store i akceptacji licencji, więc
workflow **nie** ściąga ich bezpośrednio ze store.codesys.com. Zamiast
tego trzeba je raz pobrać ręcznie i wystawić z prywatnego, dostępnego dla
runnera miejsca (np. private GitHub Release asset, Azure Blob z SAS token,
S3 z presigned URL) pod adresami przekazanymi jako sekrety repo:

- `CODESYS_DEVSYS_INSTALLER_URL` - **archiwum .zip** z instalatorem
  CODESYS Development System (V3.5 SP22) - tak CODESYS Store pakuje ten
  installer do pobrania.
- `CODESYS_RTE_INSTALLER_URL` - **archiwum .zip** z instalatorem CODESYS
  Control Win V3 x64 (Control Win SL).

Workflow zawsze pobiera/cache'uje `.zip` (`actions/cache`, klucz oparty o
`CODESYS_VERSION`), po czym w osobnym kroku rozpakowuje je
(`scripts/Expand-Installer.ps1`) i sam znajduje właściwy `.exe` w środku
(szuka pliku pasującego do `*Setup*.exe`, jeśli w archiwum jest więcej niż
jeden `.exe`). Ściąganie z prywatnego storage odpala się tylko przy braku
trafienia w cache; samo rozpakowanie i instalacja (silent install) i tak
uruchamiają się w każdym jobie od nowa, bo hostowany runner GitHub
(`windows-latest`) to za każdym razem świeża, jednorazowa maszyna.

## Ważne: URL musi być bezpośrednim linkiem do pliku

`Invoke-WebRequest` w workflow zapisuje 1:1 to, co dostanie pod danym URL.
Jeśli URL to link do **strony podglądu/udostępniania** (np. link Synology
Drive `.../d/s/<id>/<key>` otwierany normalnie w przeglądarce, gdzie plik
ściąga się dopiero po kliknięciu przycisku "Pobierz"), to zamiast realnego
`.zip` zostanie zapisana strona HTML - a próba jej rozpakowania kończy się
czytelnym błędem z `scripts/Assert-ValidZip.ps1` (zamiast dopiero mylącym
błędem `Expand-Archive`/`Start-Process` przy instalacji).

Przed wstawieniem URL do sekretu warto zweryfikować, że to faktycznie
bezpośredni link do pliku:

```powershell
curl.exe -I "<url>"
```

Odpowiedź powinna mieć `Content-Type: application/zip` (albo
`application/octet-stream`) i `Content-Length` zgodny z rozmiarem archiwum
- nie `Content-Type: text/html`. Jeśli link Synology zwraca HTML, sprawdź
w Synology Drive/File Station opcję bezpośredniego linku do pobrania (nie
link "do podglądu") albo rozważ inny hosting (prywatny GitHub Release
asset, Azure Blob z SAS token).
